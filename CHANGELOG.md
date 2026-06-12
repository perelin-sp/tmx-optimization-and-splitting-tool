## What's new in TOST v5.0

This release includes all changes made since the last published version, **v4.5.7**.

### Major changes since v4.5.7

* Added **English/Russian interface localization**:

  * added an interface language selector;
  * added Russian translations for the main UI;
  * translated Help, Settings / About, tooltips, validation messages, warnings, and most user-facing dialogs;
  * improved consistency of function names across buttons, descriptions, and Help.

* Improved **Settings / About**:

  * replaced the text button with a settings icon;
  * added interface language selection;
  * added persistent default settings;
  * improved layout in English and Russian;
  * centered the Settings / About window relative to the main application window;
  * removed unnecessary empty space and adjusted button alignment.

* Added **saved UI state**:

  * TOST now remembers the last selected tab;
  * remembers the last selected export format;
  * restores the previous window size;
  * saves the current UI state when the application is closed;
  * intentionally does not restore previously selected TMX input files, so users explicitly choose current files for each session.

* Improved **Help**:

  * expanded Russian and English Help content;
  * improved topic-based Help navigation;
  * translated remaining mixed-language Help descriptions;
  * centered the Help window relative to the main application window.

* Improved **XLSX reports**:

  * added styled report headers;
  * added frozen header rows;
  * added auto-filters;
  * added automatic column width calculation;
  * added wrapped text in cells;
  * added cell borders;
  * added visual highlighting for different report types:

    * warnings;
    * removed TUs;
    * duplicates;
    * changed TUs;
    * summaries.

* Improved **application dialogs and notifications**:

  * translated additional validation and error messages;
  * translated messages shown when no result groups are available;
  * centered Help, Settings / About, and custom notification dialogs relative to the main application window;
  * replaced standard message boxes with centered TOST modal dialogs for more predictable placement.

* Improved **optimization result viewers**:

  * translated empty-result messages;
  * translated viewer titles and details labels;
  * improved consistency for Removed TUs, Removed duplicates, Noisy warnings, Inline-tag warnings, and Changed TUs.

* Improved **Compare TMX** localization and validation:

  * translated TMX selection validation messages;
  * translated file selection dialogs;
  * improved messages for missing or invalid TMX A / TMX B input.

* Improved **preset handling messages**:

  * translated preset save, overwrite, delete, and import messages;
  * translated JSON import dialogs and results;
  * improved consistency between built-in profiles and user presets.

* Improved **resource and build consistency**:

  * confirmed the current application icon is `tost.ico`;

  * confirmed toolbar resources are:

    * `help_icon.png`;
    * `settings_icon.png`;

  * removed old resource references from the active code path;

  * updated the PyInstaller build command for the v5.0 source file and executable name.

### Current release asset

`TOST_v5_0.exe`

### Current source file

`tost_tmx_optimization_splitting_tool_v5_0.py`

### Build command

```bat
py -m PyInstaller --onefile --windowed --name "TOST_v5_0" --icon "tost.ico" --add-data "tost.ico;." --add-data "help_icon.png;." --add-data "settings_icon.png;." "tost_tmx_optimization_splitting_tool_v5_0.py"
```

### Notes

Original TMX files are still treated as read-only input and are never modified.

TOST continues to create new output files and XLSX reports in the selected output folder.

## What's new in TOST v4.5.7

This release includes all changes made since the last published repository version, **v4.0.1**.

* Added **Compare TMX** mode:

  * compare one TMX file with another TMX file;
  * compare two sets of TMX files;
  * generate XLSX comparison reports;
  * compare total TU, potentially importable TU, problem TU, detected issues, language statistics, and file differences.

* Added export of problem and optimization result groups:

  * export Problem TUs;
  * export Removed TUs;
  * export Removed duplicates;
  * export Noisy warnings;
  * export Inline-tag warnings;
  * export Changed TUs;
  * export to XLSX, Raw XML TXT, or TMX.

* Improved noisy segment handling:

  * added noisy list match mode;
  * added “both source and target” vs “either source or target” logic;
  * added short-text warnings based on user-defined character length;
  * added noisy rule details to optimization reports.

* Added user optimization presets:

  * save current optimization settings as a custom preset;
  * delete user presets;
  * import presets from JSON;
  * keep built-in profiles protected from deletion or overwrite.

* Added built-in Help:

  * added a Help button;
  * added topic-based Help navigation;
  * expanded Help to cover all major functions and workflows.

* Improved toolbar UI:

  * replaced the text Help button with an icon button;
  * replaced the Settings / About text button with an icon button;
  * aligned Help and Settings / About buttons to the same visual size;
  * changed toolbar button order so Settings / About appears before Help.

* Updated application resources:

  * renamed the main application icon resource to `tost.ico`;
  * updated toolbar icon resource names:

    * `help_icon.png`;
    * `settings_icon.png`.

* Updated build resources and PyInstaller command:

  * main icon: `tost.ico`;
  * Help icon: `help_icon.png`;
  * Settings / About icon: `settings_icon.png`.