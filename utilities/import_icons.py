# PromptFont configuration for GameMaker library Input's Icon Plug-in
#
# Instructions
# Run from a 'Utilities' subdirectory adjacent to Input project

import sys
if sys.version_info[0] != 3:
    exit('This script requires Python 3.')

import subprocess

choice = input(
    "1. Import Kenney Prompts\n"
    "2. Import PromptFont\n"
    "3. Exit\n"
    "> "
)

if choice == "1":
    subprocess.run([sys.executable, "__import_kenney_prompts.py"])
elif choice == "2":
    subprocess.run([sys.executable, "__import_promptfont.py"])