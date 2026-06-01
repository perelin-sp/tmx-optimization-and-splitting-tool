# TMX Optimization and Splitting Tool

**TMX Optimization and Splitting Tool**, short name **TOST**, is a local Windows utility for analyzing, safely splitting, and preparing TMX translation memory files for import into CAT tools.

## What TOST does

TOST helps prepare TMX files for CAT import workflows.

Main features:

* Analyze TMX files
* Safely split TMX files by file size or by TU count
* Check source and target language segments
* Detect missing, empty and tag-only translation units
* Detect duplicate source-target pairs
* Detect short or noisy segment pairs
* Report inline-tag mismatches
* Optionally strip inline tags when needed
* Keep only a selected source-target language pair
* Normalize language codes, for example `en` to `en-US` and `ru` to `ru-RU`
* Run optimization in dry run mode
* Generate XLSX reports
* Generate batch summary reports for multiple files

## Privacy

TOST works locally.

TMX files are processed on your computer and are not uploaded anywhere by the application.

## Download

Download the latest Windows build from GitHub Releases:

```text
https://github.com/YOUR_GITHUB_USERNAME/tmx-optimization-and-splitting-tool/releases/latest
```

## Build from source

Install requirements:

```powershell
py -m pip install -r requirements.txt
```

Build the Windows executable:

```powershell
py -m PyInstaller --onefile --windowed --name "TOST_v4_0_1" --icon "tmx_splitter.ico" --add-data "tmx_splitter.ico;." "tost_tmx_optimization_splitting_tool_v4_0_1.py"
```

The generated executable will be available in:

```text
dist\TOST_v4_0_1.exe
```

## Development note

I am not a professional software developer.

The initial code and later iterations of this utility were generated and refined with the help of ChatGPT, then manually tested on local TMX files. Please review the source code before using it in sensitive workflows.

## Support

TOST is free.

If the app was useful to you, you can voluntarily support its development:

* Ko-fi: https://ko-fi.com/YOUR_KOFI_NAME
* Liberapay: https://liberapay.com/YOUR_LIBERAPAY_NAME
* Boosty: https://boosty.to/YOUR_BOOSTY_NAME

Support is not a license purchase, does not unlock additional features, and does not affect access to the app.

## License

This project is released under the MIT License.
