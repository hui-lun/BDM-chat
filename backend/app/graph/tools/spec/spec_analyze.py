#這版是可以模糊搜尋projectmodel並尋找barebone_gbtsn，summary用的是llm
import re
import time
import yaml
from tabulate import tabulate
from collections import defaultdict
from ...llm import llm
import os
import datetime
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

def connect_mongo():
    load_dotenv()
    MONGODB_IP = os.getenv('MONGODB_IP')
    MONGODB_USER = os.getenv('MONGODB_USER')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
    uri = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_IP}:27017/admin"
    client = MongoClient(uri)
    return client

#----------global variable----------#
PROXY_SERVER = os.getenv('PROXY_SERVER')
DB_NAME = "product_specification"
BAREBONE_COLLECTION_NAME = "server_spec_barebone"

CURRENT_DIR = os.path.dirname(__file__)
PROMPT_PATH = os.path.join(CURRENT_DIR, "prompts.yaml")

client = connect_mongo()
db = client[DB_NAME]
pattern = r'[A-Za-z0-9]+-[A-Za-z0-9]'
collection_fields_cache = {}
status = ""
#----------global variable----------#

#----------get spec prompt----------#
with open(PROMPT_PATH, "r") as file:
    prompts = yaml.safe_load(file)

spec_field_lookup = {}

for entry in prompts["SPEC"]:
    fields = entry["mapping"]
    if isinstance(fields, str):
        fields = [fields]
    for alias in fields:
        spec_field_lookup[alias] = {
            "description": entry["description"],
        }
#----------get spec prompt----------#

#----------get qvl field prompt-----------#
all_qvl_key = set()
qvl_field_lookup = {}
    
for entry in prompts["QVL"]:
    fields = entry["mapping"]
    if isinstance(fields, str):
        fields = [fields]
    for alias in fields:
        qvl_field_lookup[alias] = {
            "description": entry["description"],
        }
#----------get qvl field prompt-----------#

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

