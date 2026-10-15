import json
import os

def load_posts()->list:
    file_path="memory/content_store.json"
    exists=os.path.exists(file_path)
    if exists==True:
        with open(file_path,"r") as f:
            content = f.read()
            if not content.strip():
                return []
            posts_history=json.loads(content)
        return posts_history
    return []

def save_posts(scheduled_posts)->bool:
    file_path="memory/content_store.json"
    new_posts=[]
    for p in scheduled_posts:
        dic={"platform" : p.platform,
            "copy" : p.copy,
            "hashtags" : p.hashtags ,
            "image_url" : p.image_url ,
            "image_credit ": p.image_credit,
            "date" : p.date}
        new_posts.append(dic)
    posts_history=load_posts()
    posts_history.extend(new_posts)
    with open(file_path,"w") as f:
        json.dump(posts_history,f,indent=2)
    return True

    
