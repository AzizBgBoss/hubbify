# We will use TheGamesDB, api.thegamesdb.net

import requests
import json
import os
import hashlib

BASE_URL = "https://api.thegamesdb.net"
API_KEY = os.getenv("API_KEY")
CACHE_DIR = "cache"

if not API_KEY:
    print("WARNING: API_KEY environment variable not set. TheGamesDB API requests will fail.")

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_json(url):
    cache_path = os.path.join(CACHE_DIR, url.split("/")[-1].replace("?apikey=" + (API_KEY or ""), "") + ".json")
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            return json.load(f)
    response = requests.get(url)
    if not response.ok:
        print(f"API Error: {response.status_code} - {response.text}")
        return None
    with open(cache_path, "w") as f:
        json.dump(response.json(), f)
    return response.json()

def md5(path):
    if not os.path.exists(path):
        return
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def get_platform_id_by_name(name):
    url = f"{BASE_URL}/v1/Platforms/ByPlatformName?apikey={API_KEY}&name={name}"
    try:
        response = get_json(url)
        return response["data"]["platforms"][0]["id"]
    except:
        return

def get_game_by_hash(path):
    if not os.path.exists(path):
        return
    
    hash = md5(path)
    url = f"{BASE_URL}/v1/Games/ByGameHash?apikey={API_KEY}&hash={hash}"
    print(f"Hash: {hash}")
    try:
        response = get_json(url)
        if response and "data" in response and "games" in response["data"] and len(response["data"]["games"]) > 0:
            return response["data"]["games"][0]
        else:
            print(f"No games found for hash: {hash}")
            return
    except Exception as e:
        print(f"Error getting game by hash: {e}")
        return

def get_game_by_name(path):
    if not os.path.exists(path):
        return
    
    name = os.path.basename(path)
    name = name.split(".")[0]
    platform = os.path.basename(os.path.dirname(path))
    platform_id = get_platform_id_by_name(platform)
    if not platform_id:
        print(f"Platform not found: {platform}")
        return
    
    url = f"{BASE_URL}/v1/Games/ByGameName?apikey={API_KEY}&name={name}&platform={platform_id}"
    print(f"Name: {name}")
    try:
        response = get_json(url)
        if response and "data" in response and "games" in response["data"] and len(response["data"]["games"]) > 0:
            return response["data"]["games"][0]
        else:
            print(f"No games found for name: {name}")
            return
    except Exception as e:
        print(f"Error getting game by name: {e}")
        return

def get_game(path):

    print(f"Scraping {path}")

    if not os.path.exists(path):
        return
    
    game = get_game_by_hash(path)
    if not game:
        game = get_game_by_name(path)
        if not game:
            return
    return game

