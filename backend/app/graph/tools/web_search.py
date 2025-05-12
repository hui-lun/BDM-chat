#richard's code
import re
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from ..llm import llm

# === Optimize Query ===
def optimize_query(query: str) -> str:
    prompt = (
        f"Only reply with the most suitable English keywords for DuckDuckGo search, no explanations, no punctuation, no extra words. "
        f"Just output the keywords:\n{query}\n"
        f"Please follow the whole of query {query} to optimize the keywords."
    )
    try:
        result = llm.invoke(prompt)
        content = result.content if hasattr(result, "content") else str(result)
        # Only take the first line, avoid LLM returning multiple suggestions or explanations
        return content.splitlines()[0].strip()
    except Exception:
        return query
# === Score ===
def score_result(res: dict, keywords: list[str]) -> int:
    """
    Calculate the total number of times all keywords in keywords appear within a single search result (res).
    """
    title = res.get("title", "").lower()
    snippet = res.get("snippet", "").lower()[:200]
    combined = title + " " + snippet

    coverage      = sum(1 for kw in keywords if kw in combined) / len(keywords)
    total_matches = sum(combined.count(kw) for kw in keywords)
    score         = total_matches + 2 * coverage
    return score
    # combined = (res.get("title", "") + " " + res.get("snippet", "")).lower()
    # return sum(combined.count(kw) for kw in keywords)

# === Keyword Filter ===
def keyword_filter(query: str, results: list, top_k: int = 5) -> list:
    keywords = re.findall(r'\w+', query.lower())
    scored = sorted(results, key=lambda r: score_result(r, keywords), reverse=True)
    
    return scored[:top_k]
# === Search and Summarize Advanced ===
def search_and_summarize_advanced(query: str, max_results: int = 10, top_k: int = 5) -> str:
    """
    Use DuckDuckGoSearchAPIWrapper to fetch structured search results (with URLs), automatically filter the top_k most relevant results using keyword matching, and then summarize the filtered results with LLM.
    """
    duck_api = DuckDuckGoSearchAPIWrapper()
    # Query optimization
    optimized_query = optimize_query(query)
    print('********************************') 
    print(f"Optimized Query: {optimized_query}")
    print('********************************')
    # try:
    #     results = duck_api.results(optimized_query, max_results)
    # except Exception as e:
    #     return f"DuckDuckGo search failed: {e}"
    # if not results or not isinstance(results, list):
    #     return "No relevant webpages found."

    full_query = f"{query} {optimized_query}"
    results = duck_api.results(full_query, max_results)
    # Automatically focus the top_k most relevant results using keyword matching
    filtered = keyword_filter(full_query, results, top_k=top_k)

    context = ""
    print('********************************')
    print(f"Filtered Results: {filtered}")
    print('********************************')
    for idx, res in enumerate(filtered, 1):
        title = res.get("title", "")
        snippet = res.get("snippet", "")
        url = res.get("link", "")
        context += f"{idx}. {title}\n{snippet}\nURL: {url}\n\n"
    prompt = (
        f"Based ONLY on the following DuckDuckGo search results, answer the user's question as accurately as possible.\n"
        f"Original Question: {query}\n"
        f"Optimized Question: {optimized_query}\n"
        f"Search Results:\n{context}\n"
        f"- Only use information that is explicitly present in the search results. Do NOT use any prior knowledge, inference, or assumptions.\n"
        f"- If the answer cannot be found in the search results, reply exactly: 'Not enough information in the search results.'\n"
        f"- Summarize the answer in 200 words or less. Avoid repeating content or the question.\n"
        f"- The answer should be a single, concise paragraph in plain text, without any special formatting, bullet points, or markdown symbols.\n"
        f"- Do not include the results number or URL in the answer.\n"
        f"- Do not include any ** or * in the answer.\n"
    )
    try:
        answer = llm.invoke(prompt)
        return answer.content if hasattr(answer, "content") else str(answer)
    except Exception as e:
        return f"LLM analysis failed: {e}"