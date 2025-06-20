#QVL ok array projectmodel ok use list summarize
from langchain_openai import ChatOpenAI
import re
import time
import yaml
from tabulate import tabulate
import os
import requests
import json
from ....graph import api_code
import logging
from collections import defaultdict
from langgraph.prebuilt import create_react_agent
from langchain.agents import Tool
from langchain.tools import tool
from ...mongodb import client

# setting logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

#-------------load vllm-------------#
inference_server_url = "http://192.168.1.120:8090/v1"
llm = ChatOpenAI(
    model="gemma-3-27b-it",
    openai_api_key="EMPTY",
    openai_api_base=inference_server_url
)
#-------------load vllm-------------#

#----------global variable----------#
BAREBONE_COLLECTION_NAME = "server_spec_barebone"

CURRENT_DIR = os.path.dirname(__file__)
PROMPT_PATH = os.path.join(CURRENT_DIR, "prompts.yaml")


 
pattern = r'[A-Za-z0-9]+-[A-Za-z0-9]'
collection_fields_cache = {}
status = ""
#----------global variable----------#

#----------mapping table -----------#
op_mapping = {
    '$regex': 'contains',
    '$gte': 'greater than or equal to',
    '$gt': 'greater than',
    '$lte': 'less than or equal to',
    '$lt': 'less than',
    '$ne': 'not equal to',
    '$eq': 'equal to',                
    '$in': 'in list',                
    '$nin': 'not in list',          
    '$exists': 'exists',          
    '$not': 'does not match condition',
}
#----------mapping table -----------#
 
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
all_qvl_key = []
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
 
@tool
def match_projectmodel(query:str) -> str:
    """"
        Use this tool when the query contains a project model (e.g., 'R163-Z35')
    """
    global all_qvl_key
    global qvl_field_lookup
    return_result = []
    try:
        #find projectmodel and gbtsn and save to db
        logger.info(repr(query))
        first_start = time.time()
        models = re.findall(r"[A-Z0-9]+-[A-Z0-9]+(?:-[A-Z0-9_]+)?", query)
        logger.info(f"Found models in query: {models}")
       
        for name in models:
            start = time.time()
            index = re.escape(name)
            regex = "^" + index
            filter_dict = {"ProjectModel": {"$regex": regex, "$options": "i"}}
            projection_dict = {"ProjectModel": 1, "barebone_gbtsn": 1}
            cursor = api_code.call_find_documents(BAREBONE_COLLECTION_NAME, filter_dict, projection_dict)
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
            logger.debug(f"step2: find projectmodel and gbtsn is : {result} and spend {end-first_start:4f}s")
           
        try:
            #----------analyze_key to database----------#
            start = time.time()
            result_key = []
            response = analyze_key(query)
            result_key.append(response)
            fields = extract_field_names(result_key)
            end = time.time()
            logger.info(f"step3: analyze key is : {fields} and spend time : {end-start:4f}")
           
            for name in result:
                #----------save to database----------#
                start = time.time()
                projectmodel = name.get('projectmodel')
                barebone_gbtsn = name.get('barebone_gbtsn')
                qvl_insert_response = api_code.call_get_qvl_data(projectmodel, barebone_gbtsn,all_qvl_key,qvl_field_lookup)
                qvl_return = qvl_insert_response['qvl_return']          # one_data / no_one_data
                qvl_name = qvl_insert_response['qvl_name']              # save qvl collection name
                all_qvl_key = qvl_insert_response['all_qvl_key']        # qvl field
                qvl_field_lookup = qvl_insert_response['qvl_field_lookup']
               
                end = time.time()
                if qvl_return == "one_data":
                    logger.info(f"step4: {qvl_name} save to database and spend {end-start:4f}s")
                else:
                    logger.warning(f"step4: {qvl_name} one data not support and spend {end-start:4f}s")
               
                #----------search database----------#
                start = time.time()
                invalid_fields = []
                nested_fields = []
                non_nested_fields = []
                qvl_field = []
                matched_fields = []
                qvl_response = [{}]
                spec_response = [{}]
                for f in fields:
                    if f in spec_field_lookup:
                        (nested_fields if "." in f else non_nested_fields).append(f)
                    elif f in qvl_field_lookup:
                        qvl_field.append(f)
                    else:
                        invalid_fields.append(f)
                if invalid_fields:
                    logger.warning(f"No matching fields: {invalid_fields}")
 
                response1 = api_code.call_get_projection(BAREBONE_COLLECTION_NAME, {"ProjectModel": projectmodel}, nested_fields)
                response2 = api_code.call_get_projection(BAREBONE_COLLECTION_NAME, {"ProjectModel": projectmodel}, non_nested_fields)
 
                spec_response = [
                    {**r1, **r2}
                    for r1, r2 in zip(response1 or [{}], response2 or [{}])
                ]
               
 
                if qvl_field and qvl_return == "one_data":
                    for keyword in qvl_field:
                        matched_fields.extend([k for k in all_qvl_key if keyword in k])
                    matched_fields = list(set(matched_fields))
                    qvl_response = api_code.call_get_projection(qvl_name, {}, matched_fields)
                elif qvl_return != "one_data" and ("qvl" in query.lower()):
                    logger.warning("QVL not supported in database")
                    return "QVL not support in database",0
                else:
                    qvl_response = [{}]
                   
                end = time.time()
                logger.info(f"step5: finish search database result and spend time : {end-start:4f}s")
               
                #----------summarize----------#
                start = time.time()
                status = 'match'
                show = summarize_result(projectmodel, spec_response+qvl_response, status)  
                return_result.append(show)
               
        except Exception as e:
            logger.error(f"Error in database operations: {str(e)}")
            return "database not found this server",0
       
        last_end = time.time()
        logger.info(f"step6: summarize spend time : {last_end-start:4f}s")
        logger.info(f"Total execution time: {last_end-first_start:.4f}s")
        if len(spec_response[0]) != 0:
            return return_result,len(spec_response[0])
        else:
            return return_result,len(qvl_response[0])
       
    except Exception as e:
        logger.error(f"Error in match_projectmodel: {str(e)}")
        return "database not found this server",0
 
