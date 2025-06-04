import json
import ast
from typing import Union, List, Dict, Any

def pretty_print_projects(project_input: Union[str, List, Dict]) -> str:
    def format_single_project(project: Dict[str, Any]) -> str:
        if not project or not isinstance(project, dict):
            return "Invalid project data"
            
        result = []
        try:
            result.append(f"🔹 Title: {project.get('Title', '(無)').strip()}")
            result.append(f"- Company Name: {project.get('Company Name', '') or '*(none)*'}")
            result.append(f"- Status: {project.get('Status') or '*(none)*'}")
            result.append(f"- End User: {project.get('End user') or '*(none)*'}")
            result.append(f"- Country: {project.get('Country') or '*(none)*'}")
            result.append(f"- Region: {project.get('region') or '*(none)*'}")
            result.append(f"- Customer Type: {project.get('Customer Type') or '*(none)*'}")
            
            def format_list_field(field_name: str, display_name: str) -> None:
                items = project.get(field_name, [])
                if not isinstance(items, list):
                    items = [items] if items is not None else []
                
                if items:
                    result.append(f"- {display_name}:")
                    for item in items:
                        if item is not None:
                            result.append(f"  • {item}")
                else:
                    result.append(f"- {display_name}: *(none)*")
            
            format_list_field("Server Used", "Server Used")
            format_list_field("Industry", "Industry")
            
            summary = project.get("Summary", [])
            if not isinstance(summary, list):
                summary = [summary] if summary is not None else []
            if summary:
                result.append("- Summary:")
                result.extend([f"  • {item}" for item in summary if item is not None])
            else:
                result.append("- Summary: *(none)*")
            
            weekly = project.get("Weekly update", [])
            if not isinstance(weekly, list):
                weekly = [weekly] if weekly is not None else []
            if weekly:
                result.append("- Weekly Update:")
                result.extend([f"  • {item}" for item in weekly if item is not None])
            else:
                result.append("- Weekly Update: *(none)*")
            
            result.append(f"- Create Date: {project.get('create date', 'N/A')}")
            result.append(f"- Last Update: {project.get('update date', 'N/A')}")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"Error formatting project data: {str(e)}"
    
    if isinstance(project_input, str):
        project_input = project_input.strip()
        if not project_input:
            return "Empty input data"
            
        try:
            try:
                project_input = json.loads(project_input)
            except json.JSONDecodeError:
                project_input = ast.literal_eval(project_input)
        except (ValueError, SyntaxError) as e:
            return f"Error parsing input: {str(e)}"
    
    if isinstance(project_input, dict):
        print("Parsed as single project")
        return format_single_project(project_input)
    elif isinstance(project_input, list):
        if not project_input:
            return "No projects to display"
            
        print(f"Parsed as list with {len(project_input)} items")
        results = []
        for i, item in enumerate(project_input, 1):
            if isinstance(item, dict):
                results.append(f"=== Project {i} ===\n{format_single_project(item)}")
            else:
                results.append(f"=== Project {i} ===\nInvalid project data")
        return "\n\n".join(results)
    else:
        return f"Unsupported input type: {type(project_input)}"