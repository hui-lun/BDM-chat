#richard's code
import re
import logging
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper, SearxSearchWrapper
from ...llm import llm

# Configure logging
logger = logging.getLogger(__name__)

# === Optimize Query ===
def optimize_query(query: str) -> str:
    logger.info("[web_search] Optimizing search query")
    prompt = (
        "Extract the most relevant, concise English keywords from the following query for DuckDuckGo search.\n"
        "Requirements:\n"
        "- Only output keywords in a single line, separated by spaces.\n"
        "- Do NOT include explanations, punctuation, or extra words.\n"
        "- Do NOT include function words, stopwords, or filler words (e.g., 'the', 'is', 'about', 'please').\n"
        "- Only keep technical terms, product names, model numbers, or core topic words.\n"
        "- Do NOT translate or modify technical terms or product names.\n"
        "- Do NOT output anything except the keywords.\n"
        f"Query: {query}\n"
    )
    try:
        result = llm.invoke(prompt)
        content = result.content if hasattr(result, "content") else str(result)
        # Only take the first line, avoid LLM returning multiple suggestions or explanations
        optimized = content.splitlines()[0].strip()
        logger.debug(f"[web_search] Optimized query: {optimized}")
        return optimized
    except Exception as e:
        logger.error(f"[web_search] Error optimizing query: {str(e)}")
        return query

# === Score ===
def score_result(res: dict, keywords: list[str]) -> int:
    """
    Calculate the total number of times all keywords in keywords appear within a single search result (res).
    """
    title = res.get("title", "").lower()
    snippet = res.get("snippet", "").lower()[:200]
    combined = title + " " + snippet

    coverage = sum(1 for kw in keywords if kw in combined) / len(keywords)
    total_matches = sum(combined.count(kw) for kw in keywords)
    score = total_matches + 2 * coverage
    return score

# === Keyword Filter ===
def keyword_filter(query: str, results: list, top_k: int = 5) -> list:
    logger.debug(f"[web_search] Filtering results with top_k={top_k}")
    keywords = re.findall(r'\w+', query.lower())
    scored = sorted(results, key=lambda r: score_result(r, keywords), reverse=True)
    
    return scored[:top_k]
# === Search and Summarize Advanced ===
def search_and_summarize(query: str, max_results: int = 10, top_k: int = 5) -> str:
    """
    Use SearxSearchWrapper to fetch structured search results (with URLs), automatically filter the top_k most relevant results using keyword matching, and then summarize the filtered results with LLM.
    """
    searxng_api = SearxSearchWrapper(searx_host='http://searxng:8080')
    # Query optimization
    optimized_query = optimize_query(query)
    print('********************************') 
    print(f"Optimized Query: {optimized_query}")
    print('********************************')

    print(f'test optimized_query: {optimized_query}')
    results = searxng_api.results(optimized_query, max_results)
    # Automatically focus the top_k most relevant results using keyword matching
    filtered = keyword_filter(optimized_query, results, top_k=top_k)

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
        f"- If the search results cover multiple unrelated topics, only answer for the topic most relevant to the user's question. Do not mix information from different topics.\n"
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