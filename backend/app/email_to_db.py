# email_to_db.py
import os
import uuid
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
 
 
def connect_mongo():
    load_dotenv()
    MONGODB_IP = os.getenv('MONGODB_IP')
    MONGODB_USER = os.getenv('MONGODB_USER')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
    uri = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_IP}:27017/admin"
    client = MongoClient(uri)
    return client
 
 
def process_email_to_mongo(email: dict) -> str:
    """
    email: {
        "Title": ..., "Company Name": ..., "BDM": ...,
        "Summary": ..., "datetime_str": ...
    }
    """
 
    client = connect_mongo()
    db = client["BDM-mgmt"]
    project_col = db["BDM-project"]
    company_col = db["company-profile"]
    bdm_col = db["BDM-info"]
 
    try:
        dt = datetime.strptime(email["datetime_str"], "%Y/%m/%d %I:%M %p")
    except ValueError:
        print("❌ 日期解析錯誤:", email["datetime_str"])
        dt = datetime.now()
 
    company_info = company_col.find_one({"Company Name": email["Company Name"]})
    if not company_info or "Company_id" not in company_info:
        raise ValueError(f"❌ Company_id not found for: {email['Company Name']}")
    company_id = company_info["Company_id"]
 
    bdm_info = bdm_col.find_one({"BDM": email["BDM"]})
    if not bdm_info or "BDM_id" not in bdm_info:
        raise ValueError(f"❌ BDM_id not found for: {email['BDM']}")
    bdm_id = bdm_info["BDM_id"]
 
    query_key = {"Title": email["Title"]}
    existing = project_col.find_one(query_key)
 
    if existing:
        summary_list = existing.get("Summary", [])
        if not isinstance(summary_list, list):
            summary_list = [summary_list] if summary_list else []
        summary_list.append(email["Summary"])
 
        update_fields = {
            "Summary": summary_list,
            "update date": dt,
            "Company_id": company_id,
            "BDM_id": bdm_id
        }
 
        thread_id = existing.get("thread_id")
        if not thread_id:
            date_code = dt.strftime("%y%m%d")
            shortid = uuid.uuid4().hex[:4]
            thread_id = f'{bdm_id}-{company_id}-{date_code}{shortid}'
        update_fields["thread_id"] = thread_id
 
        if not existing.get("create date"):
            update_fields["create date"] = dt
 
        result = project_col.update_one(query_key, {"$set": update_fields})
        print("✅ Updated existing document" if result.modified_count else "⚠️ No fields modified")
    else:
        date_code = dt.strftime("%y%m%d")
        shortid = uuid.uuid4().hex[:4]
        thread_id = f'{bdm_id}-{company_id}-{date_code}{shortid}'
 
        new_doc = {
            "Title": email["Title"],
            "Weekly update": [],
            "Server Used": [],
            "End user": None,
            "BDM_id": bdm_id,
            "Status": None,
            "Country": None,
            "Customer Type": None,
            "Industry": [],
            "Estimated Revenue": None,
            "Importance": None,
            "Summary": [email["Summary"]],
            "thread_id": thread_id,
            "create date": dt,
            "update date": dt,
            "region": None,
            "Company_id": company_id,
            "Sender": None
        }
        project_col.insert_one(new_doc)
        print("✅ Inserted new document with thread_id.")
 
    return email["Summary"]
 