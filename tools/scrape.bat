@echo off
setlocal
set SKY=%~dp0skyscraper_x86_64_win.exe
set ART=%~dp0skyscraper_artwork.xml

set /p ROMS=ROMs directory: 
if "%ROMS%"=="" (
    echo No ROMs directory entered.
    pause
    exit /b 1
)

if not exist "%ROMS%" (
    echo ROMs directory not found: %ROMS%
    pause
    exit /b 1
)

if not exist "%SKY%" (
    echo Skyscraper not found: %SKY%
    pause
    exit /b 1
)

if not exist "%ART%" (
    echo Artwork config not found: %ART%
    pause
    exit /b 1
)

rem Format: folder:platform
set PLATFORMS=3ds:3ds gb:gb gba:gba gc:gc n64:n64 nds:nds nes:nes ps2:ps2 psx:psx snes:snes wii:wii dsiware:nds

for %%E in (%PLATFORMS%) do (
    for /f "tokens=1,2 delims=:" %%F in ("%%E") do (
        echo.
        echo ============================================================
        echo  Folder: %%F  ^|  Platform: %%G
        echo ============================================================
        echo [1/2] Scraping %%F from ScreenScraper...
        "%SKY%" -p %%G -s screenscraper -i "%ROMS%\%%F" -a "%ART%"
        echo [2/2] Generating gamelist for %%F...
        "%SKY%" -p %%G -i "%ROMS%\%%F" -g "%ROMS%\%%F" -o "%ROMS%\%%F\media" -a "%ART%"
    )
)

echo.
echo ============================================================
echo  All done!
echo ============================================================
pause
