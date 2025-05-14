import requests
from pymongo import MongoClient
from langchain_openai import ChatOpenAI
from langchain.agents import Tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
import re
import ast
from langchain.schema import AIMessage
import datetime
import sys
import time
import difflib
import yaml
import json
from ...llm import llm
import os

CURRENT_DIR = os.path.dirname(__file__)
PROMPT_PATH = os.path.join(CURRENT_DIR, "prompts.yaml")



#----------global variable----------#
PROXY_SERVER = "http://10.1.8.5:5000/favicon.ico"
MONGO_URI = "mongodb://admin:password@192.168.1.166:27017/admin"
DB_NAME = "product_specification"
BAREBONE_COLLECTION_NAME = "server_spec_barebone"
QVL_COLLECTION_NAME = "server_qvl_R283_Z90_AAV3_000"
 
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
pattern = r'[A-Za-z0-9]+-[A-Za-z0-9]'
collection_fields_cache = {}
#----------global variable----------#
#----------get field prompt----------#
with open(PROMPT_PATH, "r") as file:
    prompts = yaml.safe_load(file)
 
field_lookup = {}
 
for entry in prompts["fields"]:
    fields = entry["mapping"]
    if isinstance(fields, str):
        fields = [fields]
    for alias in fields:
        field_lookup[alias] = {
            "description": entry["description"],
        }
#----------get field prompt----------#
 
def extract_field_names(raw_keys):
    # remove \n
    field_names = set()
    for item in raw_keys:
        lines = item.strip().split('\n')
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                field = parts[1].strip()
                field_names.add(field)
    return list(field_names)
 
def search_database(query: str) -> str:
    """
    Generates and executes MongoDB queries based on user input.
    Attempts to extract project model and query related QVL data.
    """
    global response_time
    global search_time
 
    # Try to extract the project model pattern from user query
    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        try:
            #find projectmodel and gbtsn and save to db
            start = time.time()
            models = re.findall(r"\b[A-Z0-9]+-[A-Z0-9]+(?:-[A-Z0-9]+)?\b", query)
            print(f"find {models} in query")
            for name in models:
                start = time.time()
                index = re.escape(name)
                regex = "^" + index
                cursor = db[BAREBONE_COLLECTION_NAME].find(
                    {"ProjectModel": {"$regex": regex, "$options": "i"}},
                    {"ProjectModel": 1, "barebone_gbtsn": 1}
                )
                results = []
                for doc in cursor:
                    results.append({
                        "projectmodel": doc.get("ProjectModel"),
                        "barebone_gbtsn": doc.get("barebone_gbtsn")
                    })
                if not results:
                    result = "barebone not found."
                elif len(results) == 1:
                    result = results[0]
                else:
                    result = results
               
                end = time.time()
            print(f"find projectmodel and gbtsn is : {result} and spend {end-start:4f}s")
           
            start = time.time()
            result_key = []
            question = eval(analyze_query(query))
            for q in question:
                response = analyze_key(q)
                result_key.append(response)
               
            fields = extract_field_names(result_key)
            end = time.time()
            print(f"analyze key is : {fields} and spend time : {end-start:4f}")
           
            start = time.time()
            projection = {"_id": 0}
            for f in fields:
                projection[f] = 1
               
            results = db[BAREBONE_COLLECTION_NAME].find({"ProjectModel": result.get('projectmodel')},projection)
           
            response = []
            for raw in results:
                response.append(raw)
               
            end = time.time()
            print(f"search database result is : {response} and spend time : {end-start:4f}")
           
            show = summary_result(query,response)  
            return show
        except Exception as e:
            print(f"An error occurred: {e}")
 
def analyze_key(question):
    prompt = f"""
        You are an assistant that helps map natural language queries to the correct field names in a dataset.
        I will provide a field_lookup dictionary that contains mappings from human-friendly terms to actual field names in the data.
        Given a user query, identify which fields in field_lookup are relevant, and output the mapping in the format:
        <natural language keyword> : <field name>.
        If no relevant field is found, explicitly state: "No matching field found."
        Question : {question}
        field_lookup : {field_lookup}
    """
    response = llm.invoke(prompt)
    return response.content
 
def analyze_query(query):
    prompt = f"""
        Please analyze the sentence below and list the number of questions it contains along with their content:
 
        User query: {query}
 
        Please respond with only the list of questions in array format.
        like: [Question1,Question2,Question3]
        """
    response = llm.invoke(prompt)
    return response.content
 
def summary_result(query,answer):
    summary_prompt = f"""You are given a user query and the system's response.
        Please list the all result in a concise and organized format.
 
        User Query:
        {query}
 
        System Response:
        {answer}
 
        Final Answer:
        """

    print("================Summary================")
    response = llm.invoke(summary_prompt)
    return response.content


    



#'find all support DDR of projectmodel R283-Z90-AAD1-000'
#'find R283-Z90-AAD2-000 storage connector'
#'find R283-Z90-AAD2-000 storage connector count'
#'choose the best server in the database'                        #This query cannot be fulfilled. The request "choose the best server" is too vague.
#'find the projectmodel which support intel cpu'
#'find the storage connector of projectmodel H223-V10-AAW1-000'  #沒有qvl的資料(one data not support)
#'find projectmodel which connector support U.2 and SATA'


#memory 對話紀錄-分析出基本資料儲存/field/客戶資料/bdm資料/
#mgmt是用memory的資料存(不用手動存)，Weekly Update用array存，Status/Country/BDM 需要固定名稱(以免打錯)/欄位型態/