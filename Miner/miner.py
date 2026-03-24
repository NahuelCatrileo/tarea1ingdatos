import os
import re
import time
import requests
import redis

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

while True:
    status = r.get("miner_status")
    if status == "stopped":
        time.sleep(5)
        continue
    
def tokenize(name):
    words = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', name).replace('_', ' ')
    return words.lower().split()

def get_functions(content, extension):
    if extension == "py":
        return re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
    elif extension == "java":
        return re.findall(r'(?:public|protected|private|static|\s) +[\w\<\>\[\]]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
    return []

def mine():
    url = "https://api.github.com/search/repositories?q=language:python+language:java&sort=stars&order=desc"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    
    repos = requests.get(url, headers=headers).json().get('items', [])
    
    for repo in repos:
        print(f"Minando: {repo['full_name']}")
        tree_url = f"https://api.github.com/repos/{repo['full_name']}/git/trees/master?recursive=1"
        tree = requests.get(tree_url, headers=headers).json().get('tree', [])
        
        for item in tree:
            if item['path'].endswith(('.py', '.java')):
                raw_url = f"https://raw.githubusercontent.com/{repo['full_name']}/master/{item['path']}"
                code = requests.get(raw_url).text
                
                ext = item['path'].split('.')[-1]
                functions = get_functions(code, ext)
                
                for func in functions:
                    words = tokenize(func)
                    for word in words:
                        r.zincrby("word_ranking", 1, word)
        
        time.sleep(2)

if __name__ == "__main__":
    mine()