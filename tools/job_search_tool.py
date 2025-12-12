from langchain_community.tools.google_jobs import GoogleJobsQueryRun
from langchain_community.utilities.google_jobs import GoogleJobsAPIWrapper
from langchain.tools import tool
from loguru import logger

@tool
def job_search(query: str) -> str:
    """
    Search for jobs using Google Jobs via SerpApi.
    Useful for finding job postings, employment opportunities, and career openings.
    
    Args:
        query: Search query for jobs (e.g., "entry level physics jobs", "software engineer remote")
        
    Returns:
        A string containing relevant job postings found.
    """
    try:
        api_wrapper = GoogleJobsAPIWrapper()
        job_tool = GoogleJobsQueryRun(api_wrapper=api_wrapper)
        result = job_tool.run(query)
        return result
    except Exception as e:
        logger.error(f"Error searching for jobs: {e}")
        return f"Error searching for jobs: {e}"
