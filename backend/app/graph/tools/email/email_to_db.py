# email_to_db.py
import os
import uuid
import logging
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import re

# Configure logging
logger = logging.getLogger(__name__)

def normalize_title(title: str) -> str:
    return re.sub(r"^(RE:|FW:|FWD:)\s*", "", title, flags=re.IGNORECASE).strip()
 
def connect_mongo():
    load_dotenv()
    MONGODB_IP = os.getenv('MONGODB_IP')
    MONGODB_USER = os.getenv('MONGODB_USER')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
    uri = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_IP}:27017/admin"
    client = MongoClient(uri)
    logger.debug("MongoDB connection established")
    return client
 
def process_email_to_mongo(email: dict) -> str:
    """
    email: {
        "Title": ..., "Company Name": ..., "BDM": ...,
        "Summary": ..., "datetime_str": ...
    }
    """
    logger.info(f"Processing email to MongoDB: {email['Title']}")
    client = connect_mongo()
    db = client["BDM-mgmt"]
    project_col = db["BDM-project"]
    company_col = db["company-profile"]
    bdm_col = db["BDM-info"]
 
    try:
        dt = datetime.strptime(email["datetime_str"], "%Y/%m/%d %I:%M %p")
    except ValueError:
        logger.error(f"[email_to_db] Date parsing error: {email['datetime_str']}")
        dt = datetime.now()
 
    company_info = company_col.find_one({"Company Name": email["Company Name"]})
    if not company_info or "Company_id" not in company_info:
        error_msg = f"Company_id not found for: {email['Company Name']}"
        logger.error(f"[email_to_db] {error_msg}")
        raise ValueError(error_msg)
    company_id = company_info["Company_id"]
 
    bdm_info = bdm_col.find_one({"BDM": email["BDM"]})
    if not bdm_info or "BDM_id" not in bdm_info:
        error_msg = f"BDM_id not found for: {email['BDM']}"
        logger.error(f"[email_to_db] {error_msg}")
        raise ValueError(error_msg)
    bdm_id = bdm_info["BDM_id"]
 
    query_key = {"Title": email["Title"]}
    existing = project_col.find_one(query_key)
 
    if existing:
        logger.info(f"Updating existing document for title: {email['Title']}")
        summary_list = existing.get("Summary", [])
        if not isinstance(summary_list, list):
            summary_list = [summary_list] if summary_list else []
        summary_list.append(email["Summary"])
 
        bdm_email_list = existing.get("BDM Email", [])
        if not isinstance(bdm_email_list, list):
            bdm_email_list = [bdm_email_list] if bdm_email_list else []
        bdm_email_list.append(email["Email"])
       
        update_fields = {
            "Summary": summary_list,
            "BDM Email": bdm_email_list,
            "update date": dt,
            "Company_id": company_id,
            "BDM_id": bdm_id
        }
 
        thread_id = existing.get("thread_id")
        if not thread_id:
            date_code = dt.strftime("%y%m%d")
            shortid = uuid.uuid4().hex[:4]
            thread_id = f'{bdm_id}-{company_id}-{date_code}{shortid}'
            logger.debug(f"Generated new thread_id for existing document: {thread_id}")
        update_fields["thread_id"] = thread_id
 
        if not existing.get("create date"):
            update_fields["create date"] = dt
 
        result = project_col.update_one(query_key, {"$set": update_fields})
        if result.modified_count:
            logger.info("Successfully updated existing document")
        else:
            logger.warning("No fields were modified in the update operation")
    else:
        logger.info(f"Creating new document for title: {email['Title']}")
        date_code = dt.strftime("%y%m%d")
        shortid = uuid.uuid4().hex[:4]
        thread_id = f'{bdm_id}-{company_id}-{date_code}{shortid}'
        logger.debug(f"Generated new thread_id: {thread_id}")
 
        new_doc = {
            "Title": email["Title"],
            "Weekly update": [],
            "Server Used": [],
            "End user": None,
            "BDM_id": bdm_id,
            "Status": 0,
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
            "Sender": None,
            "BDM Email": [email["Email"]]
        }
        project_col.insert_one(new_doc)
        logger.info("Successfully inserted new document")
 
    return {
        "thread_id": thread_id,
    }