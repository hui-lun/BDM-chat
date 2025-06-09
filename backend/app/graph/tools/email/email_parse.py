from datetime import datetime
from .email_summarize import process_email
import logging

logger = logging.getLogger(__name__)

# format for mongoDB
def mail_format_database(email_info: dict) -> dict:
    """
    將 email_info 格式轉換成標準格式：
    {
        "Title": ..., "Company Name": ..., "BDM": ...,
        "Summary": ..., "datetime_str": ...
    }
    """

    title = email_info.get("subject", "(無主旨)")
    company_name = email_info.get("from", "(無寄件者)")
    bdm = email_info.get("to", "(無收件者)")
    summary = email_info.get("summary", "(無摘要)")
    email = email_info.get("email", "(無內容)")
    raw_date = email_info.get("date", "")
    raw_date = raw_date.split(" (")[0] 
    # time format
    try:    
        dt = datetime.strptime(raw_date, "%a %b %d %Y %H:%M:%S GMT%z")
        datetime_str = dt.strftime("%Y/%-m/%-d %-I:%M %p")
    except Exception as e:
        logger.error(f" [convert_email_info] Date format error: {e}")
        datetime_str = raw_date  # fallback raw date

    # all format
    email = {
        "Title": title,
        "Company Name": company_name,
        "BDM": bdm,
        "Summary": summary,
        "datetime_str": datetime_str,
        "Email": email
    }

    return email


def parse_email_query(query: str) -> dict:
    """Parse email query string into a dictionary of email information and generate summary.
    Expected format:
    Subject: <subject>
    From: <sender>
    To: <recipients>
    Date: <datetime>
    email: <query>
    <body>
    """
    lines = query.split('\n')
    email_info = {}
    body_lines = []
    in_body = False
    
    for line in lines:
        line = line.strip()
        if not line and not in_body:
            in_body = True
            continue
            
        if in_body:
            body_lines.append(line)
        else:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                email_info[key] = value
    
    body = '\n'.join(body_lines).strip()
    email_info['body'] = body
    email_info['email'] = query
    # Generate summary using process_email
    email_info['summary'] = process_email(body)

    return email_info