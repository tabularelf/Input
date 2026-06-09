# Kenney Input Prompts importer for GameMaker library Input's Icon Plug-in
#
# Instructions
# 1. Run from a 'Utilities' subdirectory adjacent to Input project
#    - A "Prompts" with "Alternates" subdirectory of images is written
#    - Input's Icon configs are overwritten with matching assets names 
# 2. Import "Prompts" assets into GameMaker in your format of choice
#
# Additional tips from Antti Vaihia, @glebtsereteli
# 1. To open a project directory from the GM IDE: Help > Open Project In Explorer
# 2. For Windows, install Python: https://apps.microsoft.com/detail/9pnrbtzxmb4z
# 3. For Windows, browse for and run the script from Command Prompt or PowerShell
# 4. Import image files by drag & dropping into the GameMaker IDE
# 5. On "Import vector sprite" prompt, "Yes" is vector/SVG, "No" is raster/pixels
#    Note that the import-as prompt may not appear if a GM IDE Preference is set:
#    Sprite Editor > Confirm Dialogs > Load vector sprites as vectors
#    Note that the Scribble library does not support SVG
#
# Resources
#  Link: https://gist.github.com/offalynne/d7ec15c523c7f8142e614bff3a88c8a8
#  Docs: https://offalynne.grebedoc.dev/Input/#/latest/Plug-in-Binding-Icons
#  Library: https://codeberg.org/offalynne/Input
#  Kenney: https://kenney.nl/knowledge-base/game-assets-2d/using-input-prompts
#  Copyright: https://creativecommons.org/publicdomain/zero/1.0/

import csv
import zipfile
import webbrowser
import urllib.request
from pathlib import Path


CSV_PATH = "data/Kenney2Input.csv"
CSV_URL = "https://gist.githubusercontent.com/offalynne/1ea1e5176b02b53fa3b66c43809fafcf/raw/236fe051667cc7b036a75760c1fc9e33de9af4fc/Kenney2Input.csv"

ZIP_PATH = "data/kenney_input-prompts_1.5.zip"
ZIP_URL = "https://kenney.nl/media/pages/assets/input-prompts/8de120163f-1777890371/kenney_input-prompts_1.5.zip"

ZIP_CACHE = {}

FILES_TO_EDIT = [
    Path("../scripts/__InputIconConfigEdgeCases/__InputIconConfigEdgeCases.gml"),
    Path("../scripts/__InputIconConfigKeyboard/__InputIconConfigKeyboard.gml"),
    Path("../scripts/__InputIconConfigNintendo/__InputIconConfigNintendo.gml"),
    Path("../scripts/__InputIconConfigPlayStation/__InputIconConfigPlayStation.gml"),
    Path("../scripts/__InputIconConfigXbox/__InputIconConfigXbox.gml"),
]

OUT_VECTOR = Path("data/Prompts (Import me!)")
OUT_ALT = Path("data/Prompts (Import me!)/Alternate")

def ensure_csv():
    if Path(CSV_PATH).exists():
        return
    print("Downloading CSV")
    urllib.request.urlretrieve(CSV_URL, CSV_PATH)
    print("  Downloaded")

def ensure_zip():
    if Path(ZIP_PATH).exists():
        return
    print("Downloading zip")
    urllib.request.urlretrieve(ZIP_URL, ZIP_PATH)
    print("  Downloaded")

def get_zip():
    ensure_zip()
    if ZIP_PATH not in ZIP_CACHE:
        ZIP_CACHE[ZIP_PATH] = zipfile.ZipFile(ZIP_PATH, "r")
    return ZIP_CACHE[ZIP_PATH]

def extract_from_zip(inner_path, out_dir, asset_name):
    z = get_zip()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{asset_name}.svg"
    with z.open(inner_path) as src, open(out_path, "wb") as dst:
        dst.write(src.read())

def load_rows():
    ensure_csv()
    print("Loading CSV")
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"  Loaded {len(rows)} rows")
    return rows

def normalize_zip_path(path):
    marker = ".zip/"
    if marker in path:
        return path.split(marker, 1)[1]
    return path

def unpack_assets(rows):
    print("Unpacking assets")
    for row in rows:
        asset = row["Asset Name"].strip()
        vector = row["Vector"].strip()
        alt = row.get("Vector Alternate", "").strip()

        if vector:
            extract_from_zip(
                normalize_zip_path(vector),
                OUT_VECTOR,
                asset)

        if alt:
            extract_from_zip(
                normalize_zip_path(alt),
                OUT_ALT,
                asset)

    print("  Unpacked")

def replace_last_quoted_occurrence(line, quoted, replacement):
    last = line.rfind(quoted)
    if last == -1:
        return line
    return (
        line[:last]
        + replacement
        + line[last + len(quoted):])

def apply_replacements(rows):
    print("Applying replacements")

    for file_path in FILES_TO_EDIT:
        print(f"  Writing {file_path}")

        if not file_path.exists():
            print("  File not found")
            continue

        content = file_path.read_text(encoding="utf-8").splitlines()

        for line_index, line in enumerate(content):

            best_match = None
            best_asset = None

            for row in rows:
                config = row["Input Config"].strip()
                input_str = row["Input String"].strip()
                asset = row["Asset Name"].strip()

                quoted = f"\"{input_str}\""

                if config in line and quoted in line:
                    best_match = quoted
                    best_asset = asset

            if best_match is not None:
                line = replace_last_quoted_occurrence(
                    line,
                    best_match,
                    best_asset)

            content[line_index] = line

        file_path.write_text("\n".join(content), encoding="utf-8")

    print("  Replacement complete")

def main():
    rows = load_rows()
    unpack_assets(rows)
    apply_replacements(rows)
    print("Done")
    webbrowser.open(OUT_VECTOR.resolve().as_uri())
    webbrowser.open("https://kenney.nl/knowledge-base/game-assets-2d/using-input-prompts")

if __name__ == "__main__":
    main()