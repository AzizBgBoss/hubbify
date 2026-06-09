# After using Skraper, the following data will be made:
# A .dat file in XML format
# A media folder with images subfolder containing all the images

import os
from pathlib import PurePosixPath
import glob
import xml.etree.ElementTree as ET


def _text(parent, tag, default=""):
    element = parent.find(tag)
    if element is None or element.text is None:
        return default
    return element.text.strip()


def parse_dat(path):
    tree = ET.parse(path)
    root = tree.getroot()
    games = []
    for game_element in root.findall("game"):
        rom_element = game_element.find("rom")
        if rom_element is None:
            continue

        rom_name = rom_element.get("name", "")
        image_base = os.path.splitext(rom_name)[0] + ".png"
        image_path = str(PurePosixPath("media", "images", image_base))
        boximage_path = str(PurePosixPath("media", "box2dfront", image_base))

        games.append({
            "game_title": game_element.get("name", ""),
            "name": game_element.get("name", ""),
            "url": rom_name,
            "description": _text(game_element, "description"),
            "year": _text(game_element, "year"),
            "manufacturer": _text(game_element, "manufacturer"),
            "rom": {
                "name": rom_name,
                "size": rom_element.get("size", ""),
            },
            "image": image_path,
            "boximage": boximage_path,
        })

    return games


def parse_header(path):
    tree = ET.parse(path)
    root = tree.getroot()
    header = root.find("header")

    if header is None:
        return {}

    return {
        "name": _text(header, "name"),
        "description": _text(header, "description"),
        "version": _text(header, "version"),
        "date": _text(header, "date"),
        "author": _text(header, "author"),
        "url": _text(header, "url"),
    }


def find_dat(path):
    dat_files = glob.glob(os.path.join(path, "*.dat"))
    if not dat_files:
        return None
    return dat_files[0]


def parse_platform(path):
    games = []

    for dat_path in glob.glob(os.path.join(path, "*.dat")):
        games.extend(parse_dat(dat_path))

    return games


def get_game(path):
    rom_name = os.path.basename(path)
    dat_dir = os.path.dirname(path)

    for dat_path in glob.glob(os.path.join(dat_dir, "*.dat")):
        for game in parse_dat(dat_path):
            if game["rom"]["name"] == rom_name:
                return game

    return None
