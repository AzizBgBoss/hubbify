# A self-hosted ROMs hosting site with database support for known downloaders (like Universal-Updater, Kekatsu, etc...) made by AzizBgBoss.

from flask import Flask, Response, jsonify, render_template, send_from_directory
import base64
import os
import scraper

app = Flask(__name__)
ROMS_DIR = os.getenv("ROMS_DIR", "roms") # ROMs directory
DEFAULT_PNG = "default.png"
TEMP_DIR = "temp"

_DS_PLATFORMS = ["nds", "gb", "gba", "nes", "snes", "dsi"]
_3DS_PLATFORMS = _DS_PLATFORMS + ["3ds", "n64", "psx"]

def get_consoles():
    consoles = []

    try:
        platforms = os.listdir(ROMS_DIR)
    except FileNotFoundError:
        return consoles

    for platform in platforms:
        platform_dir = os.path.join(ROMS_DIR, platform)
        if not os.path.isdir(platform_dir):
            continue

        dat_path = scraper.find_dat(platform_dir)
        if dat_path is None:
            continue

        header = scraper.parse_header(dat_path)
        consoles.append({
            "platform": platform,
            "name": header.get("name") or platform,
        })

    return sorted(consoles, key=lambda console: console["name"].lower())

@app.route("/")
def index():
    return render_template("index.html", consoles=get_consoles(), host_url=os.getenv("HOST_URL"))

@app.route("/default.png")
def default_image():
    return send_from_directory(app.root_path, DEFAULT_PNG)

@app.route("/style.css")
def stylesheet():
    return send_from_directory(app.root_path, "style.css")

@app.route("/platform/<platform>")
def platform(platform):
    for console in get_consoles():
        if console["platform"] == platform:
            break
    else:
        return render_template("404.html"), 404

    roms = scraper.parse_platform(os.path.join(ROMS_DIR, platform))
    return render_template("platform.html", console=console, roms=roms)

@app.route("/platform/<platform>/<path:filename>")
def rom_file(platform, filename):
    for console in get_consoles():
        if console["platform"] == platform:
            break
    else:
        return render_template("404.html"), 404
    platform_dir = os.path.join(ROMS_DIR, platform)

    if filename == "default.png":
        return default_image()

    if filename.startswith("media/"):
        media_path = os.path.join(platform_dir, filename)
        if os.path.exists(media_path):
            return send_from_directory(platform_dir, filename)
        return default_image()

    game = scraper.get_game(os.path.join(platform_dir, filename))
    if game is None:
        return render_template("404.html"), 404
    game["platform"] = platform
    return render_template("rom.html", console=console, game=game)

@app.route("/dl/<platform>/<path:filename>")
def download(platform, filename):
    return send_from_directory(os.path.join(ROMS_DIR, platform), filename)

@app.route("/api/uu.unistore")
def universal_updater():
    unistore = {
        "storeInfo": {
                "title": "Hubbify",
                "author": "AzizBgBoss",
                "description": "Hubbify - a retro game database",
                "url": os.getenv("HOST_URL") + "api/uu.unistore",
                "file": "uu.unistore",
                "sheetURL": "",
                "sheet": "",
                "bg_index": 1,
                "bg_sheet": 0,
                "revision": 1,
                "version": 4
        },
        "storeContent": []
    }

    for console in get_consoles():
        for rom in scraper.parse_platform(os.path.join(ROMS_DIR, console["platform"])):
            if console["platform"] in _DS_PLATFORMS or console["platform"] in _3DS_PLATFORMS:
                if rom["url"].endswith(".zip"):
                    downloads = [
                        {
                            "type": "downloadFile",
                            "file": os.getenv("HOST_URL") + "dl/" + console["platform"] + "/" + rom["url"],
                            "output": "sdmc:/" + rom["url"],
                        },
                        {
                            "type": "mkdir",
                            "directory": "sdmc:/roms/" + console["platform"] + "/",
                        },
                        {
                            "type": "extractFile",
                            "file": "sdmc:/" + rom["url"],
                            "input": "",
                            "output": "sdmc:/" + rom["url"],
                        },
                        {
                            "type": "deleteFile",
                            "file": "sdmc:/" + rom["url"],
                        }
                    ]
                else:
                    downloads = [
                        {
                            "type": "downloadFile",
                            "file": os.getenv("HOST_URL") + "dl/" + console["platform"] + "/" + rom["url"],
                            "output": "sdmc:/" + rom["url"],
                        },
                        {
                            "type": "mkdir",
                            "directory": "sdmc:/roms/" + console["platform"] + "/",
                        },
                        {
                            "type": "move",
                            "old": "sdmc:/" + rom["url"],
                            "new": "sdmc:/roms/" + console["platform"] + "/" + rom["url"],
                        }
                    ]

                content = {
                    "info": {
                    "title": rom["name"],
                    "author": rom["manufacturer"],
                    "description": rom["description"].split(".")[0],
                    "category": [console["name"]],
                    "console": ["3DS", "DS"] if console["platform"] in _DS_PLATFORMS else ["3DS"],
                    "icon_index": 0,
                    "sheet_index": 0,
                    "last_updated": rom["year"],
                    "license": "none",
                    "version": "0"
                },
                    "Install ROM to /roms/" + console["platform"] + "/": downloads
                }
                unistore["storeContent"].append(content)

    return jsonify(unistore)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5550)