@tool
def unmatch_projectmodel(query:str)->str:
    """"
        Use this tool when the query contains a project model(e.g., 'R163-Z35').
    """
    try:
        status = "no_match"
        start = time.time()
        match_groups = defaultdict(list)
        response = analyze_server(query)
        if "```json" in response:
            response = remove_code_fences(response)
 
        data_dict = json.loads(response)
        result = build_mongo_filter(data_dict)
       
        or_conditions = []
        for key, cond in result.items():
            if isinstance(cond, dict):
                or_conditions.append({key: cond})
            else:
                #only one value
                or_conditions.append({key: {"$eq": cond}})
        final_query = {"$or": or_conditions}
       
        results = api_code.call_find_documents(BAREBONE_COLLECTION_NAME, final_query)
       
        for doc in results:
            matched_conditions = []
            for i, cond in enumerate(or_conditions):
                if match_condition(doc, cond):
                    matched_conditions.append(f"Condition #{i + 1}")
            projectmodel = doc.get("ProjectModel", "Unknown")
            key = tuple(sorted(matched_conditions))
            match_groups[key].append(projectmodel)
           
        show = summarize_result(or_conditions, match_groups, status)
        end = time.time()
        logger.info(f"Unmatch projectmodel search completed in {end-start:.4f}s")
        total = sum(len(v) for v in match_groups.values())
        return show,total
   
       
    except Exception as e:
        logger.error(f"Error in unmatch_projectmodel: {str(e)}")
        return "database not found this server"
 
def search_database(query: str) -> str:
    tools = [
        Tool(
            name="match_projectmodel",
            func=match_projectmodel,
            description="Use this tool when the query contains a project model (e.g., R283-Z90-AAD1-000)"
        ),
        Tool(
            name="unmatch_projectmodel",
            func=unmatch_projectmodel,
            description="Use this tool when the query does not contain a project model but contains other specifications"
        )
    ]
 
    agent = create_react_agent(llm, tools)
    result = agent.invoke({"messages":[("user", query)]})
    final_response = result.get("messages")[-1].content
   
    match = re.search(r"\[([a-zA-Z_]+)\(.*\)\]", final_response)
 
    if match:
        tool_name = match.group(1)
        tool_obj = next((t for t in tools if t.name == tool_name), None)
        result,num = tool_obj.invoke(input=query)
    else:
        logger.info("error")
   
    if isinstance(result,list):
        result = "\n".join(result)
    else:
        result = result
               
    if tool_obj.name == "match_projectmodel":
        if "qvl" in query.lower():
            temp = "qvl"
            if num>5:
                path = api_code.save_output_file(result)
                base_url = "http://192.168.1.166:5501/qvl_web.html"
                final_url = f"{base_url}?txt=/file/{path}"
                return final_url, temp, num
            else:
                return result, temp, num
        else:
            temp = "spec"
            return result, temp,num
    else:
        temp = "unmatch"
        if num>5:
            path = api_code.save_output_file(result)
            base_url = "http://192.168.1.166:5501/model_web.html"
            final_url = f"{base_url}?txt=/file/{path}"
            return final_url, temp, num
        else:
            return result, temp, num
       
 
       
def get_nested_value(doc, field):
    keys = field.split('.')
    for key in keys:
        if isinstance(doc, list):
            doc = doc[0] if doc else None
        if isinstance(doc, dict):
            doc = doc.get(key)
        else:
            return None
    return doc
 
