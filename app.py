# A self-hosted ROMs hosting site with database support for known downloaders (like Universal-Updater, Kekatsu, etc...) made by AzizBgBoss.

from flask import Flask, Response, jsonify, render_template, send_from_directory
from urllib.parse import quote
import json
import os
import scraper
import PIL
from PIL import Image
import subprocess

app = Flask(__name__)
ROMS_DIR = os.getenv("ROMS_DIR", "Roms") # ROMs directory
CONSOLES_JSON = "consoles.json"
DEFAULT_PNG = "default.png"
TEMP_DIR = "temp"
ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mkv", ".avi"}

_DS_PLATFORMS = ["nds", "gb", "gba", "nes", "snes", "dsi"]
_3DS_PLATFORMS = _DS_PLATFORMS + ["3ds", "n64", "psx"]

def load_console_metadata():
    try:
        with open(os.path.join(app.root_path, CONSOLES_JSON), encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}

    if not isinstance(metadata, dict):
        return {}
    return metadata

def get_consoles():
    consoles = []
    systems = scraper.parse_systems(ROMS_DIR)
    metadata = load_console_metadata()

    try:
        platforms = os.listdir(ROMS_DIR)
    except FileNotFoundError:
        return consoles

    for platform in platforms:
        platform_dir = os.path.join(ROMS_DIR, platform)
        if not os.path.isdir(platform_dir):
            continue

        system = systems.get(platform, {})
        console_metadata = metadata.get(platform, {})
        extensions = system.get("extensions") or console_metadata.get("extensions") or []
        console = {
            "platform": platform,
            "name": console_metadata.get("name") or system.get("name") or platform,
            "extensions": extensions,
            "manufacturer": console_metadata.get("manufacturer", ""),
            "type": console_metadata.get("type", ""),
            "generation": console_metadata.get("generation", ""),
            "release_year": console_metadata.get("release_year", ""),
            "description": console_metadata.get("description", ""),
            "unistore_consoles": console_metadata.get("unistore_consoles", []),
        }
        consoles.append(console)

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

    roms = scraper.parse_platform(os.path.join(ROMS_DIR, platform), console.get("extensions"))
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

    extension = os.path.splitext(filename)[1].lower()
    if filename.startswith(("media/", "images/", "downloaded_images/")) or extension in ASSET_EXTENSIONS:
        if os.path.exists(os.path.join(platform_dir, filename)):
            return send_from_directory(platform_dir, filename)
        return default_image()

    game = scraper.get_game(os.path.join(platform_dir, filename), console.get("extensions"))
    if game is None:
        return render_template("404.html"), 404
    game["platform"] = platform
    return render_template("rom.html", console=console, game=game)

@app.route("/dl/<platform>/<path:filename>")
def download(platform, filename):
    return send_from_directory(os.path.join(ROMS_DIR, platform), filename)

@app.route("/api/uu/sheet.t3x")
def universal_updater_spreadsheet():
    return send_from_directory(app.root_path, "images/sheet.t3x")

@app.route("/api/uu.unistore")
def universal_updater():
    host_url = os.getenv("HOST_URL") or ""
    unistore = {
        "storeInfo": {
                "title": "Hubbify",
                "author": "AzizBgBoss",
                "description": "Hubbify - a retro game database",
                "url": host_url + "api/uu.unistore",
                "file": "uu.unistore",
                "sheetURL": host_url + "api/uu/sheet.t3x",
                "sheet": "sheet.t3x",
                "bg_index": 1,
                "bg_sheet": 0,
                "revision": 11,
                "version": 4
        },
        "storeContent": []
    }

    iconidx = 1
    image_entries = 0

    # Generate the Universal-Updater icon spreadsheet.
    images_dir = os.path.join(app.root_path, "images")
    os.makedirs(images_dir, exist_ok=True)
    t3spath = os.path.join(images_dir, "sheet.t3s")
    with open(t3spath, "w", encoding="utf-8") as f:
        f.write("--atlas -f rgba -z auto\n\n../default.png\n")
    for console in get_consoles():
        for rom in scraper.parse_platform(os.path.join(ROMS_DIR, console["platform"]), console.get("extensions")):
            unistore_consoles = console.get("unistore_consoles")
            if not unistore_consoles and (console["platform"] in _DS_PLATFORMS or console["platform"] in _3DS_PLATFORMS):
                unistore_consoles = ["3DS", "DS"] if console["platform"] in _DS_PLATFORMS else ["3DS"]

            if unistore_consoles:
                description = rom.get("description") or rom.get("desc") or ""
                if rom["url"].endswith(".zip"):
                    downloads = [
                        {
                            "type": "downloadFile",
                            "file": host_url + "dl/" + console["platform"] + "/" + quote(rom["url"]),
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
                            "output": "sdmc:/roms/" + console["platform"] + "/",
                        },
                        {
                            "type": "deleteFile",
                            "file": "sdmc:/" + rom["url"],
                        }
                    ]
                else:
                    downloads = [
                        {
                            "type": "mkdir",
                            "directory": "sdmc:/roms/" + console["platform"] + "/",
                        },
                        {
                            "type": "downloadFile",
                            "file": host_url + "dl/" + console["platform"] + "/" + quote(rom["url"]),
                            "output": "sdmc:/roms/" + console["platform"] + "/" + rom["url"],
                        },
                    ]

                icon_index = 0
                if rom.get("marquee"):
                    source_icon = os.path.join(ROMS_DIR, console["platform"], rom["marquee"])
                    source_icon = scraper._normalize_rom_path(source_icon)
                    output_icon_name = f"icon_{iconidx}.png"
                    output_icon = os.path.join(images_dir, output_icon_name)

                    try:
                        icon = Image.open(source_icon)
                        icon = icon.resize((48, 48)).convert("RGBA")
                        icon.save(output_icon)
                    except (OSError, ValueError):
                        icon_index = 0
                    else:
                        icon_index = iconidx
                        iconidx += 1
                        image_entries += 1
                        with open(t3spath, "a", encoding="utf-8") as f:
                            f.write(f"{output_icon_name}\n")

                content = {
                    "info": {
                    "title": rom.get("name") or rom["url"],
                    "author": rom.get("manufacturer") or rom.get("publisher") or rom.get("developer") or "Unknown",
                    "description": description.split(".")[0] if description else "",
                    "category": [console["name"]],
                    "console": unistore_consoles,
                    "icon_index": icon_index,
                    "sheet_index": 0,
                    "last_updated": rom.get("year") or rom.get("releasedate") or "",
                    "license": "none",
                    "version": "0",
                    "stars": int(float(rom.get("rating")) * 20) if rom.get("rating") else 0,
                },
                    "Install ROM to /roms/" + console["platform"] + "/": downloads
                }
                unistore["storeContent"].append(content)
    
    if image_entries:
        tex3ds = os.path.join(app.root_path, "tools", "tex3ds_x86_64_win.exe")
        outputt3x = os.path.join(images_dir, "sheet.t3x")
        subprocess.run([tex3ds, "-i", t3spath, "-o", outputt3x], check=True)
        print(f"Generated {outputt3x}")

    return jsonify(unistore)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5550)
