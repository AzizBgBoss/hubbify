# A self-hosted ROMs hosting site with database support for known downloaders (like Universal-Updater, Kekatsu, etc...) made by AzizBgBoss.

from flask import Flask, render_template
import json, os
import scraper
import threading

app = Flask(__name__)
ROMS_DIR = os.getenv("ROMS_DIR", "roms") # ROMs directory
ROMS_META_DIR = os.getenv("ROMS_META_DIR", "roms") # ROMs metadata directory
# Both can be the same btw but I made them different in case you wanna keep your ROMs folder intact

# Make the roms metadata directory if it doesn't exist
if not os.path.exists(ROMS_META_DIR):
    os.makedirs(ROMS_META_DIR)

with open("metadata.json") as f:
    consoles = json.load(f)

for console in consoles:
    console_dir = os.path.join(ROMS_META_DIR, console["platform"])
    if not os.path.exists(console_dir):
        os.makedirs(console_dir)

def update_metadata():
    for console in consoles:
        meta_path = os.path.join(ROMS_META_DIR, console["platform"], "metadata.json")
        roms_dir = os.path.join(ROMS_DIR, console["platform"])
        
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
        else:
            meta = []
        
        try:
            current_roms = set(f for f in os.listdir(roms_dir) if f.endswith(tuple(console["extensions"])))
        except FileNotFoundError:
            print(f"Warning: ROMs directory not found for {console['platform']}")
            continue
        
        meta = [m for m in meta if m["url"] in current_roms]
        
        meta_urls = {m["url"] for m in meta}
        for rom in current_roms:
            if rom not in meta_urls:
                game = scraper.get_game(os.path.join(roms_dir, rom))
                meta.append({
                    "url": rom,
                    "name": game.get("game_title") if game else rom
                })
            else:
                rom_entry = next(m for m in meta if m["url"] == rom)
                if not rom_entry.get("name") or rom_entry["name"] == "":
                    game = scraper.get_game(os.path.join(roms_dir, rom))
                    rom_entry["name"] = game.get("game_title") if game else rom
        
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

for console in consoles:
    meta_path = os.path.join(ROMS_META_DIR, console["platform"], "metadata.json")
    if not os.path.exists(meta_path):
        with open(meta_path, "w") as f:
            json.dump([], f)

metadata_thread = threading.Thread(target=update_metadata, daemon=True)
metadata_thread.start()
                    

@app.route("/")
def index():
    return render_template("index.html", consoles=consoles)

@app.route("/platform/<platform>")
def platform(platform):
    for console in consoles:
        if console["platform"] == platform:
            break
    else:
        return render_template("404.html"), 404
    with open(os.path.join(ROMS_META_DIR, platform, "metadata.json")) as f:
        roms = json.load(f)
    return render_template("platform.html", console=console, roms=roms)

if __name__ == "__main__":
    app.run(debug=True)