def match_condition(doc, cond):
    for field, criteria in cond.items():            #key condition like (CPUBrand,{'$regex': 'Intel'})
        field_value = get_nested_value(doc, field)  #key correspondence value like CPUBrand to Intel
        op, target = next(iter(criteria.items()))   #op=regex or ne or gte ; target=value ; just get first condition
       
        if field_value is None or str(field_value) == "None":
            return False
           
        if isinstance(criteria, dict):
            op, target = next(iter(criteria.items()))
        else:
            op = "$eq"
            target = criteria
           
        if op == "$regex":
            if not isinstance(field_value, str):
                field_value = str(field_value)
            if not re.search(target, field_value):
                return False
        elif op == "$eq":
            if str(field_value) != str(target):
                return False
        elif op == "$ne":
            if str(field_value) == str(target):
                return False
        elif op in ["$gte", "$gt", "$lt", "$lte"]:
            try:
                field_value = float(field_value)
                target = float(target)
                if op == "$gte" and field_value < target:
                    return False
                elif op == "$gt" and field_value <= target:
                    return False
                elif op == "$lt" and field_value >= target:
                    return False
                elif op == "$lte" and field_value > target:
                    return False
            except (ValueError, TypeError):
                return False
        else:
            return False
    return True
 
def remove_code_fences(text: str) -> str:
    # remove ```json ```
    lines = text.splitlines()
    filtered_lines = [line for line in lines if not line.strip().startswith("```")]
    return "\n".join(filtered_lines)
 
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
 
def analyze_server(question):
    prompt = f"""
    You are an AI assistant that extracts relevant field keys and their corresponding content from the user's request.
 
    You must follow these rules:
    - Only choose from the keys listed below in `field_description`. Do not invent new keys.
    - If the user input includes conditions like "at least", "more than", "minimum", or "X or above", include those in the matched content.
    - Extract the most relevant part of the user input for each matched key.
 
    ## Field Descriptions:
    {spec_field_lookup}
 
    ## User Input:
    {question}
 
    ## Output Format (JSON):
    {{
    "matched_keys": [...],
    "matched_content": {{ key: matched_text }}
    }}
    """
    response = llm.invoke(prompt)
    return response.content
 
def clean_server_name(condition,data_list):
    response = "The following project models meet the specified criteria:\n"
    for i, cond in enumerate(condition, 1):
        response += f"Condition #{i}: {condition_to_str(cond)}\n"
    response += "Below are the machines that satisfy each condition combination:\n"
   
    for cond_combo, models in sorted(data_list.items(), key=lambda x: (-len(x[0]), x[0])):
        cond_str = " + ".join(cond_combo) if cond_combo else "No condition matched"
        response += f"\nMatched conditions: {cond_str}\n"
        num = 1
        for model in models:
            response += f"{model}  "
            if num % 3 == 0:
                response += f"\n"
            else:
                response = response
            num += 1
    return response
 
def summarize_result(model,data_list,status):
    if status == "match":
        result = clean_spec(model,data_list)
    else:
        condition = model                           #save difference condition
        result = clean_server_name(condition,data_list)
    return result
 
def criteria_to_str(criteria):
    parts = []
    for op, val in criteria.items():
        op_str = op_mapping.get(op, op)
        parts.append(f"{op_str} {val}")
    return " and ".join(parts)
 
def condition_to_str(cond):
    parts = []
    for field, criteria in cond.items():
        crit_str = criteria_to_str(criteria)
        parts.append(f"{field} {crit_str}")
    return ", ".join(parts)
 
def parse_condition(text):
    # more specific patterns first
    # change at least and less than to mongodb code
    word_to_number = {
        "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
        "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"
    }
   
    # convert word numbers to digits
    for word, digit in word_to_number.items():
        text = re.sub(rf"\b{word}\b", digit, text, flags=re.IGNORECASE)
       
    if m := re.search(r'at least\s+(\d+)', text):
        return {"$gte": m.group(1), '$ne': "None"}
    if m := re.search(r'(\d+)\s+(or more|or above|and up)', text):
        return {"$gte": m.group(1), '$ne': "None"}
    if m := re.search(r'minimum\s+of\s+(\d+)', text):
        return {"$gte": m.group(1), '$ne': "None"}
    if m := re.search(r'minimum\s+(\d+)', text):
        return {"$gte": m.group(1), '$ne': "None"}
    if m := re.search(r'more than\s+(\d+)', text):
        return {"$gt": m.group(1), '$ne': "None"}
    if m := re.search(r'less than\s+(\d+)', text):
        return {"$lt": m.group(1), '$ne': "None"}
    if m := re.search(r'no more than\s+(\d+)', text):
        return {"$lte": m.group(1), '$ne': "None"}
    if m := re.search(r'(\d+)', text):
        return m.group(1)  # fallback: exact match
    return {"$regex":text.strip()}
 
def build_mongo_filter(parsed_input):
    filter_dict = {}
    for key in parsed_input["matched_keys"]:
        text = parsed_input["matched_content"].get(key, "")
        cond = parse_condition(text)
        if cond is not None:
            filter_dict[key] = cond
    return filter_dict
 
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
            result += f"\n- {key} #{idx+1}\n"
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
 
        header = f"{base_key} #{number}" if number else base_key
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