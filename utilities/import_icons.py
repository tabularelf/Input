# Importer for GameMaker library Input's Icon Plug-in
#
# Instructions
# 1. Run from a subdirectory adjacent to an Input project
#    - Input's Icon configs are overwritten as appropriate
#    - For graphic sets, "Prompts" with "Alternates" directories are written to "data"
# 2. Import font or graphic assets into GameMaker in your format of choice
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
import subprocess
from pathlib import Path

FILES_TO_EDIT = [
    Path("../scripts/__InputIconConfigEdgeCases/__InputIconConfigEdgeCases.gml"),
    Path("../scripts/__InputIconConfigKeyboard/__InputIconConfigKeyboard.gml"),
    Path("../scripts/__InputIconConfigNintendo/__InputIconConfigNintendo.gml"),
    Path("../scripts/__InputIconConfigPlayStation/__InputIconConfigPlayStation.gml"),
    Path("../scripts/__InputIconConfigXbox/__InputIconConfigXbox.gml"),
]

DATA_PATH_NAME = "data"
OUT_PATH       = Path(DATA_PATH_NAME) / "Prompts (Import me!)"
OUT_ALT        = OUT_PATH / "Alternate"
CSV_FIELD_NAME = "Asset Name"

ZIP_CACHE = {}

def load_csv(path):
    print("Loading CSV")
    with open(Path(DATA_PATH_NAME) / path, newline="", encoding="utf-8") as f:
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
        print(f"  Rewriting {file_path}")
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

def ensure_zip(path, url):
    if Path(path).exists():
        return
    print(f"Downloading {path}…")
    urllib.request.urlretrieve(url, path)

def get_zip(url):
    path = Path(DATA_PATH_NAME) / url.split("/")[-1]
    ensure_zip(path, url)
    if path not in ZIP_CACHE:
        ZIP_CACHE[path] = zipfile.ZipFile(path, "r")
    return ZIP_CACHE[path]

def subfile_path(p):
    return p.split(".zip/", 1)[-1] if ".zip/" in p else p

def extract(zip_url, inner, out_dir, name, ext="svg"):
    z = get_zip(zip_url)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}.{ext}"
    with z.open(inner) as s, open(out, "wb") as f:
        f.write(s.read())

def write_macros(rows=None):
    if not rows:
        return
    file_path = FILES_TO_EDIT[0]
    print(f"Writing macros to {file_path}")
    if not file_path.exists():
        print("  File not found")
        return

    lines = file_path.read_text(encoding="utf-8").splitlines()
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

PIXEL_SCALE = 16
def crop_region(img, x, y, w, h):
    return img.crop((
        x * PIXEL_SCALE,
        y * PIXEL_SCALE,
        (x + w) * PIXEL_SCALE,
        (y + h) * PIXEL_SCALE,
    ))

def compose_halves(img):
    img = img.convert("RGBA")
    w, h = img.size
    half = w // 2
    left = img.crop((0, 0, half, h)).convert("RGBA")
    right = img.crop((half, 0, w, h)).convert("RGBA")
    left.alpha_composite(right)
    return left

def process_pixel_row(row, source_img):
    asset   = row[CSV_FIELD_NAME].strip()
    compose = row["Compose"].strip().upper() == "TRUE"
    main    = crop_region(source_img, int(row["X"]),     int(row["Y"]),     int(row["W"]),     int(row["H"]))
    alt     = crop_region(source_img, int(row["Alt X"]), int(row["Alt Y"]), int(row["Alt W"]), int(row["Alt H"]))
    if compose:
        main = compose_halves(main)
        alt = compose_halves(alt)
    OUT_PATH.mkdir(parents=True, exist_ok=True)
    OUT_ALT.mkdir( parents=True, exist_ok=True)
    main.save(OUT_PATH / f"{asset}.png")
    alt.save( OUT_ALT  / f"{asset}.png")

VERSION_STRING = "#macro INPUT_VERSION"
def get_version(path):
    for line in path.split("\n"):
        if VERSION_STRING in line:
            return line.split('"')[1]

VECTOR_CSV_PATH = "Kenney2Input.csv"
VECTOR_ZIP_URL  = "https://kenney.nl/media/pages/assets/input-prompts/8de120163f-1777890371/kenney_input-prompts_1.5.zip"
VECTOR_WEB_URL  = "https://kenney.nl/knowledge-base/game-assets-2d/using-input-prompts"
CC0_URL         = "https://creativecommons.org/publicdomain/zero/1.0/"
def import_kenney_vector():
    rows = load_csv(VECTOR_CSV_PATH)
    for row in rows:
        name   = row[CSV_FIELD_NAME].strip()
        vector = row["Vector"].strip()
        alternate = row.get("Vector Alternate", "").strip()
        if vector:
            extract(VECTOR_ZIP_URL ,subfile_path (vector),OUT_PATH ,name)
        if alternate:
            extract(VECTOR_ZIP_URL ,subfile_path (alternate),OUT_ALT ,name)
    if restore_configs():
        write_macros()
        apply_config_replacements(rows, CSV_FIELD_NAME)
    if yn("Open asset website?"):
        webbrowser.open(VECTOR_WEB_URL)
    if yn("Open license?"):
        webbrowser.open(CC0_URL)
    webbrowser.open(OUT_PATH.resolve().as_uri())
    print("Done")

