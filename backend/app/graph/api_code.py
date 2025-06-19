import requests

BASE_URL = "http://192.168.1.166:8000"

# === call /find_documents ===
def call_find_documents(collection, filter_dict=None, projection_dict=None):
    url = f"{BASE_URL}/find_documents"
    
    payload = {
        "collection": collection,
    }
    
    if filter_dict != None:
        payload['filter_dict'] = filter_dict
    else:
        payload['filter_dict'] = None
    
    if projection_dict != None:
        payload['projection_dict'] = projection_dict
    else:
        payload['projection_dict'] = None
    response = requests.post(url, json=payload)
    return response.json()

# === call /get_qvl_data ===
def call_get_qvl_data(projectmodel, barebone_gbtsn,all_qvl_key,qvl_field_lookup):
    url = f"{BASE_URL}/get_qvl_data"
    payload = {
        "projectmodel": projectmodel,
        "barebone_gbtsn": barebone_gbtsn,
        "all_qvl_key": all_qvl_key,
        "qvl_field_lookup": qvl_field_lookup
    }
    response = requests.post(url, json=payload) 
    return response.json()


# === call /get_projection ===
# (BAREBONE_COLLECTION_NAME, {"ProjectModel": projectmodel}, non_nested_fields)
def call_get_projection(collection, projectmodel, fields):
    url = f"{BASE_URL}/get_projection"
    payload = {
        "collection": collection,
        "projectmodel": projectmodel,
        "fields": fields
    }
    response = requests.post(url, json=payload)
    return response.json()

# === call /get_email ===
def call_get_email(email):
    url = f"{BASE_URL}/get_email"
    payload = {
        "email": email
    }

    response = requests.post(url, json=payload)
    return response.json()

def save_output_file(index):
    url = f"{BASE_URL}/save_file"
    payload = {
        "index":index
    }
    response = requests.post(url,json=payload)
    return response.json()