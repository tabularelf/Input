# PromptFont configuration for GameMaker library Input's Icon Plug-in
#
# Instructions
# 1. Run from a 'Utilities' subdirectory adjacent to Input project
#    Input's default Icon config strings are overwritten with PromptFont glyph references
# 2. Manually import PromptFont to project in IDE
#
# Resources
#  Link: https://gist.github.com/offalynne/e5ad9ff2a14d7d89a6b6f6c3c3acf313
#  Docs: https://offalynne.grebedoc.dev/Input/#/latest/Plug-in-Binding-Icons
#  Library: https://codeberg.org/offalynne/Input
#  PromptFont: https://shinmera.com/docs/promptfont/
#  Copyright: https://shinmera.com/docs/promptfont/LICENSE.txt

import sys
if sys.version_info[0] != 3:
    exit('This script requires Python 3.')

import csv
import webbrowser
import urllib.request
from pathlib import Path

CSV_PATH = "data/PromptFont2Input.csv"
CSV_URL = "https://gist.githubusercontent.com/offalynne/6f8ae4fad0ee8b6ac53b57a2c82f9752/raw/0b23a691a58103e1f1ba8006225e8c281e6ac508/PromptFont2Input.csv"

FILES_TO_EDIT = [
    Path("../scripts/__InputIconConfigEdgeCases/__InputIconConfigEdgeCases.gml"),
    Path("../scripts/__InputIconConfigKeyboard/__InputIconConfigKeyboard.gml"),
    Path("../scripts/__InputIconConfigNintendo/__InputIconConfigNintendo.gml"),
    Path("../scripts/__InputIconConfigPlayStation/__InputIconConfigPlayStation.gml"),
    Path("../scripts/__InputIconConfigXbox/__InputIconConfigXbox.gml"),
]

def ensure_csv():
    if Path(CSV_PATH).exists():
        return
    print("Downloading CSV")
    urllib.request.urlretrieve(CSV_URL, CSV_PATH)
    print("  Downloaded")

def load_rows():
    ensure_csv()
    print("Loading CSV")
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"  Loaded {len(rows)} rows")
    return rows

def replace_last_quoted_occurrence(line, quoted, replacement):
    last = line.rfind(quoted)
    if last == -1:
        return line
    return (
        line[:last]
        + replacement
        + line[last + len(quoted):])

def write_macros(rows):
    file_path = FILES_TO_EDIT[0]
    print(f"Writing macros to {file_path}")
    if not file_path.exists():
        print("  File not found")
        return

    lines = file_path.read_text(encoding="utf-8").splitlines()
    lines = [
        line
        for line in lines
        if not line.lstrip().startswith("#macro ")]

    entries = []
    seen = set()
    for row in rows:
        glyph = row["Glyph Name"].strip()
        if glyph in seen:
            continue
        seen.add(glyph)
        entries.append(
            (
                glyph,
                row["Codepoint"].strip(),
                row.get("Alternate", "").strip()))

    macro_names = []
    for glyph, _, alt in entries:
        macro_names.append(glyph)
        if alt:
            macro_names.append(f"{glyph}Alt")

    longest = max(len(name) for name in macro_names) if macro_names else 0
    macros = []
    for glyph, codepoint, alt in entries:
        macros.append(
            f'#macro {glyph.ljust(longest)} "\\u{codepoint}"')
        if alt:
            macros.append(
                f'#macro {(glyph + "Alt").ljust(longest)} "\\u{alt}"')

    output = "\n".join(macros) + "\n\n"
    file_path.write_text(
        output + "\n".join(lines).lstrip("\n"),
        encoding="utf-8")
    print(f"  Wrote {len(macros)} macros")

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
            best_glyph = None
            for row in rows:
                config = row["Input Config"].strip()
                input_str = row["Input String"].strip()
                glyph = row["Glyph Name"].strip()
                
                quoted = f"\"{input_str}\""
                if config in line and quoted in line:
                    best_match = quoted
                    best_glyph = glyph

            if best_match is not None:
                line = replace_last_quoted_occurrence(
                    line,
                    best_match,
                    best_glyph)

            content[line_index] = line

        file_path.write_text(
            "\n".join(content),
            encoding="utf-8")

    print("  Replacement complete")

def main():
    rows = load_rows()
    write_macros(rows)
    apply_replacements(rows)    
    webbrowser.open("https://shinmera.com/project/promptfont/releases/download/latest/promptfont.zip")
    print("Done")
    webbrowser.open("https://shinmera.com/docs/promptfont/LICENSE.txt")


if __name__ == "__main__":
    main()