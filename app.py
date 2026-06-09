# A self-hosted ROMs hosting site with database support for known downloaders (like Universal-Updater, Kekatsu, etc...) made by AzizBgBoss.

from flask import Flask, Response, render_template, send_from_directory
import base64
import os
import scraper

app = Flask(__name__)
ROMS_DIR = os.getenv("ROMS_DIR", "roms") # ROMs directory
DEFAULT_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAHgAAAB4CAIAAAC2BqGFAAAA+ElEQVR4nO3QQQ3AIADAQMDv"
    "pCHEINt4emjFsk85mOX9uwEzGxgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgY"
    "GBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgY"
    "GBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgY"
    "GBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgY"
    "GBgYGBgYGBgYGBgYGBgYGBj4Eq8BXgAB0Y0kCwAAAABJRU5ErkJggg=="
)

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
    return render_template("index.html", consoles=get_consoles())

@app.route("/default.png")
def default_image():
    return Response(DEFAULT_PNG, mimetype="image/png")

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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5550)
