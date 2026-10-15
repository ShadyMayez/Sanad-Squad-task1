from models.schemas import FinalPost,DraftPost
from typing import List
from tools.unsplash_tool import fetch_image
class ImageSourcerAgent():
    def __init__(self):
        pass
    def run(self,draft_posts)->list[FinalPost]:
      final_posts=[]
      for i,p in enumerate(draft_posts):
        print(f"[ImageSourcer] Processing post {i+1}/{len(draft_posts)}...")
        query = p.image_query
        results=fetch_image(query)
        if not results or isinstance(results,list):
            image_url=None
            image_credit=None
        else:
            image_url = results.get("image_url")
            image_credit = results.get("credit")
        try:
            final_post=FinalPost(
                platform=p.platform,
                copy=p.copy,
                hashtags=p.hashtags,
                image_url=image_url,
                image_credit=image_credit)
        except Exception as e:
            print(f"[ERROR creating FinalPost]: {e}")
            print(f"Results was: {results}")
            continue
        final_posts.append(final_post)
      return final_posts