import requests
from config import SERPER_API
from utils import requests_retry

def search_trending_topics(query:str )-> list[dict]:
  url="https://google.serper.dev/search"
  headers = {"X-API-KEY": SERPER_API,
             "Content-Type": "application/json"}
  payload = {"q": query,
             "num": 5}
  try:  
   make_request=requests_retry(requests.post)
   response= make_request(url, headers=headers, json=payload)
   response.raise_for_status()
   response_json=response.json()
   response_content=response_json["organic"]
   return  response_content
  except Exception as e :
     print(f"[ERROR: searching for the topic]:\n-{e}")
     return []