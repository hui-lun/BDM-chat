from .llm import llm

def markdown_output(data):
    prompt = (
        "You are a professional technical writer. "
        "Please rewrite the following content into a well-structured, professional Markdown format. "
        "The output should include:\n"
        "- A level-2 Markdown title (## Title)\n"
        "- Section headers in bold (e.g., **1. Overview**)\n"
        "- Bullet points or numbered lists where appropriate\n"
        "- Important terms in bold (e.g., **Company Name**)\n"
        "- One blank line between sections for readability\n\n"
        "Here is the content:\n"
        f"{data}"
    )

    response_text = llm.invoke(prompt).content.strip()
    return response_text