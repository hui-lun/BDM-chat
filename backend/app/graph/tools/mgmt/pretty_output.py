# def pretty_print_projects(data):
#     result = []
#     for item in data:
#         result.append(f"🔹 Title: {item.get('Title', '(無)')}")
#         result.append(f"- Company Name: {item.get('Company Name', '(無)')}")
#         result.append(f"- End user: {item.get('End user') or '*(null)*'}")
#         result.append(f"- Status: {item.get('Status') or '*(null)*'}")
#         result.append(f"- Country: {item.get('Country') or '*(null)*'}")
#         result.append(f"- Customer Type: {item.get('Customer Type') or '*(null)*'}")
#         result.append(f"- Region: {item.get('region') or '*(null)*'}")
        
#         # Server Used
#         servers = item.get("Server Used", [])
#         result.append(f"- Server Used: {', '.join(servers) if servers else '*(none)*'}")

#         # Summary
#         summary = item.get("Summary", [])
#         if summary:
#             result.append("- Summary:")
#             result.extend([f"  - {s}" for s in summary])
#         else:
#             result.append("- Summary: *(none)*")

#         # Weekly update
#         weekly = item.get("Weekly update", [])
#         if weekly:
#             result.append("- Weekly update:")
#             result.extend([f"  - {w}" for w in weekly])
#         else:
#             result.append("- Weekly update: *(none)*")

#         result.append(f"- Create date: {item.get('create date')}")
#         result.append(f"- Update date: {item.get('update date')}")
#         result.append("") 
#     result.append("") 
#     return "\n".join(result)



# import json

# def pretty_print_projects(project_str):
#     print(f'Input string: {project_str}')
    
#     # 尝试将字符串转换为字典
#     try:
#         # 如果字符串是字典的字符串表示形式
#         if project_str.startswith('{') and project_str.endswith('}'):
#             import ast
#             project = ast.literal_eval(project_str)
#         else:
#             # 尝试解析为JSON
#             project = json.loads(project_str)
#     except (ValueError, SyntaxError, json.JSONDecodeError) as e:
#         print(f"Error parsing project data: {e}")
#         return "Invalid project data"
    
#     # 确保project是字典类型
#     if not isinstance(project, dict):
#         print(f"Expected dict, got {type(project)}")
#         return "Invalid project data"
    
#     print(f"Parsed project type: {type(project)}")
    
#     # 处理字典数据
#     result = []
#     try:
#         result.append(f"🔹 Title: {project.get('Title', '(無)').strip()}")
#         result.append(f"- Company Name: {project.get('Company Name', '') or '*(none)*'}")
#         result.append(f"- Status: {project.get('Status') or '*(none)*'}")
#         result.append(f"- End User: {project.get('End user') or '*(none)*'}")
#         result.append(f"- Country: {project.get('Country') or '*(none)*'}")
#         result.append(f"- Region: {project.get('region') or '*(none)*'}")
#         result.append(f"- Customer Type: {project.get('Customer Type') or '*(none)*'}")
        
#         def format_list_field(field_name, display_name):
#             items = project.get(field_name, [])
#             if isinstance(items, list) and items:
#                 result.append(f"- {display_name}:")
#                 result.extend([f"  • {item}" for item in items if item is not None])
#             else:
#                 result.append(f"- {display_name}: *(none)*")
        
#         format_list_field("Server Used", "Server Used")
#         format_list_field("Industry", "Industry")
        
#         # 处理 Summary
#         summary = project.get("Summary", [])
#         if isinstance(summary, list) and summary:
#             result.append("- Summary:")
#             result.extend([f"  • {item}" for item in summary if item])
#         else:
#             result.append("- Summary: *(none)*")
        
#         # 处理 Weekly update
#         weekly = project.get("Weekly update", [])
#         if isinstance(weekly, list) and weekly:
#             result.append("- Weekly Update:")
#             result.extend([f"  • {item}" for item in weekly if item])
#         else:
#             result.append("- Weekly Update: *(none)*")
        
#         # 添加日期信息
#         result.append(f"- Create Date: {project.get('create date', 'N/A')}")
#         result.append(f"- Last Update: {project.get('update date', 'N/A')}")
        
#         return "\n".join(result)
    
#     except Exception as e:
#         print(f"Error formatting project data: {e}")
#         return f"Error formatting data: {str(e)}"
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