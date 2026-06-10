import os
from pathlib import PurePosixPath
import xml.etree.ElementTree as ET


SYSTEM_FILES = ("es_systems.cfg", "es_systems.xml")
GAMELIST_FILE = "gamelist.xml"
SKIP_DIRS = {"media", "images", "downloaded_images", "covers", "boxart", "manuals", "videos"}
SKIP_FILES = {GAMELIST_FILE, "metadata.json"}
SKIP_EXTENSIONS = {".cfg", ".xml", ".txt", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mkv", ".avi", ".sav"}


def _text(parent, tag, default=""):
    element = parent.find(tag)
    if element is None or element.text is None:
        return default
    return element.text.strip()


def _safe_parse(path):
    try:
        return ET.parse(path)
    except (FileNotFoundError, ET.ParseError, OSError):
        return None


def _make_platform_relative(path, platform_dir):
    if not path or not platform_dir:
        return path

    path_for_os = path.replace("/", os.sep).replace("\\", os.sep)
    if not os.path.isabs(path_for_os):
        return path

    try:
        platform_root = os.path.abspath(platform_dir)
        absolute_path = os.path.abspath(path_for_os)
        if os.path.commonpath([platform_root, absolute_path]) == platform_root:
            return os.path.relpath(absolute_path, platform_root)
    except (OSError, ValueError):
        pass

    return path


def _normalize_rom_path(path, platform_dir=None):
    path = _make_platform_relative(path or "", platform_dir)
    path = (path or "").replace("\\", "/").strip()
    while path.startswith("./"):
        path = path[2:]
    return path.strip("/")


def _normalize_media_path(path, platform_dir=None):
    path = _normalize_rom_path(path, platform_dir)
    if path.startswith("../"):
        return ""
    return str(PurePosixPath(path)) if path else ""


def _default_game(platform_dir, rom_path):
    name = os.path.splitext(os.path.basename(rom_path))[0]
    image_base = name + ".png"

    return {
        "path": rom_path,
        "url": rom_path,
        "name": name,
        "game_title": name,
        "description": "",
        "desc": "",
        "image": str(PurePosixPath("media", "images", image_base)),
        "boximage": str(PurePosixPath("media", "box2dfront", image_base)),
        "marquee": "",
        "thumbnail": "",
        "video": "",
        "rating": "",
        "releasedate": "",
        "year": "",
        "developer": "",
        "publisher": "",
        "manufacturer": "",
        "genre": "",
        "players": "",
        "favorite": "",
        "hidden": "",
        "kidgame": "",
        "playcount": "",
        "lastplayed": "",
        "rom": {
            "name": rom_path,
            "size": _file_size(os.path.join(platform_dir, rom_path)),
        },
    }


def _file_size(path):
    try:
        return str(os.path.getsize(path))
    except OSError:
        return ""


def _year_from_releasedate(releasedate):
    if len(releasedate) >= 4 and releasedate[:4].isdigit():
        return releasedate[:4]
    return ""


def _game_from_element(platform_dir, game_element):
    rom_path = _normalize_rom_path(_text(game_element, "path"), platform_dir)
    if not rom_path:
        return None

    game = _default_game(platform_dir, rom_path)
    releasedate = _text(game_element, "releasedate")
    desc = _text(game_element, "desc")
    developer = _text(game_element, "developer")
    publisher = _text(game_element, "publisher")

    game.update({
        "name": _text(game_element, "name", game["name"]),
        "game_title": _text(game_element, "name", game["game_title"]),
        "description": desc,
        "desc": desc,
        "image": _normalize_media_path(_text(game_element, "image"), platform_dir) or game["image"],
        "boximage": _normalize_media_path(_text(game_element, "box2dfront"), platform_dir) or _normalize_media_path(_text(game_element, "thumbnail"), platform_dir) or _normalize_media_path(_text(game_element, "image"), platform_dir) or game["boximage"],
        "marquee": _normalize_media_path(_text(game_element, "marquee"), platform_dir),
        "thumbnail": _normalize_media_path(_text(game_element, "thumbnail"), platform_dir),
        "video": _normalize_media_path(_text(game_element, "video"), platform_dir),
        "rating": _text(game_element, "rating"),
        "releasedate": releasedate,
        "year": _year_from_releasedate(releasedate),
        "developer": developer,
        "publisher": publisher,
        "manufacturer": publisher or developer,
        "genre": _text(game_element, "genre"),
        "players": _text(game_element, "players"),
        "favorite": _text(game_element, "favorite"),
        "hidden": _text(game_element, "hidden"),
        "kidgame": _text(game_element, "kidgame"),
        "playcount": _text(game_element, "playcount"),
        "lastplayed": _text(game_element, "lastplayed"),
    })
    return game


def parse_gamelist(path):
    tree = _safe_parse(path)
    if tree is None:
        return {}

    platform_dir = os.path.dirname(path)
    games = {}
    root = tree.getroot()

    for game_element in root.findall("game"):
        game = _game_from_element(platform_dir, game_element)
        if game is None:
            continue
        games[game["url"]] = game

    return games


def _is_rom_file(path, extensions=None):
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower()

    if name in SKIP_FILES or ext in SKIP_EXTENSIONS:
        return False
    if extensions:
        return ext in extensions
    return True


def list_rom_files(path, extensions=None):
    roms = []
    extensions = {ext.lower() for ext in extensions or []}

    try:
        entries = os.listdir(path)
    except OSError:
        return roms

    for entry in entries:
        entry_path = os.path.join(path, entry)
        if os.path.isdir(entry_path) or not _is_rom_file(entry_path, extensions):
            continue
        roms.append(entry)

    return sorted(roms, key=lambda rom: rom.lower())


def parse_platform(path, extensions=None):
    scraped_games = parse_gamelist(os.path.join(path, GAMELIST_FILE))
    games = []

    for rom_path in list_rom_files(path, extensions):
        game = scraped_games.get(rom_path) or scraped_games.get("./" + rom_path) or _default_game(path, rom_path)
        game["url"] = rom_path
        game["path"] = rom_path
        game["rom"]["name"] = rom_path
        game["rom"]["size"] = _file_size(os.path.join(path, rom_path))
        games.append(game)

    return games


def get_game(path, extensions=None):
    rom_name = os.path.basename(path)
    platform_dir = os.path.dirname(path)

    for game in parse_platform(platform_dir, extensions):
        if game["url"] == rom_name:
            return game

    if os.path.exists(path) and _is_rom_file(path, extensions):
        return _default_game(platform_dir, rom_name)

    return None


def find_systems_file(path):
    for filename in SYSTEM_FILES:
        system_path = os.path.join(path, filename)
        if os.path.exists(system_path):
            return system_path
    return None


def parse_systems(path):
    systems_path = find_systems_file(path)
    tree = _safe_parse(systems_path) if systems_path else None
    systems = {}

    if tree is None:
        return systems

    root = tree.getroot()
    for system in root.findall("system"):
        name = _text(system, "name")
        if not name:
            continue
        extensions = [ext.lower() for ext in _text(system, "extension").split() if ext.startswith(".")]
        systems[name] = {
            "platform": name,
            "name": _text(system, "fullname", name),
            "path": _normalize_rom_path(_text(system, "path")),
            "extensions": extensions,
            "theme": _text(system, "theme"),
            "command": _text(system, "command"),
            "emulators": _text(system, "emulators"),
        }

    return systems
