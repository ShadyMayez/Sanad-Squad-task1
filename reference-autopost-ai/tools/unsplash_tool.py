import requests
from config import UNSPLASH_API
from typing import Optional
from utils import requests_retry

def fetch_image(query: str, orientation: str = "landscape")->dict:
    url="https://api.unsplash.com/search/photos"
    headers={"Authorization": f"Client-ID {UNSPLASH_API}"}
    params = {"query": query,
              "per_page": 1,
              "orientation": orientation} 
    try:   
        make_request=requests_retry(requests.get)
        print(f"[Unsplash] Searching for: {query}")
        response = make_request(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        response_json=response.json()
        response_content=response_json["results"]
        if not response_content:
            print(f"[Unsplash] No images found for query: {query}")
            return {}
        image_data=response_content[0]
        image={}
        image["image_url"]=image_data["urls"]["regular"]
        image["image_description"]=image_data["description"]
        image["credit"]=image_data["user"]["username"]
        image["credit_url"]=image_data["user"]["portfolio_url"]
        return image
    except Exception as e:
        print(f"[ERROR: searching for the images]:\n-{e}")
        return {}
