# Hubbify

Hubbify is a small self-hosted ROM browser and downloader. Point it at a ROMs folder, start the Flask server, and you get a simple web page for browsing platforms, game metadata, images, and downloads.

It also has a Universal-Updater feed at `/api/uu.unistore`.

## Requirements

- Python 3.10 or newer
- Flask
- Pillow
- A ROMs folder organized by platform (emulationstation style)
- `tools/tex3ds_x86_64_win.exe` if you want Universal-Updater icon sheets
- `tools/skyscraper_x86_64_win.exe` if you want to scrape game metadata and artwork

Example ROM folder:

```text
roms/
  gb/
    gamelist.xml
    Pokemon Red.gb
    media/
      images/
      marquees/
  gba/
    gamelist.xml
    Metroid Fusion.gba
```

## Setup

Install the Python packages:

```bash
pip install flask pillow
```

Set your ROM folder and public server URL. You can put these in `.env`, or set them in your shell before starting the app. Example:

```text
HOST_URL="http://192.168.1.12:5550/"
ROMS_DIR="D:\\Roms"
```

`HOST_URL` should be the address your other devices can use to reach Hubbify. `ROMS_DIR` should point at your ROM collection.

## Usage

Start the server:

```bash
python app.py
```

Open the site:

```text
http://localhost:5550/
```

Useful routes:

- `/` - browse all detected consoles
- `/platform/<platform>` - browse one console's games
- `/dl/<platform>/<filename>` - download a ROM
- `/api/uu.unistore` - Universal-Updater store file
- `/api/uu/sheet.t3x` - Universal-Updater icon sheet

## Scraping with Skyscraper

Hubbify works best when each platform folder has a `gamelist.xml` and media folders. The included batch file at `tools/scrape.bat` can do that with Skyscraper.

The batch uses the Skyscraper files in `tools`:

```text
tools/
  scrape.bat
  skyscraper_x86_64_win.exe
  skyscraper_artwork.xml
  tex3ds_x86_64_win.exe
```

Run it from the project folder:

```bat
tools\scrape.bat
```

It will ask for your ROMs directory:

```text
ROMs directory: D:\Roms
```

For each platform in the `PLATFORMS` list, it does two passes:

- Scrapes metadata and artwork from ScreenScraper
- Generates `gamelist.xml` and writes media into that platform's `media` folder

If you add or remove systems, edit the `PLATFORMS` line in the batch file. The format is `folder:skyscraper_platform`, so `dsiware:nds` means "use the `dsiware` folder, but scrape it as the `nds` platform."

## Metadata

Hubbify reads console info from `consoles.json` and game info from each platform's `gamelist.xml`.

If a ROM has no metadata, it still shows up using the filename. If artwork is missing, the app falls back to `default.png`.
