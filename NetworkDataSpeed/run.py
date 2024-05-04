#importing important utilities and libraries
import os
import json
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
import urllib.request
import tiktoken
import math
from PyPDF2 import PdfReader
import langchain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.text_splitter import CharacterTextSplitter

#function to count number of tokens using tiktoken function
def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

#loading the environment variables
load_dotenv()
service_endpoint = os.getenv('service_endpoint')
index_name = os.getenv('index_name')
key = os.getenv('key')
storage_account_name= os.getenv('storage')
container_name=os.getenv('container')
oai_deployment = os.getenv('oai_deployment')
oai_base=os.getenv('oai_base')
oai_key=os.getenv('oai_key')

#setting important configurations
#os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2024-02-15-preview"
os.environ["AZURE_OPENAI_ENDPOINT"] = oai_base
os.environ["OPENAI_API_KEY"] = oai_key



#creating an Azure AI Search Client
search_client = SearchClient(service_endpoint, index_name, AzureKeyCredential(key))

#taking the user query as input
user_query=input('enter your query')
results = search_client.search(search_text=user_query)

title=""
count=0

for result in results:
    while(count==0):
        title=result['title']
        count=count+1
#print (title)       

#storing the content of the supplement pdf file in a seperate file
url = "https://" + str(storage_account_name) + ".blob.core.windows.net/" + str(container_name) + "/" + str(title)
filename = 'text_file.txt'
urllib.request.urlretrieve(url, filename)
#reader = PdfReader('file.pdf')
reader = open(file=r"text_file.txt", encoding="utf8").read()

'''# Split the text into chunks of 1000 characters with 200 characters overlap.
text_splitter = CharacterTextSplitter(        
    separator = "\n",
    chunk_size = 50,
    chunk_overlap  = 10,
    length_function = len,
)
textTexts = text_splitter.split_text(reader)
# Show how many chunks of text are generated.
print(len(textTexts))

#print(textTexts)'''

#get number of tokens from the PDF text
no_of_tokens = num_tokens_from_string(reader,"cl100k_base")

#variable initialization
summary=""
word_sum=""

n=math.ceil(no_of_tokens/4096)
print("n:" + str(n))
content_length = len(reader)
lcount=0
print("content_length" + str(content_length))
rcount=int(content_length/n)
print("rcount" + str(rcount))
'''pages=len(reader.pages)
text=" "
count=0
while(count!=pages):
    page=reader.pages[count]
    text=text+page.extract_text()
    count=count+1'''
#using the "chain of summarisation" alogorithm
while(rcount<content_length):
    word_sum = reader[lcount:rcount]
    #creating a azure openai language model to answer the user query   
    llm = AzureChatOpenAI(
        openai_api_key=oai_key,
        openai_api_version="2023-05-15",
        azure_deployment=oai_deployment,
    )


    #user_prompt = str(user_query) + "the supplement content provided to you is: \n" + str(text)
    user_prompt = str(user_query) + "the supplement content provided to you is: \n" + str(word_sum)
    system_prompt = "you are an AI assistant designated to help people answer their queries based on the supplement content provided to you"

    prompt = ChatPromptTemplate.from_messages([
    ("system",system_prompt),
    ("user","{input}")
    ])

    chain=prompt | llm | StrOutputParser()

    #print(chain.invoke({"input":user_prompt}))
    chain.invoke({"input":user_prompt})

    summary = summary + chain.invoke({"input":user_prompt})
    lcount=int(lcount + content_length/n)
    rcount=int(rcount+content_length/n)
    
#print("summary" + str(summary))

summaryllm = AzureChatOpenAI(
    openai_api_key=oai_key,
    openai_api_version="2023-05-15",
    azure_deployment=oai_deployment,
)


#user_prompt = str(user_query) + "the supplement content provided to you is: \n" + str(text)
user_prompt = str(user_query) + "the supplement content provided to you is: \n" + str(summary)
system_prompt = "you are an AI assistant designated to help people answer their queries based on the supplement content provided to you"

prompt = ChatPromptTemplate.from_messages([
("system",system_prompt),
("user","{input}")
])

chain1=prompt | llm | StrOutputParser()

print(chain1.invoke({"input":user_prompt}))

    

