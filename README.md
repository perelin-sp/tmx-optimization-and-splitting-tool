# TMX Optimization and Splitting Tool

**TMX Optimization and Splitting Tool**, or **TOST**, is a Windows desktop utility for preparing TMX translation memory files for safer import into CAT tools.

TOST focuses on a conservative workflow: analyze TMX files, safely split large files, optionally create optimized copies, compare TMX versions, and generate reports that make the process auditable.

## What TOST does

TOST can:

- analyze TMX files before import;
- estimate potentially importable translation units;
- detect common TMX issues, including:
  - missing source language;
  - missing target language;
  - empty source or target segments;
  - tag-only source or target segments;
  - XML parse errors or malformed translation units;
  - inline-tag mismatches;
  - noisy or punctuation-only segment pairs;
- split large TMX files safely by:
  - file size;
  - number of translation units;
- create optimized TMX copies while keeping the original files unchanged;
- remove selected problematic translation units;
- remove exact duplicate source-target pairs;
- normalize language codes, for example from `en` / `ru` to `en-US` / `ru-RU`;
- keep only the selected source-target language pair;
- strip inline tags when needed;
- compare two TMX files or two sets of TMX files;
- export problem/result groups to:
  - XLSX;
  - Raw XML TXT;
  - TMX;
- save, delete, and import custom optimization presets;
- use the interface in English or Russian;
- save interface state between launches;
- generate formatted XLSX reports for review and auditing.

TOST is intended for translators, localization engineers, and CAT tool users who need to prepare TMX files before importing them into tools such as Smartcat, memoQ, Phrase, Trados, and similar systems.

## Main features

### Split / Analyze

The Split / Analyze tab helps inspect TMX files before import and split large TMX files into smaller valid TMX parts.

It can:

- analyze selected TMX files;
- count total TU, potentially importable TU, problem TU, and detected issues;
- show problem TU details;
- export analysis reports to XLSX;
- split TMX files by file size or by TU count;
- optionally analyze before splitting;
- optionally run a post-check after splitting.

### Optimize TMX

The Optimize TMX tab creates cleaned TMX copies without modifying the original files.

It can remove or report:

- TU without source language;
- TU without target language;
- empty source or target segments;
- tag-only source or target segments;
- malformed TU or XML parse errors;
- exact duplicate source-target pairs;
- noisy segment pairs;
- one-character or punctuation-only pairs;
- inline-tag mismatches.

It also supports:

- optimization profiles;
- custom user presets;
- preset import from JSON;
- language code normalization;
- keeping only the selected source-target language pair;
- dry run mode.

### Compare TMX

The Compare TMX tab compares two TMX files or two sets of TMX files.

It can compare:

- total TU;
- potentially importable TU;
- problem TU;
- detected issues;
- language statistics;
- file differences between side A and side B.

Comparison results are exported to XLSX reports.

### Export result groups

TOST can export selected problem/result groups, including:

- Problem TUs;
- Removed TUs;
- Removed duplicates;
- Noisy warnings;
- Inline-tag warnings;
- Changed TUs.

Supported export formats:

- XLSX report;
- Raw XML TXT;
- TMX file.

### Help and settings

TOST includes built-in topic-based Help and a Settings / About window.

The application supports:

- English and Russian interface languages;
- default output folder;
- default split settings;
- default language settings;
- saved interface state;
- centered Help, Settings, and notification dialogs.

## Privacy

TOST works locally on your computer.

The application does not upload TMX files anywhere, does not connect to external services, and does not send your translation memories to any server.

Your TMX files remain on your machine. Output files and reports are created only in the output folder selected by the user.

Original TMX files are not modified. TOST creates new output files.

## Download

For Windows users, download the latest `.exe` file from the GitHub Releases page.

Current release asset:

```text
TOST_v5_0.exe
```

No installation is required. Run the executable directly.

Windows SmartScreen or antivirus software may warn you that the executable is from an unknown publisher. The executable is not digitally signed.

If you prefer, you can review the source code and build the application yourself.

## Build from source

Requirements:

- Windows;
- Python 3;
- PyInstaller.

Install build requirements:

```bat
py -m pip install -r requirements.txt
```

From the project folder, run:

```bat
py -m PyInstaller --onefile --windowed --name "TOST_v5_0" --icon "tost.ico" --add-data "tost.ico;." --add-data "help_icon.png;." --add-data "settings_icon.png;." "tost_tmx_optimization_splitting_tool_v5_0.py"
```

The executable will be created in:

```text
dist\TOST_v5_0.exe
```

Required resource files:

```text
tost.ico
help_icon.png
settings_icon.png
```

## Project files

Recommended repository files for the v5.0 release:

```text
README.md
CHANGELOG.md
LICENSE
requirements.txt
tost.ico
help_icon.png
settings_icon.png
tost_tmx_optimization_splitting_tool_v5_0.py
```

Build output folders such as `build/` and `dist/` should not normally be committed to the repository.

## Development note

I am not a professional software developer.

The initial code and later iterations of this utility were generated and refined with the help of ChatGPT, then manually tested on local TMX files. Please review the source code before using it in sensitive workflows.

## License

This project is released under the MIT License.

See the `LICENSE` file for details.
