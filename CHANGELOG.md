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