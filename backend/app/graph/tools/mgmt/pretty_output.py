def pretty_print_projects(data):
    result = []
    for item in data:
        result.append(f"🔹 Title: {item.get('Title', '(無)')}")
        result.append(f"- Company Name: {item.get('Company Name', '(無)')}")
        result.append(f"- End user: {item.get('End user') or '*(null)*'}")
        result.append(f"- Status: {item.get('Status') or '*(null)*'}")
        result.append(f"- Country: {item.get('Country') or '*(null)*'}")
        result.append(f"- Customer Type: {item.get('Customer Type') or '*(null)*'}")
        result.append(f"- Region: {item.get('region') or '*(null)*'}")
        
        # Server Used
        servers = item.get("Server Used", [])
        result.append(f"- Server Used: {', '.join(servers) if servers else '*(none)*'}")

        # Summary
        summary = item.get("Summary", [])
        if summary:
            result.append("- Summary:")
            result.extend([f"  - {s}" for s in summary])
        else:
            result.append("- Summary: *(none)*")

        # Weekly update
        weekly = item.get("Weekly update", [])
        if weekly:
            result.append("- Weekly update:")
            result.extend([f"  - {w}" for w in weekly])
        else:
            result.append("- Weekly update: *(none)*")

        result.append(f"- Create date: {item.get('create date')}")
        result.append(f"- Update date: {item.get('update date')}")
        result.append("") 
    result.append("") 
    return "\n".join(result)
