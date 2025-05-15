#這版是可以模糊搜尋projectmodel並尋找barebone_gbtsn，summary用的是list
from pymongo import MongoClient
from langchain_openai import ChatOpenAI
import re
import time
import yaml
import json
from tabulate import tabulate
from collections import defaultdict
from ...mongodb import client
from ...llm import llm
import os
 
#----------global variable----------#
PROXY_SERVER = "http://10.1.8.5:5000/favicon.ico"
DB_NAME = "product_specification"
BAREBONE_COLLECTION_NAME = "server_spec_barebone"
QVL_COLLECTION_NAME = "server_qvl_R283_Z90_AAV3_000"
 
CURRENT_DIR = os.path.dirname(__file__)
PROMPT_PATH = os.path.join(CURRENT_DIR, "prompts.yaml")
 
 
db = client[DB_NAME]
pattern = r'[A-Za-z0-9]+-[A-Za-z0-9]'
collection_fields_cache = {}
status = ""
#----------global variable----------#
 
#----------get field prompt----------#
with open(PROMPT_PATH, "r") as file:
    prompts = yaml.safe_load(file)
 
field_lookup = {}
 
for entry in prompts["SPEC"]:
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
            else:
                field_names.add(line)
    return list(field_names)
 
def search_database(query: str) -> str:
    """
    Generates and executes MongoDB queries based on user input.
    Attempts to extract project model and query related QVL data.
    """
    # Try to extract the project model pattern from user query
    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        try:
            #find projectmodel and gbtsn and save to db
            first_start = time.time()
            models = re.findall(r"\b[A-Z0-9]+-[A-Z0-9]+(?:-[A-Z0-9]+)?\b", query)
            print(f"step1: find {models} in query")
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
            print(f"step2: find projectmodel and gbtsn is : {result} and spend {end-first_start:4f}s")
           
            try:
                start = time.time()
                result_key = []
                response = analyze_key(query)
                result_key.append(response)
                fields = extract_field_names(result_key)
                end = time.time()
                print(f"step3: analyze key is : {fields} and spend time : {end-start:4f}")
               
                start = time.time()
                projection = {"_id": 0}
                for f in fields:
                    projection[f] = 1
                   
                results = db[BAREBONE_COLLECTION_NAME].find({"ProjectModel": result.get('projectmodel')},projection)
               
                response = []
                for raw in results:
                    response.append(raw)
                   
                end = time.time()
                print(f"step4: finish search database result and spend time : {end-start:4f}")
               
                #----------summary----------#
                start = time.time()
                show = summary_result(name,response)  
                print("=================SUMMARY=================")
                print(show)
                last_end = time.time()
                print(f"step5: summary spend time : {last_end-start:4f}")
                #----------summary----------#
               
                print(f"Program execution time : {last_end-first_start:4f}")  
                return show
            except:
                print("database not found this server")
                return "database not found this server"
        except Exception as e:
            print(f"An error occurred: {e}")
 
def analyze_key(question):
    prompt = f"""
        You are a helpful assistant. Map the user query to the correct field name(s) from the provided dictionary.
 
        If any part of the query matches a concept in field_lookup, return the match in the format:
        <field name>
 
        If there is no match, respond with: "No matching field found."
 
        Query: {question}
        field_lookup: {field_lookup}
        """
    response = llm.invoke(prompt)
    return response.content
 
def flatten_and_merge(data, parent_key=''):
    merged = defaultdict(list)
 
    def _flatten(obj, current_key=''):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_key = f"{current_key}.{k}" if current_key else k
                _flatten(v, new_key)
        elif isinstance(obj, list):
            for item in obj:
                _flatten(item, current_key)
        else:
            if obj is not None:
                merged[current_key].append(obj)
 
    _flatten(data, parent_key)
    return merged
 
def summary_result(model,answer):
    flat = flatten_and_merge(answer)
    result = f"{model} Summary:\n"
    for key, values in flat.items():
        if len(values) == 1:
            result += f"- {key} : {values[0]} \n"
        else:
            joined = ", ".join(values)
            result += f"- {key} : {joined} \n"
    return result
 