PIXEL_CSV_PATH      = "KenneyPixel2Input.csv"
PIXEL_1BIT_ZIP_URL  = "https://kenney.nl/media/pages/assets/input-prompts-pixel-1-bit/ba3f0202e6-1774771290/kenney_input-prompts-pixel-1-bit.zip"
PIXEL_COLOR_ZIP_URL = "https://kenney.nl/media/pages/assets/input-prompts-pixel/84a40a31f6-1774771309/kenney_input-prompts-pixel.zip"
PIXEL_1BIT_WEB_URL  = "https://kenney.nl/assets/input-prompts-pixel-1-bit"    
PIXEL_COLOR_WEB_URL = "https://kenney.nl/assets/input-prompts-pixel"
def import_kenney_pixel():
    try:
        from PIL import Image
    except ImportError:
        print("Installing Pillow…")
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "Pillow",
        ])
        from PIL import Image
    rows = load_csv(PIXEL_CSV_PATH)
    if restore_configs():
        write_macros()
        apply_config_replacements(rows, CSV_FIELD_NAME)

    if yn("Use color icons?"):
        zip_url = PIXEL_COLOR_ZIP_URL
        web_url = PIXEL_COLOR_WEB_URL
        tilemap_path = "Tilemap/tilemap_packed.png"
    else:
        zip_url = PIXEL_1BIT_ZIP_URL
        web_url = PIXEL_1BIT_WEB_URL
        tilemap_path = "Tilemap/tilemap_white_packed.png"
    z = get_zip(zip_url)
    with z.open(tilemap_path) as f:
        source_img = Image.open(f).convert("RGBA")
    for row in rows:
        process_pixel_row(row, source_img)

    if yn("Open asset website?"):
        webbrowser.open(web_url)
    if yn("Open license?"):
        webbrowser.open(CC0_URL)
    webbrowser.open(OUT_PATH.resolve().as_uri())
    print("Done")

def import_font(csv_path, zip_url=None, license_url=None):
    rows = load_csv(csv_path)
    if restore_configs():
        write_macros(rows)
        apply_config_replacements(rows, "Glyph Name")

    if zip_url:
        if yn("Download font?"):
            webbrowser.open(zip_url)
    if license_url:
        if yn("Open license?"):
            webbrowser.open(license_url)
    print("Done")

PROMPTFONT_CSV_PATH    = "PromptFont2Input.csv"
PROMPTFONT_ZIP_URL     = "https://shinmera.com/project/promptfont/releases/download/latest/promptfont.zip"
PROMPTFONT_LICENSE_URL = "https://shinmera.com/docs/promptfont/LICENSE.txt"
def import_promptfont():
    import_font(PROMPTFONT_CSV_PATH, PROMPTFONT_ZIP_URL, PROMPTFONT_LICENSE_URL)

MARUMONICA_CSV_PATH   = "MaruMonica2Input.csv"
MARUMONIA_ZIP_URL     = "https://booth.pm/downloadables/7530579"
MARUMONIA_LICENSE_URL = "https://hicchicc.github.io/00ff/"
def import_marumonica():
    import_font(MARUMONICA_CSV_PATH, MARUMONIA_ZIP_URL, MARUMONIA_LICENSE_URL)

SOURCE_URL = "https://codeberg.org/offalynne/Input/raw/branch/main/"
REMOTE_VERSION_PATH = SOURCE_URL + "scripts/__InputConstants/__InputConstants.gml"
def restore_configs():
    local  = Path("../" + "/".join(REMOTE_VERSION_PATH.split("/")[-3:])).read_text(encoding="utf-8", errors="ignore")
    remote = urllib.request.urlopen(REMOTE_VERSION_PATH).read().decode("utf-8", errors="ignore")

    ver_local  = get_version(local)
    ver_remote = get_version(remote)
    if ver_local != ver_remote:
        print("Input version mismatch")
        print("  Local :", ver_local)
        print("  Remote:", ver_remote)
        return False

    for path in FILES_TO_EDIT:
        url = (SOURCE_URL + path.as_posix().removeprefix("../"))
        print(f"  Restoring {path}")
        path.write_bytes(urllib.request.urlopen(url).read())
    return True

print("Choose icon set to import")
choice = input(
    " 1. Kenney Vector: SVGs\n"
    " 2. Kenney Pixel: PNGs\n"
    " 3. PromptFont: Vector Font\n"
    " 4. MaruMonica: Pixel Font\n"
    " 5. Restore default Icon configs\n"
    " 6. Exit\n"
    ">"
)
if choice == "1":
    import_kenney_vector()
elif choice == "2":
    import_kenney_pixel()
elif choice == "3":
    import_promptfont()
elif choice == "4":
    import_marumonica()
elif choice == "5":
    restore_configs()