def fetch_qvl(model, sku, gbt_pn):
    try:
        response = requests.get(PROXY_SERVER, params={"Model": model, "SKU": sku, "gbt_pn": gbt_pn}, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            return "no_one_data"
        return data
    except Exception as e:
        return "no_one_data"
    
def insert_qvl(data):
    collection = db[QVL_COLLECTION_NAME]
    collection.delete_many({})
    if isinstance(data, list):
        data['time'] = datetime.datetime.now()
        collection.insert_many(data)
    else:
        data['time'] = datetime.datetime.now()
        collection.insert_one(data)
    print("QVL data inserted into MongoDB successfully.")

def get_qvl_data(projectmodel,barebone_gbtsn):
    global QVL_COLLECTION_NAME
    QVL_COLLECTION_NAME = f"server_qvl_{projectmodel.replace('-', '_')}" if projectmodel else None          #replace - to _
    collections = db.list_collection_names()
    if QVL_COLLECTION_NAME not in collections:
        if re.match(pattern, projectmodel):
            modelname = projectmodel.split('-')
            model = f"{modelname[0]}-{modelname[1]}"
            sku = f"{modelname[2]}"
            gbt_pn = f"{barebone_gbtsn}"
            result = fetch_qvl(model, sku, gbt_pn)
            if result == "no_one_data":
                return "no_one_data"
            else:
                insert_qvl(result)
                get_qvl_field()
                return "one_data"
    else:
        get_qvl_field()
        return "one_data"

def get_qvl_field():
    qvl_db = db[QVL_COLLECTION_NAME]
    for document in qvl_db.find():
        for field in document.keys():
            if field != '_id':
                all_qvl_key.add(field)
                if ">>>" in field:
                    base_key = field.split('>>>')[0]
                else:
                    base_key = field.split('_')[0]
                
                if base_key not in qvl_field_lookup:
                    description = f"This field represents {base_key} related data."
                    qvl_field_lookup[base_key] = {
                        "description": description,
                    }

def get_projection_result(collection, query, fields):
    """Helper to query specific fields from a collection."""
    if not fields:
        return []
    projection = {f: 1 for f in fields}
    projection["_id"] = 0
    return list(db[collection].find(query, projection))

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
            return_result = []
            models = re.findall(r"[A-Z0-9]+-[A-Z0-9]+(?:-[A-Z0-9_]+)?", query)
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
                    result = [results[0]]
                else:
                    result = results
                
                end = time.time()
            print(f"step2: find projectmodel and gbtsn is : {result} and spend {end-first_start:4f}s")
            
            try:
                #----------analyze_key to database----------#
                start = time.time()
                result_key = []
                response = analyze_key(query)
                result_key.append(response)
                fields = extract_field_names(result_key)
                end = time.time()
                print(f"step3: analyze key is : {fields} and spend time : {end-start:4f}")
                #----------analyze_key to database----------#
                for name in result:
                    #----------save to database----------#
                    start = time.time()
                    projectmodel = name.get('projectmodel')
                    barebone_gbtsn = name.get('barebone_gbtsn')
                    qvl_return = get_qvl_data(projectmodel, barebone_gbtsn)
                    end = time.time()
                    if qvl_return == "one_data":
                        print(f"step4: {QVL_COLLECTION_NAME} save to database and spend {end-start:4f}s")
                    else:
                        print(f"step4: {QVL_COLLECTION_NAME} one data not support and spend {end-start:4f}s")
                    #----------save to database----------#
                    #----------search database----------#
                    start = time.time()
                    invalid_fields = []
                    nested_fields = []
                    non_nested_fields = []
                    qvl_field = []
                    matched_fields = []

                    for f in fields:
                        if f in spec_field_lookup:
                            (nested_fields if "." in f else non_nested_fields).append(f)
                        elif f in qvl_field_lookup:
                            qvl_field.append(f)
                        else:
                            invalid_fields.append(f)
                    if invalid_fields:
                        print(f"[WARN] No matching fields: {invalid_fields}")

                    response1 = get_projection_result(BAREBONE_COLLECTION_NAME, {"ProjectModel": projectmodel}, nested_fields)
                    response2 = get_projection_result(BAREBONE_COLLECTION_NAME, {"ProjectModel": projectmodel}, non_nested_fields)

                    spec_response = [
                        {**r1, **r2}
                        for r1, r2 in zip(response1 or [{}], response2 or [{}])
                    ]

                    if qvl_field and qvl_return == "one_data":
                        for keyword in qvl_field:
                            matched_fields.extend([k for k in all_qvl_key if keyword in k])
                        matched_fields = list(set(matched_fields))
                        qvl_response = get_projection_result(QVL_COLLECTION_NAME, {}, matched_fields)
                    else:
                        qvl_response = [{}]
                        
                    end = time.time()
                    print(f"step5: finish search database result and spend time : {end-start:4f}")
                    #----------search database----------#
                    
                    #----------summarize----------#
                    start = time.time()
                    show = summarize_result(projectmodel,spec_response+qvl_response)   
                    return_result.append(show)
            except Exception as e:
                print(f"An error occurred: {e}")
                return "database not found this server"
            
            last_end = time.time()
            print(f"step6: summarize spend time : {last_end-start:4f}")
            #----------summarize----------#
            print(f"Program execution time : {last_end-first_start:4f}")   
            return return_result
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return "database not found this server"
    else:
        #要再補一個spec search projectmodel
        return "database not found this server"

def analyze_key(question):
    if "qvl" not in question.lower():
        field_lookup = spec_field_lookup
    else:
        field_lookup = qvl_field_lookup
        
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

def summarize_result(model,data_list):
    result = clean_spec(model,data_list)
    return result

def clean_spec(model,data_list):
    if not data_list:
        return "No data."

    data = data_list[0]
    result = f"{model} summarize:\n"

    keys_to_itemize = [k for k, v in data.items() if isinstance(v, list) and v and isinstance(v[0], dict)]

    for k, v in data.items():
        if k in keys_to_itemize:
            continue
        if v is None:
            continue
        if isinstance(v, list):
            def flatten_list(x):
                if isinstance(x, list):
                    return ", ".join(flatten_list(i) for i in x)
                else:
                    return str(x)
            joined = flatten_list(v)
            if joined:
                result += f"- {k} : {joined}\n"
        else:
            result += f"- {k} : {v}\n"

    for key in keys_to_itemize:
        for idx, item in enumerate(data[key]):
            result += f"- {key} #{idx+1}\n"
            for k, v in item.items():
                if v is None:
                    continue
                if isinstance(v, list):
                    def flatten_list(x):
                        if isinstance(x, list):
                            return ", ".join(flatten_list(i) for i in x)
                        else:
                            return str(x)
                    joined = flatten_list(v)
                    if joined:
                        result += f"  - {k} : {joined}\n"
                else:
                    result += f"  - {k} : {v}\n"
    num = 1
    for key, details in data_list[1].items():  
        if '>>>' in key and '_' in key:
            base_key = key.split('_')[0] 
            number = key.split('_')[1]   
        elif '_' in key:
            base_key = key.split('_')[0] 
            number = key.split('_')[1]   
        else:
            base_key = key
            number = ""

        header = f"{base_key} #{num}" if number else base_key
        num += 1
        result += f"- {header}\n"
        for k, v in details.items():
            if v is None or v == '':
                continue
            if isinstance(v, list):
                joined = ", ".join(str(i) for i in v)
                result += f"    - {k}: {joined}\n"
            else:
                result += f"    - {k}: {v}\n"
        result += "\n"
    return result