# Importer for GameMaker library Input's Icon Plug-in
#
# Instructions
# 1. Run from a subdirectory adjacent to an Input project
#    - Input's Icon configs are overwritten as appropriate
#    - For graphic sets, "Prompts" with "Alternates" directories are written to "data"
# 2. Import font/graphic assets into GameMaker in your format of choice
# 3. Add the appropriate license to your project datafiles
#
# Additional tips from Antti Vaihia, Gleb Tsereteli
# 1. To open a project directory from the GM IDE: Help > Open Project In Explorer
# 2. For Windows, install Python: https://apps.microsoft.com/detail/9pnrbtzxmb4z
# 3. For Windows, browse for and run the script from Command Prompt or PowerShell
# 4. Import image files by drag & dropping into the GameMaker IDE
# 5. On "Import vector sprite" prompt, "Yes" is vector/SVG, "No" is raster/pixels
#    Note that the import-as prompt may not appear if a GM IDE Preference is set:
#    Sprite Editor > Confirm Dialogs > Load vector sprites as vectors
#    Note that the Scribble library does not support SVG


import sys
if sys.version_info[0] != 3:
    exit("This script requires Python 3.")

import csv
import zipfile
import urllib.request
import webbrowser
from pathlib import Path

FILES_TO_EDIT = [
    Path("../scripts/__InputIconConfigEdgeCases/__InputIconConfigEdgeCases.gml"),
    Path("../scripts/__InputIconConfigKeyboard/__InputIconConfigKeyboard.gml"),
    Path("../scripts/__InputIconConfigNintendo/__InputIconConfigNintendo.gml"),
    Path("../scripts/__InputIconConfigPlayStation/__InputIconConfigPlayStation.gml"),
    Path("../scripts/__InputIconConfigXbox/__InputIconConfigXbox.gml"),
]

def load_csv(path):
    print("Loading CSV")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"  Loaded {len(rows)} rows")
    return rows

def replace_last(line, quoted, replacement):
    i = line.rfind(quoted)
    if i == -1:
        return line
    return line[:i] + replacement + line[i + len(quoted):]

def apply_config_replacements(rows, value_field):
    print("Applying replacements")

    for file_path in FILES_TO_EDIT:
        print(f"  Writing {file_path}")
        if not file_path.exists():
            print("  File not found")
            continue

        lines = file_path.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            best_match = None
            best_value = None
            for row in rows:
                config = row["Input Config"].strip()
                input_string = row["Input String"].strip()
                input_string = f"\"{input_string}\""
                value = row[value_field].strip()
                if config in line and input_string in line:
                    best_match = input_string
                    best_value = value
            if best_match is not None:
                lines[i] = replace_last(line, best_match, best_value)

        file_path.write_text("\n".join(lines), encoding="utf-8")
    print("  Replacement complete")

ZIP_CACHE = {}
ZIP_PATH = "data/kenney_input-prompts_1.5.zip"
ZIP_URL = "https://kenney.nl/media/pages/assets/input-prompts/8de120163f-1777890371/kenney_input-prompts_1.5.zip"
OUT_VECTOR = Path("data/Prompts (Import me!)")
OUT_ALT = Path("data/Prompts (Import me!)/Alternate")

def ensure_zip():
    if Path(ZIP_PATH).exists():
        return
    print("Downloading zip…")
    urllib.request.urlretrieve(ZIP_URL, ZIP_PATH)

def get_zip():
    ensure_zip()
    if ZIP_PATH not in ZIP_CACHE:
        ZIP_CACHE[ZIP_PATH] = zipfile.ZipFile(ZIP_PATH, "r")
    return ZIP_CACHE[ZIP_PATH]

def subfile_path(p):
    return p.split(".zip/", 1)[-1] if ".zip/" in p else p

def extract(inner, out_dir, name):
    zfile = get_zip()
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}.svg"
    with zfile.open(inner) as s, open(out, "wb") as subfile:
        subfile.write(s.read())

def write_macros(rows):
    file_path = FILES_TO_EDIT[0]
    print(f"Writing macros to {file_path}")
    if not file_path.exists():
        print("  File not found")
        return

    lines = file_path.read_text(encoding="utf-8").splitlines()
    lines = [l for l in lines if not l.lstrip().startswith("#macro ")]
    entries = []
    seen = set()
    for row in rows:
        glyph = row["Glyph Name"].strip()
        if glyph in seen:
            continue
        seen.add(glyph)
        entries.append((
            glyph,
            row["Codepoint"].strip(),
            row.get("Alternate", "").strip()
        ))

    macro_names = []
    for glyph, _, alt in entries:
        macro_names.append(glyph)
        if alt:
            macro_names.append(f"{glyph}Alt")

    longest = max((len(n) for n in macro_names), default=0)
    macros = []
    for glyph, codepoint, alt in entries:
        macros.append(f'#macro {glyph.ljust(longest)} "\\u{codepoint}"')
        if alt:
            macros.append(
                f'#macro {(glyph + "Alt").ljust(longest)} "\\u{alt}"'
            )

    output = "\n".join(macros) + "\n\n"
    file_path.write_text(
        output + "\n".join(lines).lstrip("\n"),
        encoding="utf-8"
    )
    print(f"  Wrote {len(macros)} macros")

def yn(prompt, default=False):
    suffix = "Y/n" if default else "y/N"
    answer = input(f"{prompt} ({suffix}): ").strip().lower()
    if not answer:
        return default
    return answer == "y"

def import_kenney_vector():
    rows = load_csv("data/Kenney2Input.csv")
    for row in rows:
        name = row["Asset Name"].strip()
        vector = row["Vector"].strip()
        alternate = row.get("Vector Alternate", "").strip()
        if vector:
            extract(subfile_path(vector), OUT_VECTOR, name)
        if alternate:
            extract(subfile_path(alternate), OUT_ALT, name)

    write_macros([])
    apply_config_replacements(rows, "Asset Name")
    if yn("Open asset website?"):
        webbrowser.open("https://kenney.nl/knowledge-base/game-assets-2d/using-input-prompts")
    if yn("Open license?"):
        webbrowser.open("https://creativecommons.org/publicdomain/zero/1.0/")
    webbrowser.open(OUT_VECTOR.resolve().as_uri())
    print("Done")

def import_font(csv_path, zip_url=None, license_url=None):
    rows = load_csv(csv_path)
    write_macros(rows)
    apply_config_replacements(rows, "Glyph Name")
    if zip_url:
        if yn("Download font?"):
            webbrowser.open(zip_url)
    if license_url:
        if yn("Open license?"):
            webbrowser.open(license_url)

    print("Done")

print("Choose icon set to import")
choice = input(
    "1. Kenney Vector Prompts\n"
    "2. PromptFont Glyphs\n"
    "3. MaruMonica Glyphs\n"
    "4. Exit\n"
    "> "
)

if choice == "1":
    import_kenney_vector()

elif choice == "2":
    import_font(
        "data/PromptFont2Input.csv",
        zip_url = "https://shinmera.com/project/promptfont/releases/download/latest/promptfont.zip",
        license_url = "https://shinmera.com/docs/promptfont/LICENSE.txt",
    )

elif choice == "3":
    import_font(
        "data/MaruMonica2Input.csv",
        zip_url = "https://booth.pm/downloadables/7530579",
        license_url = "https://hicchicc.github.io/00ff/",
    )