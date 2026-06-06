# TMX Optimization and Splitting Tool

**TMX Optimization and Splitting Tool**, or **TOST**, is a desktop utility for preparing TMX translation memory files for safer import into CAT tools.

TOST focuses on a conservative workflow: analyze TMX files, split large files safely, optionally create optimized copies, compare TMX versions, and generate reports that make the process auditable.

## What TOST does

TOST can:

* analyze TMX files before import;
* estimate potentially importable translation units;
* detect common TMX issues, including:

  * missing source language;
  * missing target language;
  * empty source or target segments;
  * tag-only source or target segments;
  * XML parse errors or malformed translation units;
  * inline-tag mismatches;
  * noisy or punctuation-only segment pairs;
* split large TMX files safely by:

  * file size;
  * number of translation units;
* create optimized TMX copies while keeping the original files unchanged;
* remove selected problematic translation units;
* remove exact duplicate source-target pairs;
* normalize language codes, for example from `en` / `ru` to `en-US` / `ru-RU`;
* keep only the selected source-target language pair;
* strip inline tags when needed;
* compare two TMX files or two sets of TMX files;
* export problem/result groups to:

  * XLSX;
  * Raw XML TXT;
  * TMX;
* save, delete, and import custom optimization presets;
* generate XLSX reports for review and auditing.

TOST is intended for translators, localization engineers, and CAT tool users who need to prepare TMX files before importing them into tools such as Smartcat, memoQ, Phrase, Trados, and similar systems.

## Privacy

TOST works locally on your computer.

The application does not upload TMX files anywhere, does not connect to external services, and does not send your translation memories to any server.

Your TMX files remain on your machine. Output files and reports are created only in the output folder selected by the user.

Original TMX files are not modified. TOST creates new output files.

## Download

For Windows users, download the latest `.exe` file from the GitHub Releases page.

Current release asset:

`TOST_v4_5_7.exe`

No installation is required. Run the executable directly.

Windows SmartScreen or antivirus software may warn you that the executable is from an unknown publisher. The executable is not digitally signed.

If you prefer, you can review the source code and build the application yourself.

## Build from source

Requirements:

* Windows
* Python 3
* PyInstaller

From the project folder, run:

```bat
py -m PyInstaller --onefile --windowed --name "TOST_v4_5_7" --icon "tost.ico" --add-data "tost.ico;." --add-data "help_icon.png;." --add-data "settings_icon.png;." "tost_tmx_optimization_splitting_tool_v4_5_7.py"
```

The executable will be created in:

```text
dist\TOST_v4_5_7.exe
```

Required resource files:

```text
tost.ico
help_icon.png
settings_icon.png
```

## Development note

I am not a professional software developer.

The initial code and later iterations of this utility were generated and refined with the help of ChatGPT, then manually tested on local TMX files. Please review the source code before using it in sensitive workflows.

## License

This project is released under the MIT License.

See the `LICENSE` file for details.
