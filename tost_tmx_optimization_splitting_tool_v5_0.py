import json
import zipfile
from xml.sax.saxutils import escape
import os
import sys
import queue
import re
import threading
import time
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from xml.etree import ElementTree as ET

APP_TITLE = "TMX Optimization and Splitting Tool v5.0"
APP_SHORT_NAME = "TOST"
DEFAULT_MAX_MB = "250"
DEFAULT_PART_TU_COUNT = "50000"
DEFAULT_PREFIX = "part"
DEFAULT_SOURCE_LANGS = "en,en-us,en-gb"
DEFAULT_TARGET_LANGS = "ru,ru-ru"
DEFAULT_NORMALIZE_SOURCE_LANG = "en-US"
DEFAULT_NORMALIZE_TARGET_LANG = "ru-RU"


# UI localization. English remains the internal/base language; Russian is applied at UI creation time.
# Technical terms such as TMX, TU, TUV, CAT, XML, XLSX, source/target, xml:lang are intentionally kept where useful.
UI_TRANSLATIONS_RU = {
    "TMX files": "Файлы TMX",
    "Add TMX files...": "Добавить TMX...",
    "Remove selected": "Удалить выбранные",
    "Clear": "Очистить",
    "Settings / About": "Настройки / О программе",
    "Help": "Справка",
    "Split / Analyze": "Разделение / Анализ",
    "Optimize TMX": "Оптимизация TMX",
    "Compare TMX": "Сравнение TMX",
    "Output": "Вывод",
    "Output folder:": "Папка вывода:",
    "Browse...": "Обзор...",
    "Language pair / language variants": "Языковая пара / варианты кодов языков",
    "Source langs:": "Языки оригинала:",
    "Target langs:": "Языки перевода:",
    "Use comma-separated variants, for example: en,en-us,en-gb and ru,ru-ru.": "Укажите варианты через запятую, например: en,en-us,en-gb и ru,ru-ru.",
    "Safe split settings": "Настройки безопасного разделения",
    "Split mode:": "Режим разделения:",
    "By file size, MB": "По размеру файла, MB",
    "By TU count": "По количеству TU",
    "Prefix:": "Префикс:",
    "Analyze TMX before splitting and create XLSX report": "Анализировать TMX перед разделением и создавать XLSX-отчет",
    "Post-check created files after splitting": "Проверять созданные файлы после разделения",
    "TU count mode counts written <tu> blocks only. Safe split still preserves TU content.": "Режим TU считает только записанные блоки <tu>. Safe Split сохраняет содержимое TU.",
    "Analyze": "Анализ",
    "Safe Split": "Safe Split",
    "Cancel": "Отмена",
    "Open output folder": "Открыть папку вывода",
    "Open report": "Открыть отчет",
    "View problem TUs": "Проблемные TU",
    "Export problem TUs": "Экспорт проблемных TU",
    "Profile and language pair": "Профиль и языковая пара",
    "Optimization profile:": "Профиль оптимизации:",
    "Apply profile": "Применить профиль",
    "Save as preset": "Сохранить пресет",
    "Delete preset": "Удалить пресет",
    "Import presets": "Импорт пресетов",
    "Keep only selected source-target language pair": "Оставить только выбранную пару оригинал-перевод",
    "Normalize source language code to:": "Нормализовать код языка оригинала в:",
    "Normalize target language code to:": "Нормализовать код языка перевода в:",
    "Basic cleanup options": "Базовая очистка",
    "Remove TU without source language": "Удалять TU без языка оригинала",
    "Remove TU without target language": "Удалять TU без языка перевода",
    "Remove TU with empty source or target segment": "Удалять TU с пустым сегментом оригинала или перевода",
    "Remove TU with tag-only source or target segment": "Удалять TU, где оригинал или перевод состоит только из тегов",
    "Remove TU with XML parse errors / malformed TU": "Удалять TU с ошибками XML / поврежденной структурой",
    "Duplicates and short/noisy segments": "Дубли и короткие/мусорные сегменты",
    "Remove exact duplicate source-target pairs; keep the first occurrence": "Удалять точные дубли пар оригинал-перевод; оставлять первое вхождение",
    "Warn about short/noisy source-target pairs": "Предупреждать о коротких/мусорных парах оригинал-перевод",
    "Remove pairs matching the noisy segment list": "Удалять пары, совпадающие со списком мусорных сегментов",
    "Remove one-character or punctuation-only pairs": "Удалять односимвольные пары и пары только из пунктуации",
    "Noisy segment list:": "Список мусорных сегментов:",
    "List match:": "Совпадение со списком:",
    "Warn if both texts are <=": "Предупреждать, если оба текста <=",
    "chars": "симв.",
    "Both source and target": "Оба: оригинал и перевод",
    "Either source or target": "Любой: оригинал или перевод",
    "Inline tags": "Inline-теги",
    "Report inline-tag mismatch between source and target": "Сообщать о расхождении inline-тегов между оригиналом и переводом",
    "Strip inline tags only from mismatched TUs": "Удалять inline-теги только из TU с расхождением тегов",
    "Strip inline tags from all kept TUs": "Удалять inline-теги из всех сохраненных TU",
    "Dry run (report only)": "Dry run (только отчет)",
    "Open optimized TMX": "Открыть оптимизированный TMX",
    "View removed TUs": "Удаленные TU",
    "View duplicates": "Дубли",
    "View noisy warnings": "Предупреждения о мусорных сегментах",
    "View inline-tag warnings": "Предупреждения по inline-тегам",
    "View changed TUs": "Измененные TU",
    "Export result groups": "Экспорт групп результатов",
    "Compare two TMX files or two sets of TMX files using the current Source langs and Target langs settings. This is useful for comparing an original TMX with an optimized TMX, or outputs from different tools.": "Сравните два TMX-файла или два набора TMX с текущими настройками языков оригинала и перевода. Это удобно для сравнения исходной и оптимизированной базы или результатов разных инструментов.",
    "TMX A:": "TMX A:",
    "TMX B:": "TMX B:",
    "No TMX files selected": "Файлы TMX не выбраны",
    "Select TMX A...": "Выбрать TMX A...",
    "Select TMX B...": "Выбрать TMX B...",
    "Clear A": "Очистить A",
    "Clear B": "Очистить B",
    "If one file is selected on each side, they are compared directly. If multiple files are selected, matching is done by file name.": "Если с каждой стороны выбран один файл, они сравниваются напрямую. Если выбрано несколько файлов, сопоставление выполняется по имени файла.",
    "Overall: idle": "Overall: ожидание",
    "Result summary": "Сводка результата",
    "Log": "Лог",
    "Default settings": "Настройки по умолчанию",
    "Default output folder:": "Папка вывода по умолчанию:",
    "Default part size, MB:": "Размер части по умолчанию, MB:",
    "Default part TU count:": "Количество TU в части по умолчанию:",
    "Default split mode:": "Режим разделения по умолчанию:",
    "By MB": "По MB",
    "Default prefix:": "Префикс по умолчанию:",
    "Default source langs:": "Языки оригинала по умолчанию:",
    "Default target langs:": "Языки перевода по умолчанию:",
    "Analyze TMX before splitting by default": "Анализировать TMX перед разделением по умолчанию",
    "Post-check created files after splitting by default": "Проверять созданные файлы после разделения по умолчанию",
    "Save": "Сохранить",
    "Apply": "Применить",
    "Reset": "Сбросить",
    "Open settings folder": "Открыть папку настроек",
    "Close": "Закрыть",
    "About": "О программе",
    "Function": "Функция",
    "Description": "Описание",
    "Interface language:": "Язык интерфейса:",
    "English": "English",
    "Russian": "Русский",
    "Note: Restart TOST to apply language settings": "Примечание: настройки языка будут применены после перезапуска TOST",
    "XLSX report": "XLSX-отчет",
    "Raw XML TXT": "Raw XML TXT",
    "TMX file": "TMX-файл",
    "Export": "Экспорт",
    "Select at least one result group to export.": "Выберите хотя бы одну группу результатов для экспорта.",
}

UI_TRANSLATIONS_RU.update({
    "Safe split preserves original TU content and splits only on <tu> boundaries. Original TMX files are never modified.": "Безопасное разделение сохраняет исходное содержимое TU и разделяет файл только по границам <tu>. Исходные TMX-файлы никогда не изменяются.",
    "Safe Split": "Безопасное разделение",
    "View noisy warnings": "Предупреждения о мусорных сегментах",
    "View inline-tag warnings": "Предупреждения по inline-тегам",
    "Both source and target": "Оба: оригинал и перевод",
    "Either source or target": "Любой: оригинал или перевод",
    "Overall: idle": "Общий прогресс: ожидание",
    "Overall: done": "Общий прогресс: завершено",
    "Overall: error": "Общий прогресс: ошибка",
    "Overall": "Общий прогресс",
    "Result summary: no analysis or optimization has been run yet.": "Сводка результата: анализ или оптимизация еще не запускались.",
    "Result summary: comparing TMX files...": "Сводка результата: сравнение TMX-файлов...",
    "General CAT-safe": "Общий CAT-safe",
    "Strict import": "Строгий импорт",
    "Smartcat-oriented": "Ориентированный на Smartcat",
    "Custom": "Пользовательский",
    "Noisy warnings": "Предупреждения о мусорных сегментах",
    "Inline-tag warnings": "Предупреждения по inline-тегам",
    "Select TMX...": "Выбрать TMX...",
    "Select TMX files": "Выбрать TMX-файлы",
    "Compare options": "Параметры сравнения",
    "Compare two TMX files or two sets of TMX files using the current Source langs and Target langs settings. This is useful for comparing an original TMX with an optimized TMX, two exports, or two versions of the same base.": "Сравните два TMX-файла или два набора TMX с текущими настройками языков оригинала и перевода. Это удобно для сравнения исходной и оптимизированной базы, двух экспортов или двух версий одной базы.",
    "If one TMX is selected on each side, files are compared directly even if their file names differ. If multiple TMX files are selected, matching uses file name.": "Если с каждой стороны выбран один TMX, файлы сравниваются напрямую, даже если имена отличаются. Если выбрано несколько TMX-файлов, сопоставление выполняется по имени файла.",
    "No analysis or optimization has been run yet.": "Анализ или оптимизация еще не запускались.",
    "Select result groups and output format.": "Выберите группы результатов и формат выгрузки.",
    "Groups": "Группы",
    "Format:": "Формат:",
    "Cancel": "Отмена",
    "Problem TUs from the latest analysis. Select a row to view the original TU XML.": "Проблемные TU из последнего анализа. Выберите строку, чтобы посмотреть исходный XML блока TU.",
    "Original TU XML": "Исходный XML блока TU",
    "Details / raw XML": "Детали / raw XML",
    "Settings reset to defaults. Click Apply to persist them.": "Настройки сброшены к значениям по умолчанию. Нажмите «Применить», чтобы сохранить их.",
})


UI_TRANSLATIONS_RU.update({
    "Save settings": "Сохранить",
    "Reset settings": "Сбросить",
    "Settings reset to defaults. Click Save settings to persist them.": "Настройки сброшены к значениям по умолчанию. Нажмите «Применить», чтобы сохранить их.",
})

# Additional localization consistency fixes added in v4.6.6.
UI_TRANSLATIONS_RU.update({
    "No TMX files selected": "Файлы TMX не выбраны",
    "Safe Split": "Безопасное разделение",
    "General CAT-safe": "Общий CAT-safe",
    "Strict import": "Строгий импорт",
    "Smartcat-oriented": "Ориентированный на Smartcat",
    "Custom": "Пользовательский",
    "Noisy warnings": "Предупреждения о мусорных сегментах",
    "View noisy warnings": "Предупреждения о мусорных сегментах",
    "Inline-tag warnings": "Предупреждения по inline-тегам",
    "View inline-tag warnings": "Предупреждения по inline-тегам",
    "Both source and target": "Оба: оригинал и перевод",
    "Either source or target": "Любой: оригинал или перевод",
})


# Additional messagebox and validation localization added in v4.8.2.
UI_TRANSLATIONS_RU.update({
    "Preset name:": "Имя пресета:",
    "Preset name cannot be empty.": "Имя пресета не может быть пустым.",
    "Built-in profile names cannot be overwritten. Choose another name.": "Имена встроенных профилей нельзя перезаписывать. Выберите другое имя.",
    "Preset already exists:": "Пресет уже существует:",
    "Overwrite it?": "Перезаписать?",
    "Only user presets can be deleted. Built-in profiles are always available.": "Удалять можно только пользовательские пресеты. Встроенные профили всегда доступны.",
    "Delete user preset?": "Удалить пользовательский пресет?",
    "Import optimization presets": "Импорт пресетов оптимизации",
    "JSON files": "Файлы JSON",
    "All files": "Все файлы",
    "No valid user presets were found in the selected file.": "В выбранном файле не найдено корректных пользовательских пресетов.",
    "Some presets already exist.": "Некоторые пресеты уже существуют.",
    "Yes - overwrite existing presets.": "Да - перезаписать существующие пресеты.",
    "No - import only new presets.": "Нет - импортировать только новые пресеты.",
    "Cancel - do not import.": "Отмена - не импортировать.",
    "Preset import completed.": "Импорт пресетов завершен.",
    "Added:": "Добавлено:",
    "Overwritten:": "Перезаписано:",
    "Skipped:": "Пропущено:",
    "Could not import presets:": "Не удалось импортировать пресеты:",
    "Could not open output folder:": "Не удалось открыть папку вывода:",
    "Could not open settings folder:": "Не удалось открыть папку настроек:",
    "No problem TUs are available. Run Analyze first.": "Проблемные TU недоступны. Сначала запустите анализ.",
    "No result groups are available yet. Run Analyze or Optimize TMX first.": "Группы результатов пока недоступны. Сначала запустите анализ или оптимизацию TMX.",
    "Selected groups do not contain raw TU XML blocks that can be exported as TMX.": "Выбранные группы не содержат исходных XML-блоков TU, которые можно экспортировать как TMX.",
    "Export completed:": "Экспорт завершен:",
    "Export failed:": "Ошибка экспорта:",
    "TMX A is not selected or does not contain valid TMX files.": "TMX A не выбран или не содержит корректных TMX-файлов.",
    "TMX B is not selected or does not contain valid TMX files.": "TMX B не выбран или не содержит корректных TMX-файлов.",
    "Source langs and target langs cannot be empty.": "Поля языков оригинала и перевода не могут быть пустыми.",
    "Source and target language lists overlap:": "Списки языков оригинала и перевода пересекаются:",
    "Continue anyway?": "Все равно продолжить?",
    "Output folder cannot be empty.": "Папка вывода не может быть пустой.",
    "Output folder is not writable:": "Нет прав на запись в папку вывода:",
    "The selected optimization settings may change or remove TMX content:": "Выбранные настройки оптимизации могут изменить или удалить содержимое TMX:",
    "Original TMX files are never modified. Continue?": "Исходные TMX-файлы никогда не изменяются. Продолжить?",
    "Dry run is enabled: TOST will create an XLSX report only and will not leave an optimized TMX file.": "Включен тестовый запуск: TOST создаст только XLSX-отчет и не создаст оптимизированный TMX-файл.",
    "Remove exact duplicates keeps only the first source-target pair and removes later duplicates.": "Удаление точных дублей оставляет только первое вхождение пары оригинал-перевод и удаляет последующие дубли.",
    "Remove pairs matching the noisy segment list may delete valid short UI strings if the list is too broad.": "Удаление пар из списка мусорных сегментов может удалить корректные короткие UI-строки, если список слишком широкий.",
    "Remove one-character or punctuation-only pairs can delete legitimate UI labels such as symbols or numbered options.": "Удаление односимвольных пар или пар только из пунктуации может удалить корректные UI-метки, например символы или нумерованные варианты.",
    "Strip inline tags only from mismatched TUs changes segment content in affected TU blocks.": "Удаление inline-тегов только из TU с расхождением тегов изменяет содержимое сегментов в затронутых TU.",
    "Strip inline tags from all kept TUs changes segment content across the optimized TMX.": "Удаление inline-тегов из всех сохраненных TU изменяет содержимое сегментов во всем оптимизированном TMX.",
    "Language normalization rewrites xml:lang values in the optimized TMX.": "Нормализация языковых кодов переписывает значения xml:lang в оптимизированном TMX.",
    "Keep only selected source-target language pair removes other languages from multilingual TU blocks.": "Опция оставления только выбранной пары оригинал-перевод удаляет другие языки из многоязычных блоков TU.",
    "Remove XML parse errors / malformed TU is aggressive; malformed blocks will be excluded from the optimized TMX.": "Удаление TU с ошибками XML / поврежденной структурой является агрессивной очисткой; поврежденные блоки будут исключены из оптимизированного TMX.",
    "Please add at least one TMX file.": "Добавьте хотя бы один TMX-файл.",
    "Part size must be a positive number.": "Размер части должен быть положительным числом.",
    "Part TU count must be a positive integer.": "Количество TU в части должно быть положительным целым числом.",
    "Noisy segment list is empty, but noisy segment removal is enabled.": "Список мусорных сегментов пуст, но включено удаление мусорных сегментов.",
    "Minimum text length must be a positive integer.": "Минимальная длина текста должна быть положительным целым числом.",
    "Invalid source language code for normalization:": "Некорректный код языка оригинала для нормализации:",
    "Invalid target language code for normalization:": "Некорректный код языка перевода для нормализации:",
    "Select TMX file(s) for side A": "Выберите TMX-файл(ы) для стороны A",
    "Select TMX file(s) for side B": "Выберите TMX-файл(ы) для стороны B",
    "No {label} has been created yet.": "Файл {label} еще не создан.",
    "Could not open {label}:": "Не удалось открыть {label}:",
    "TMX files": "Файлы TMX",
    "All files": "Все файлы",
})

HELP_TOPICS_RU = {
    "Overview": ("Обзор", """TMX Optimization and Splitting Tool подготавливает TMX-памяти переводов к безопасному импорту в CAT-системы.

Основные разделы:
- Разделение / Анализ: проверка TMX и безопасное разделение больших баз.
- Оптимизация TMX: создание очищенных копий TMX по выбранным правилам.
- Сравнение TMX: сравнение двух TMX-файлов или двух наборов файлов.
- Экспорт проблемных групп: выгрузка выбранных диагностических групп для проверки или теста.
- Настройки / О программе: настройки по умолчанию, пути вывода и информация о программе.

Исходные TMX-файлы никогда не изменяются. Новые TMX-файлы и XLSX-отчеты создаются в выбранной папке вывода."""),
    "Safety principle": ("Принцип безопасности", """Исходные TMX-файлы используются только для чтения.

Безопасное разделение по возможности сохраняет исходное содержимое TU и разделяет файл только по границам <tu>.

Оптимизация TMX создает новые очищенные файлы в папке вывода. Потенциально рискованные действия, такие как удаление дублей, удаление мусорных пар, нормализация языковых кодов или удаление inline-тегов, показывают предупреждение перед запуском.

Тестовый запуск позволяет заранее посмотреть результат оптимизации без создания оптимизированного TMX."""),
    "Input files": ("Входные файлы", """Используйте кнопку Добавить TMX-файлы, чтобы выбрать один или несколько TMX-файлов.

Удалить выбранные удаляет выделенные файлы из списка. Очистить очищает весь список.

Большинство операций поддерживает несколько файлов. Для пакетной обработки TOST может создавать сводные пакетные отчеты."""),
    "Output folder": ("Папка вывода", """Папка вывода - это папка, куда TOST сохраняет разделенные файлы, оптимизированные TMX, экспортированные группы и XLSX-отчеты.

Исходные TMX-файлы остаются без изменений.

Открыть папку вывода открывает выбранную папку вывода в файловом менеджере операционной системы."""),
    "Source and target languages": ("Языки оригинала и перевода", """Языки оригинала и Языки перевода определяют, какие языковые коды считать исходным и целевым языком.

Указывайте варианты через запятую. Например:
Языки оригинала: en,en-us,en-gb
Языки перевода: ru,ru-ru

Это полезно, если TMX содержит смешанные варианты кодов: en, en-US, en-GB, ru, ru-RU."""),
    "Safe Split": ("Безопасное разделение", """Безопасное разделение делит TMX на меньшие валидные TMX-файлы.

Можно делить по размеру файла или по количеству TU. Этот режим не переписывает текст сегментов, не удаляет теги и не нормализует языковые коды.

Безопасное разделение предназначено для случаев, когда нужно максимально сохранить исходное содержимое TU."""),
    "Split by file size": ("Разделение по размеру", """Разделение по размеру создает части, близкие к заданному размеру в MB.

TOST записывает только целые блоки <tu> и не разрезает translation unit посередине.

Один очень большой TU может сделать часть больше заданного лимита."""),
    "Split by TU count": ("Разделение по количеству TU", """Разделение по количеству TU создает новую часть после указанного количества записанных блоков <tu>.

Это полезно, если CAT-система чувствительна к количеству translation units, а не к размеру файла.

В этом режиме считаются только записанные TU."""),
    "Analyze": ("Анализ", """Анализ проверяет выбранные TMX-файлы и создает XLSX-отчеты.

Он показывает:
- общее количество TU;
- потенциально импортируемые TU;
- проблемные TU;
- общее количество найденных проблем;
- статистику ошибок;
- статистику языков;
- детали проблемных TU с исходным XML.

Запускайте Анализ перед оптимизацией, чтобы понять структуру базы."""),
    "Analyze before split": ("Анализ перед разделением", """Анализ перед разделением запускает анализ перед Безопасным разделением и создает XLSX-отчет.

Это помогает увидеть, есть ли во входной базе отсутствующие языки, пустые сегменты, сегменты только с тегами, ошибки XML или смешанные языковые коды."""),
    "Post-check after split": ("Проверка после разделения", """Проверка после разделения анализирует созданные части после Безопасного разделения.

Она подтверждает количество созданных файлов и считает всего TU, потенциально импортируемые TU, проблемные TU и найденные проблемы в выходных частях.

Создается отдельный XLSX-отчет."""),
    "Potentially importable TU": ("Потенциально импортируемые TU", """Потенциально импортируемые TU - это количество TU, где есть выбранные языки оригинала и перевода и нет найденных блокирующих проблем.

Это оценка. Конкретная CAT-система все равно может отклонить часть TU по своим внутренним причинам."""),
    "Problem TU and detected issues": ("Проблемные TU и найденные проблемы", """Проблемные TU - это количество TU, где есть хотя бы одна найденная проблема.

Всего найденных проблем может быть больше, чем проблемных TU, потому что в одном TU может быть несколько проблем.

Например, один TU может иметь и оригинал только с тегами, и перевод только с тегами."""),
    "Language statistics": ("Статистика языков", """Статистика языков показывает, какие значения xml:lang есть в TMX.

Отчет включает количество TUV, количество TU, непустые сегменты, пустые сегменты и сегменты только с тегами для каждого языкового кода.

Это помогает выявить смешанные варианты вроде en, en-US, en-GB, ru, ru-RU."""),
    "View problem TUs": ("Просмотр проблемных TU", """Просмотр проблемных TU открывает таблицу проблемных TU из последнего анализа.

При выборе строки TOST показывает исходный XML блока TU под таблицей.

Это позволяет проверить проблемные TU без ручного открытия исходного TMX."""),
    "Open report": ("Открыть отчет", """Открыть отчет открывает последний релевантный XLSX-отчет, созданный анализом, оптимизацией, сравнением TMX, экспортом или проверкой после разделения.

Если отчет еще не создан, сначала запустите соответствующую операцию."""),
    "Open optimized TMX": ("Открыть оптимизированный TMX", """Открыть оптимизированный TMX открывает последний оптимизированный TMX-файл, созданный Оптимизацией TMX.

Для Тестового запуска эта кнопка неприменима, потому что Тестовый запуск создает только отчет и не создает оптимизированный TMX."""),
    "Optimize TMX": ("Оптимизация TMX", """Оптимизация TMX создает очищенную копию выбранных TMX-файлов.

В зависимости от настроек она может удалять TU с отсутствующими языками, пустыми сегментами, сегментами только с тегами, дублями, мусорными парами, односимвольными парами, парами только из пунктуации и поврежденные TU.

Также можно нормализовать языковые коды, оставить только выбранную языковую пару, проверить расхождение inline-тегов и удалить inline-теги при необходимости."""),
    "Basic cleanup options": ("Базовая очистка", """Базовая очистка удаляет TU, которые с высокой вероятностью вызывают проблемы импорта.

Доступные опции:
- удалить TU без языка оригинала;
- удалить TU без языка перевода;
- удалить TU с пустым сегментом оригинала или перевода;
- удалить TU с сегментом оригинала или перевода только с тегами;
- удалить TU с ошибками XML или поврежденной структурой.

Удаленные блоки TU фиксируются в отчете оптимизации."""),
    "Tag-only TU": ("TU только с тегами", """Сегмент только с тегами содержит inline-теги, но не содержит реального текста.

Пример: <seg><ph x=\"1\"/></seg>

Такие TU обычно бесполезны для памяти переводов и могут быть удалены через Оптимизацию TMX."""),
    "Duplicate removal": ("Удаление дублей", """Удаление точных дублей пар оригинал-перевод оставляет первое вхождение и удаляет последующие точные дубли такой пары.

Поиск дублей основан на выбранной паре сегментов оригинала и перевода.

Удаленные дубли записываются на лист Удаленные дубли и могут быть просмотрены или экспортированы."""),
    "Noisy segment rules": ("Правила мусорных сегментов", """Правила мусорных сегментов находят короткие или технические пары, например записи только из пунктуации.

Доступны:
- пользовательский Список мусорных сегментов;
- режим совпадения со списком: оба сегмента, оригинал и перевод, или любой из них;
- предупреждения для пар, где оба текста короче заданного лимита;
- опциональное удаление пар из списка мусорных сегментов;
- опциональное удаление односимвольных пар и пар только из пунктуации.

Перед агрессивным удалением проверяйте отчеты: короткие UI-строки иногда бывают валидными переводами."""),
    "Inline tags": ("Inline-теги", """Inline-теги - это плейсхолдеры или маркеры форматирования внутри сегмента, например <ph>, <bpt>, <ept>, <it>, <ut>, <hi>, <sub>.

Они могут обозначать форматирование, переменные, ссылки, переносы строк и другие нетекстовые элементы."""),
    "Inline-tag mismatch": ("Расхождение inline-тегов", """Расхождение inline-тегов означает, что в оригинале и переводе разная последовательность inline-тегов.

По умолчанию TOST только сообщает о таких расхождениях и не удаляет TU.

Группа Предупреждения по inline-тегам содержит последовательности тегов, превью и исходный XML блока TU для проверки."""),
    "Strip inline tags": ("Удаление inline-тегов", """Удаление inline-тегов удаляет inline-теги из сохраненных TU.

Доступны варианты:
- удалить inline-теги только из TU с расхождением тегов;
- удалить inline-теги из всех сохраненных TU.

Это меняет содержимое сегментов. Используйте только если целевая CAT-система отвергает TU с тегами или если вам намеренно нужна текстовая память без тегов.

Измененные TU записываются в отчет с XML до и после."""),
    "Language normalization": ("Нормализация языковых кодов", """Нормализация языковых кодов переписывает значения xml:lang в оптимизированном файле.

Например, оригинал en и перевод ru могут быть записаны как en-US и ru-RU.

Текст сегментов не переводится и не изменяется. Меняется только атрибут языкового кода.

Коды задаются пользователем в полях Нормализовать код языка оригинала в и Нормализовать код языка перевода в."""),
    "Keep selected language pair": ("Оставить выбранную языковую пару", """Оставить только выбранную пару оригинал-перевод удаляет лишние языковые варианты из оптимизированного файла.

TOST находит TUV оригинала и перевода с помощью полей Языки оригинала и Языки перевода. Если эта опция включена, в выходном TU остаются только выбранные TUV оригинала и перевода.

Это полезно для подготовки чистой двуязычной TMX из многоязычной или смешанной по кодам TMX."""),
    "Optimization profiles": ("Профили оптимизации", """Профили оптимизации - это пресеты, которые выставляют параметры оптимизации.

Встроенные профили:
- Общий CAT-safe: осторожная очистка.
- Строгий импорт: более сильная очистка для строгих сценариев импорта.
- Ориентированный на Smartcat: использует строгие требования импорта, похожие на Smartcat, как практический ориентир; логика остается общей и может помогать с другими CAT-системами.
- Пользовательский: сохраняет текущие ручные настройки.

Применить профиль применяет выбранный профиль к текущим настройкам."""),
    "User presets": ("Пользовательские пресеты", """Пользовательские пресеты позволяют сохранять, удалять и импортировать собственные настройки оптимизации.

Сохранить пресет сохраняет текущие настройки оптимизации под пользовательским именем.
Удалить пресет удаляет пользовательский пресет.
Импорт пресетов импортирует пресеты из JSON-файлов.

Встроенные профили нельзя перезаписать или удалить. Импортированные пресеты сохраняются в tost_settings.json и появляются в том же меню профилей."""),
    "Dry run": ("Тестовый запуск", """Тестовый запуск создает только отчет и не создает оптимизированный TMX.

Используйте его перед агрессивной очисткой, чтобы посмотреть, что будет удалено или изменено.

Тестовый запуск полезен для проверки удаления дублей, удаления мусорных пар, нормализации языков, фильтрации выбранной языковой пары и удаления inline-тегов."""),
    "Result summary": ("Сводка результата", """Сводка результата показывает краткие метрики после анализа, Безопасного разделения или Оптимизации TMX.

Для оптимизации она показывает состояние до и после, количество удаленных TU, дублей, мусорных сегментов, односимвольных/пунктуационных удалений и измененных TU."""),
    "View optimization results": ("Просмотр результатов оптимизации", """После Оптимизации TMX TOST может показывать группы результатов прямо в программе.

Доступные окна просмотра:
- Удаленные TU;
- Дубли;
- Предупреждения о мусорных сегментах;
- Предупреждения по inline-тегам;
- Измененные TU.

При выборе строки ниже таблицы показывается исходный XML или подробная информация."""),
    "Compare TMX": ("Сравнение TMX", """Сравнение TMX сравнивает два TMX-файла или два набора TMX-файлов с использованием текущих настроек языков оригинала и перевода.

Если с каждой стороны выбран один файл, они сравниваются напрямую, даже если имена отличаются.

Если выбрано несколько файлов, TOST сопоставляет файлы по имени.

Отчет сравнения включает сводные метрики, метрики по файлам, совпавшие файлы, файлы только в A, файлы только в B и статистику языков для обеих сторон."""),
    "Export problem/result groups": ("Экспорт проблемных групп", """Экспортирует выбранные проблемные группы или группы результатов оптимизации в XLSX, TXT с исходным XML или TMX.

Группы включают:
- Проблемные TU;
- Удаленные TU;
- Удаленные дубли;
- Предупреждения о мусорных сегментах;
- Предупреждения по inline-тегам;
- Измененные TU.

Используйте Экспорт проблемных TU после Анализа. Используйте Экспорт групп результатов после Оптимизации TMX."""),
    "Export formats": ("Форматы экспорта", """XLSX-отчет создает таблицу со всеми доступными колонками.

TXT с исходным XML записывает исходные XML-блоки <tu> в текстовый файл для ручной проверки.

TMX-файл собирает выбранные блоки TU в валидный TMX-файл для тестирования или повторного импорта выбранных единиц."""),
    "Batch summary reports": ("Пакетные сводные отчеты", """При обработке нескольких файлов TOST может создавать пакетные сводные отчеты.

Пакетные отчеты суммируют результаты по всем обработанным файлам и также показывают метрики по каждому файлу.

Они полезны для больших памятей переводов, разделенных на много частей."""),
    "Reports": ("Отчеты", """TOST создает XLSX-отчеты для анализа, оптимизации, тестового запуска, проверки после разделения, сравнения, экспорта и пакетных операций.

Отчеты нужны, чтобы каждое удаление, предупреждение или изменение можно было проверить.

Типичные листы: Сводка, Статистика ошибок, Статистика языков, Проблемы, Удаленные TU, Удаленные дубли, Предупреждения о мусорных сегментах, Предупреждения по inline-тегам, Измененные TU, сводки по пакетам и файлам."""),
    "Settings / About": ("Настройки / О программе", """Настройки / О программе содержит папку вывода по умолчанию, настройки разделения по умолчанию, варианты языков по умолчанию, префикс по умолчанию и настройки анализа/проверки после разделения.

Сохранить записывает настройки в tost_settings.json.
Сбросить восстанавливает значения по умолчанию.
Открыть папку настроек открывает папку с файлом настроек.

TOST также восстанавливает последнюю выбранную вкладку, размер окна и формат экспорта после перезапуска. Список входных TMX-файлов намеренно не восстанавливается.

О программе объясняет базовый принцип безопасности и показывает версию приложения."""),
    "Safety checks and warnings": ("Проверки и предупреждения", """Перед запуском операций TOST проверяет обязательные входные данные и настройки.

Примеры:
- выбраны ли TMX-файлы;
- доступна ли папка вывода;
- корректен ли размер части или лимит TU;
- заполнены ли списки языков оригинала и перевода;
- не конфликтуют ли списки языков оригинала и перевода;
- корректны ли коды нормализации языков.

Рискованные действия оптимизации показывают предупреждение перед обработкой."""),
}

def _polish_ru_help_topics():
    replacements = {
        "Safe Split": "Безопасное разделение",
        "Optimize TMX": "Оптимизация TMX",
        "Analyze": "Анализ",
        "View problem TUs": "Проблемные TU",
        "Open report": "Открыть отчет",
        "Open optimized TMX": "Открыть оптимизированный TMX",
        "Basic cleanup options": "Базовая очистка",
        "Remove exact duplicate source-target pairs": "Удаление точных дублей пар source-target",
        "Removed duplicates": "Удаленные дубли",
        "Noisy warnings": "Предупреждения о мусорных сегментах",
        "Inline-tag warnings": "Предупреждения по inline-тегам",
        "View removed TUs": "Удаленные TU",
        "View duplicates": "Дубли",
        "View noisy warnings": "Предупреждения о мусорных сегментах",
        "View inline-tag warnings": "Предупреждения по inline-тегам",
        "View changed TUs": "Измененные TU",
        "Export problem TUs": "Экспорт проблемных TU",
        "Export result groups": "Экспорт групп результатов",
        "Compare TMX": "Сравнение TMX",
        "Settings / About": "Настройки / О программе",
        "Save": "Сохранить",
        "Reset": "Сбросить",
        "Open settings folder": "Открыть папку настроек",
        "Output folder": "Папка вывода",
        "Open output folder": "Открыть папку вывода",
        "Source langs": "Языки оригинала",
        "Target langs": "Языки перевода",
        "source-target": "оригинал-перевод",
        "source and target": "оригинал и перевод",
        "source or target": "оригинал или перевод",
        "source language": "язык оригинала",
        "target language": "язык перевода",
        "source segment": "сегмент оригинала",
        "target segment": "сегмент перевода",
        "source": "оригинал",
        "target": "перевод",
        "User presets": "Пользовательские пресеты",
        "Save as preset": "Сохранить пресет",
        "Delete preset": "Удалить пресет",
        "Import presets": "Импорт пресетов",
        "Optimization profiles": "Профили оптимизации",
        "Basic cleanup options": "Базовая очистка",
        "Remove exact duplicate оригинал-перевод pairs": "Удаление точных дублей пар оригинал-перевод",
        "Remove exact duplicate source-target pairs": "Удаление точных дублей пар оригинал-перевод",
        "Noisy segment list": "Список мусорных сегментов",
        "Both оригинал and перевод": "оба: оригинал и перевод",
        "Either оригинал or перевод": "любой: оригинал или перевод",
        "Both source and target": "оба: оригинал и перевод",
        "Either source or target": "любой: оригинал или перевод",
        "Language statistics": "Статистика языков",
        "Post-check created files after splitting": "Проверка созданных файлов после разделения",
        "Analyze TMX before splitting": "Анализ TMX перед разделением",
        "Dry run": "Dry run",
        "Result summary": "Сводка результата",
        "XLSX report": "XLSX-отчет",
        "TMX file": "TMX-файл",
        "Apply profile": "Применить профиль",
        "General CAT-safe": "Общий CAT-safe",
        "Strict import": "Строгий импорт",
        "Smartcat-oriented": "Ориентированный на Smartcat",
        "Custom": "Пользовательский",
        "Add TMX files": "Добавить TMX-файлы",
        "Remove selected": "Удалить выбранные",
        "Clear": "Очистить",
        "Split by file size": "Разделение по размеру",
        "Split by TU count": "Разделение по количеству TU",
        "translation unit": "translation unit",
        "translation units": "translation units",
        "total TU": "всего TU",
        "Total TU": "Всего TU",
        "potentially importable TU": "потенциально импортируемые TU",
        "Potentially importable TU": "Потенциально импортируемые TU",
        "problem TU": "проблемные TU",
        "Problem TU": "Проблемные TU",
        "detected issues": "найденные проблемы",
        "Total detected issues": "Всего найденных проблем",
        "Problem TUs": "Проблемные TU",
        "Removed TUs": "Удаленные TU",
        "Changed TUs": "Измененные TU",
        "raw XML": "исходный XML",
        "raw TU XML": "исходный XML блока TU",
        "Raw XML": "исходный XML",
        "Raw XML TXT": "TXT с исходным XML",
        "Summary": "Сводка",
        "Error counts": "Статистика ошибок",
        "Problems": "Проблемы",
        "Language statistics": "Статистика языков",
        "Removed duplicates": "Удаленные дубли",
        "Noisy warnings": "Предупреждения о мусорных сегментах",
        "Inline-tag warnings": "Предупреждения по inline-тегам",
        "batch/file summaries": "сводки по пакетам и файлам",
        "batch reports": "пакетные отчеты",
        "Batch reports": "Пакетные отчеты",
        "batch-отчеты": "пакетные отчеты",
        "batch reports": "пакетные отчеты",
        "batch": "пакетный",
        "missing": "отсутствующие языки",
        "empty": "пустые сегменты",
        "tag-only": "только теги",
        "duplicate": "дубли",
        "duplicates": "дубли",
        "noisy": "мусорные",
        "one-character": "односимвольные",
        "punctuation-only": "только пунктуация",
        "malformed units": "поврежденные TU",
        "malformed TU": "поврежденные TU",
        "Inline tags": "Inline-теги",
        "inline tags": "inline-теги",
        "Inline-tag mismatch": "Расхождение inline-тегов",
        "inline-tag mismatch": "расхождение inline-тегов",
        "inline-tag mismatches": "расхождения inline-тегов",
        "Strip inline tags": "Удаление inline-тегов",
        "Strip inline tags": "Удаление inline-тегов",
        "strip inline tags": "удалить inline-теги",
        "Language normalization": "Нормализация языковых кодов",
        "language normalization": "нормализация языковых кодов",
        "Normalize source language code to": "Нормализовать код языка оригинала в",
        "Normalize target language code to": "Нормализовать код языка перевода в",
        "Keep selected language pair": "Оставить выбранную языковую пару",
        "Keep only selected source-target language pair": "Оставить только выбранную пару оригинал-перевод",
        "Noisy rules": "Правила мусорных сегментов",
        "Noisy segment list": "Список мусорных сегментов",
        "list match mode": "режим совпадения со списком",
        "Both source and target": "Оба: оригинал и перевод",
        "Either source or target": "Любой: оригинал или перевод",
        "CAT system": "CAT-система",
        "CAT systems": "CAT-системы",
        "CAT-системаs": "CAT-системы",
        "tagged units": "TU с тегами",
        "plain-text memory": "текстовая память без тегов",
        "placeholders": "плейсхолдеры",
        "formatting markers": "маркеры форматирования",
        "line breaks": "переносы строк",
        "Report": "Отчет",
        "reports": "отчеты",
        "Reports": "Отчеты",
    }
    polished = {}
    for key, value in HELP_TOPICS_RU.items():
        title, body = value
        for src, dst in replacements.items():
            title = title.replace(src, dst)
            body = body.replace(src, dst)
        polished[key] = (title, body)
    HELP_TOPICS_RU.update(polished)

_polish_ru_help_topics()

def get_app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_settings_path():
    return os.path.join(get_app_dir(), "tost_settings.json")


def resource_path(relative_path):
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

def apply_window_icon(root):
    icon_path = resource_path("tost.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass


class ToolTip:
    def __init__(self, widget, text=None, text_func=None, delay_ms=2000, wraplength=420):
        self.widget = widget
        self.text = text
        self.text_func = text_func
        self.delay_ms = delay_ms
        self.wraplength = wraplength
        self._after_id = None
        self._tip_window = None
        self.widget.bind("<Enter>", self._schedule, add="+")
        self.widget.bind("<Leave>", self._hide, add="+")
        self.widget.bind("<ButtonPress>", self._hide, add="+")
        self.widget.bind("<FocusOut>", self._hide, add="+")

    def _get_text(self):
        if self.text_func:
            try:
                return self.text_func() or ""
            except Exception:
                return ""
        return self.text or ""

    def _schedule(self, event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        self._after_id = None
        text = self._get_text().strip()
        if not text or self._tip_window is not None:
            return
        try:
            x = self.widget.winfo_pointerx() + 14
            y = self.widget.winfo_pointery() + 18
        except Exception:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + 20
        self._tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=text,
            justify=tk.LEFT,
            background="#ffffe0",
            foreground="#222222",
            relief=tk.SOLID,
            borderwidth=1,
            padx=7,
            pady=5,
            wraplength=self.wraplength,
        )
        label.pack()

    def _hide(self, event=None):
        self._cancel()
        if self._tip_window is not None:
            try:
                self._tip_window.destroy()
            except Exception:
                pass
            self._tip_window = None


class MenuItemToolTip:
    """Tooltip for tk.Menu entries. Shows after the active menu item is hovered."""

    def __init__(self, menu, text_func, delay_ms=2000, wraplength=460):
        self.menu = menu
        self.text_func = text_func
        self.delay_ms = delay_ms
        self.wraplength = wraplength
        self._after_id = None
        self._tip_window = None
        self._current_label = None
        self.menu.bind("<<MenuSelect>>", self._on_menu_select, add="+")
        self.menu.bind("<Unmap>", self._hide, add="+")
        self.menu.bind("<Leave>", self._hide, add="+")
        self.menu.bind("<ButtonPress>", self._hide, add="+")

    def _on_menu_select(self, event=None):
        label = ""
        try:
            idx = self.menu.index("active")
            if idx is not None:
                label = self.menu.entrycget(idx, "label")
        except Exception:
            label = ""
        if label != self._current_label:
            self._hide()
            self._current_label = label
        if label:
            self._cancel()
            self._after_id = self.menu.after(self.delay_ms, self._show)

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.menu.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        self._after_id = None
        label = self._current_label or ""
        try:
            idx = self.menu.index("active")
            if idx is not None:
                active_label = self.menu.entrycget(idx, "label")
                if active_label:
                    label = active_label
                    self._current_label = active_label
        except Exception:
            pass
        try:
            text = (self.text_func(label) or "").strip()
        except Exception:
            text = ""
        if not text or self._tip_window is not None:
            return
        # Menus are drawn as top-level native windows on Windows. If the tooltip is
        # placed near the pointer it can be covered by the opened menu. Place it to
        # the right of the drop-down menu and force it above other windows.
        try:
            menu_x = self.menu.winfo_rootx()
            menu_y = self.menu.winfo_rooty()
            menu_w = max(self.menu.winfo_width(), 150)
            x = menu_x + menu_w + 10
            y = max(menu_y, self.menu.winfo_pointery() - 8)
        except Exception:
            x = self.menu.winfo_pointerx() + 180
            y = self.menu.winfo_pointery() - 8

        self._tip_window = tw = tk.Toplevel(self.menu.winfo_toplevel())
        tw.wm_overrideredirect(True)
        try:
            tw.wm_attributes("-topmost", True)
        except Exception:
            pass

        label_widget = tk.Label(
            tw,
            text=text,
            justify=tk.LEFT,
            background="#ffffe0",
            foreground="#222222",
            relief=tk.SOLID,
            borderwidth=1,
            padx=7,
            pady=5,
            wraplength=self.wraplength,
        )
        label_widget.pack()
        tw.update_idletasks()

        try:
            screen_w = tw.winfo_screenwidth()
            tip_w = tw.winfo_reqwidth()
            if x + tip_w + 8 > screen_w:
                x = max(8, menu_x - tip_w - 10)
        except Exception:
            pass

        tw.wm_geometry(f"+{x}+{y}")
        try:
            tw.lift()
        except Exception:
            pass

    def _hide(self, event=None):
        self._cancel()
        if self._tip_window is not None:
            try:
                self._tip_window.destroy()
            except Exception:
                pass
            self._tip_window = None
        if event is not None and getattr(event, "type", None):
            # Keep the active item label when the hide was caused by switching menu items.
            if str(event.type) not in ("VirtualEvent",):
                self._current_label = None


TU_START_RE = re.compile(br"<tu(?:\s|>)", re.IGNORECASE)
TU_END_RE = re.compile(br"</tu\s*>", re.IGNORECASE)
TUV_RE = re.compile(br"<tuv\b([^>]*)>(.*?)</tuv\s*>", re.IGNORECASE | re.DOTALL)
LANG_RE = re.compile(br"(?:xml:lang|lang)\s*=\s*(['\"])(.*?)\1", re.IGNORECASE | re.DOTALL)
SEG_RE = re.compile(br"<seg\b[^>]*>(.*?)</seg\s*>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(br"<[^>]+>", re.DOTALL)
INLINE_TAG_RE = re.compile(br"<\s*/?\s*([A-Za-z0-9:_-]+)([^>]*)>", re.DOTALL)
INLINE_ATTR_RE = re.compile(br"\b(x|i|id|rid|type)\s*=\s*([\'\"])(.*?)\2", re.IGNORECASE | re.DOTALL)



def parse_lang_set(value):
    return {x.strip().lower().replace("_", "-") for x in value.split(",") if x.strip()}


def sanitize_filename(name):
    name = os.path.basename(name)
    name = re.sub(r"[^\w._ -]+", "_", name)
    return name.strip(" .") or "tmx"


def bytes_to_text(data):
    for enc in ("utf-8-sig", "utf-16", "windows-1251", "latin-1"):
        try:
            return data.decode(enc)
        except Exception:
            pass
    return data.decode("utf-8", errors="replace")


def strip_xml_tags_and_space(data):
    data = re.sub(TAG_RE, b"", data)
    data = data.replace(b"&nbsp;", b" ")
    return data.strip()


def get_tuvs_from_xml(tu_bytes):
    result = []
    try:
        root = ET.fromstring(tu_bytes)
        for elem in root.iter():
            tag = elem.tag
            local = tag.split("}", 1)[-1] if isinstance(tag, str) else ""
            if local.lower() != "tuv":
                continue
            lang = None
            for key, value in elem.attrib.items():
                key_local = key.split("}", 1)[-1].lower()
                if key_local == "lang":
                    lang = value.strip().lower().replace("_", "-")
                    break

            seg_text = ""
            seg_has_inline_tags = False
            seg_found = False
            for child in elem.iter():
                child_tag = child.tag
                child_local = child_tag.split("}", 1)[-1] if isinstance(child_tag, str) else ""
                if child_local.lower() == "seg":
                    seg_found = True
                    seg_text = "".join(child.itertext()).strip()
                    # If <seg> has child XML elements but no text, it is usually a tag-only segment,
                    # for example <seg><ph x="1"/></seg>.
                    seg_has_inline_tags = any(True for _ in list(child))
                    break
            result.append({
                "lang": lang,
                "text": seg_text,
                "seg_found": seg_found,
                "tag_only": bool(seg_found and seg_has_inline_tags and not seg_text),
            })
        return result, None
    except Exception as exc:
        return None, str(exc)


def get_tuvs_fallback(tu_bytes):
    result = []
    for match in TUV_RE.finditer(tu_bytes):
        attrs = match.group(1)
        body = match.group(2)
        lang_match = LANG_RE.search(attrs)
        lang = None
        if lang_match:
            lang = bytes_to_text(lang_match.group(2)).strip().lower().replace("_", "-")
        seg_match = SEG_RE.search(body)
        seg_found = bool(seg_match)
        seg_body = seg_match.group(1) if seg_match else b""
        seg_text = bytes_to_text(strip_xml_tags_and_space(seg_body)).strip()
        tag_only = bool(seg_found and not seg_text and TAG_RE.search(seg_body))
        result.append({
            "lang": lang,
            "text": seg_text,
            "seg_found": seg_found,
            "tag_only": tag_only,
        })
    return result


def analyze_tu(tu_bytes, source_langs, target_langs):
    tuvs, xml_error = get_tuvs_from_xml(tu_bytes)
    used_fallback = False
    if tuvs is None or not tuvs:
        tuvs = get_tuvs_fallback(tu_bytes)
        used_fallback = True

    langs = []
    source_present = False
    target_present = False
    source_nonempty = False
    target_nonempty = False
    source_tag_only = False
    target_tag_only = False

    for tuv in tuvs:
        lang = tuv.get("lang")
        text = tuv.get("text") or ""
        tag_only = bool(tuv.get("tag_only"))
        if lang:
            langs.append(lang)
        nonempty = bool(text.strip())
        if lang in source_langs:
            source_present = True
            if nonempty:
                source_nonempty = True
            elif tag_only:
                source_tag_only = True
        if lang in target_langs:
            target_present = True
            if nonempty:
                target_nonempty = True
            elif tag_only:
                target_tag_only = True

    problems = []
    if not source_present:
        problems.append("missing_source_lang")
    elif source_nonempty:
        pass
    elif source_tag_only:
        problems.append("tag_only_source_seg")
    else:
        problems.append("empty_source_seg")

    if not target_present:
        problems.append("missing_target_lang")
    elif target_nonempty:
        pass
    elif target_tag_only:
        problems.append("tag_only_target_seg")
    else:
        problems.append("empty_target_seg")

    if not tuvs:
        problems.append("no_tuv_found")
    if used_fallback and xml_error:
        problems.append("xml_parse_error")

    return {
        "ok": not problems,
        "problems": problems,
        "langs": sorted(set(langs)),
        "tuv_count": len(tuvs),
        "xml_error": xml_error if used_fallback else "",
        "tuvs": tuvs,
    }


def get_preview(text, limit=180):
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) > limit:
        return text[:limit - 1] + "…"
    return text


def get_raw_xml_preview(tu_bytes, limit=32000):
    text = bytes_to_text(tu_bytes).strip()
    if len(text) > limit:
        return text[:limit - 1] + "…"
    return text


def select_text_for_langs(tuvs, lang_set):
    for tuv in tuvs or []:
        if tuv.get("lang") in lang_set:
            return tuv.get("text") or ""
    return ""

def normalize_pair_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def make_duplicate_key(tuvs, source_langs, target_langs):
    source = normalize_pair_text(select_text_for_langs(tuvs, source_langs))
    target = normalize_pair_text(select_text_for_langs(tuvs, target_langs))
    if not source or not target:
        return None
    return (source, target)


def parse_noisy_set(value):
    items = set()
    for item in (value or "").split(","):
        item = normalize_pair_text(item)
        if item:
            items.add(item)
    return items


def is_one_char_or_punctuation(text):
    text = normalize_pair_text(text)
    if not text:
        return False
    # "A" or "1" can be valid UI strings, so this is only a candidate check,
    # not an automatic deletion rule unless the user enables the option.
    if len(text) == 1:
        return True
    return all((not ch.isalnum()) for ch in text)


def is_noisy_segment(text, noisy_set):
    text = normalize_pair_text(text)
    if not text:
        return False
    return text in noisy_set


def noisy_list_pair_matches(source_text, target_text, noisy_set, match_mode):
    source_is_noisy = is_noisy_segment(source_text, noisy_set)
    target_is_noisy = is_noisy_segment(target_text, noisy_set)
    if match_mode == "Either source or target":
        return bool(source_is_noisy or target_is_noisy)
    return bool(source_is_noisy and target_is_noisy)


def is_short_length_pair(source_text, target_text, threshold):
    source_text = normalize_pair_text(source_text)
    target_text = normalize_pair_text(target_text)
    if not source_text or not target_text or threshold <= 0:
        return False
    return len(source_text) <= threshold and len(target_text) <= threshold


def get_source_target_texts(tuvs, source_langs, target_langs):
    return (
        normalize_pair_text(select_text_for_langs(tuvs, source_langs)),
        normalize_pair_text(select_text_for_langs(tuvs, target_langs)),
    )



def get_seg_body_for_langs(tu_bytes, lang_set):
    """Return the raw inner XML of the first <seg> for the requested language variants."""
    for match in TUV_RE.finditer(tu_bytes):
        attrs = match.group(1)
        body = match.group(2)
        lang_match = LANG_RE.search(attrs)
        if not lang_match:
            continue
        lang = bytes_to_text(lang_match.group(2)).strip().lower().replace("_", "-")
        if lang not in lang_set:
            continue
        seg_match = SEG_RE.search(body)
        if seg_match:
            return seg_match.group(1)
    return b""


def normalize_inline_tag_name(name_bytes):
    name = bytes_to_text(name_bytes).strip().lower()
    if ":" in name:
        name = name.split(":", 1)[1]
    return name


def inline_tag_sequence_from_seg_body(seg_body):
    """Return a conservative inline tag sequence from raw <seg> inner XML.

    The sequence keeps the tag name and stable tag identifiers when present.
    This is intentionally used as a warning/check, not as a default deletion rule.
    """
    sequence = []
    for match in INLINE_TAG_RE.finditer(seg_body or b""):
        name = normalize_inline_tag_name(match.group(1))
        if not name or name == "seg":
            continue
        attrs = match.group(2) or b""
        keys = []
        for attr in INLINE_ATTR_RE.finditer(attrs):
            attr_name = bytes_to_text(attr.group(1)).strip().lower()
            attr_value = bytes_to_text(attr.group(3)).strip()
            if attr_value:
                keys.append(f"{attr_name}={attr_value}")
        if keys:
            sequence.append(f"{name}[{','.join(keys)}]")
        else:
            sequence.append(name)
    return sequence


def get_inline_tag_sequences(tu_bytes, source_langs, target_langs):
    source_seg = get_seg_body_for_langs(tu_bytes, source_langs)
    target_seg = get_seg_body_for_langs(tu_bytes, target_langs)
    return (
        inline_tag_sequence_from_seg_body(source_seg),
        inline_tag_sequence_from_seg_body(target_seg),
    )


def inline_tag_mismatch_reason(source_sequence, target_sequence):
    if source_sequence == target_sequence:
        return ""
    if len(source_sequence) != len(target_sequence):
        return "inline_tag_count_mismatch"
    return "inline_tag_sequence_mismatch"


# Inline tag stripping is intentionally conservative. Placeholder-like TMX
# inline tags are removed completely. Wrapper-like tags are unwrapped so their
# text content is preserved.
INLINE_PLACEHOLDER_NAMES = ["ph", "bpt", "ept", "it", "ut"]
INLINE_WRAPPER_NAMES = ["hi", "sub"]


def _tag_name_pattern(name):
    return rb"(?:[A-Za-z0-9_-]+:)?" + name.encode("ascii")


def strip_inline_tags_from_bytes(data):
    if not data:
        return data
    result = data
    # Remove paired placeholder tags with their encoded native-tag payload.
    for name in INLINE_PLACEHOLDER_NAMES:
        n = _tag_name_pattern(name)
        result = re.sub(rb"<\s*" + n + rb"\b[^>]*>.*?<\s*/\s*" + n + rb"\s*>", b"", result, flags=re.IGNORECASE | re.DOTALL)
        result = re.sub(rb"<\s*" + n + rb"\b[^>]*/\s*>", b"", result, flags=re.IGNORECASE | re.DOTALL)
        # Fallback for non-self-closing placeholder start/end tags without content.
        result = re.sub(rb"<\s*/?\s*" + n + rb"\b[^>]*>", b"", result, flags=re.IGNORECASE | re.DOTALL)
    # Unwrap wrapper tags and keep their contents.
    for name in INLINE_WRAPPER_NAMES:
        n = _tag_name_pattern(name)
        result = re.sub(rb"<\s*/?\s*" + n + rb"\b[^>]*>", b"", result, flags=re.IGNORECASE | re.DOTALL)
    return result


def normalize_lang_value_in_tuv(tuv_bytes, new_lang_code):
    """Replace only the language-code value in the first lang/xml:lang attribute of a <tuv>."""
    if not tuv_bytes or not new_lang_code:
        return tuv_bytes
    new_value = str(new_lang_code).strip().encode("utf-8")
    if not new_value:
        return tuv_bytes

    def repl(match):
        raw = match.group(0)
        old_value = match.group(2)
        idx = raw.find(old_value)
        if idx < 0:
            return raw
        return raw[:idx] + new_value + raw[idx + len(old_value):]

    return LANG_RE.sub(repl, tuv_bytes, count=1)


def filter_and_normalize_tuvs(tu_bytes, source_langs, target_langs, keep_only_pair=False,
                              normalize_source=False, normalize_target=False,
                              source_code="", target_code=""):
    """Preserve the TU wrapper and non-TUV metadata while optionally removing unselected TUVs
    and normalizing the selected source/target language codes. Returns (new_bytes, changes).
    """
    changes = []
    if not tu_bytes:
        return tu_bytes, changes
    source_code = (source_code or "").strip()
    target_code = (target_code or "").strip()
    result_parts = []
    last = 0
    seen_source = False
    seen_target = False
    any_changed = False

    for match in TUV_RE.finditer(tu_bytes):
        attrs = match.group(1) or b""
        tuv_raw = match.group(0)
        lang_match = LANG_RE.search(attrs)
        lang = None
        if lang_match:
            lang = bytes_to_text(lang_match.group(2)).strip().lower().replace("_", "-")

        is_source = bool(lang in source_langs)
        is_target = bool(lang in target_langs)
        keep = True
        if keep_only_pair and not (is_source or is_target):
            keep = False

        result_parts.append(tu_bytes[last:match.start()])
        if keep:
            new_tuv = tuv_raw
            if is_source and normalize_source and source_code:
                normalized = normalize_lang_value_in_tuv(new_tuv, source_code)
                if normalized != new_tuv:
                    changes.append(f"normalize_source_lang:{lang}->{source_code}")
                    new_tuv = normalized
                    any_changed = True
            if is_target and normalize_target and target_code:
                normalized = normalize_lang_value_in_tuv(new_tuv, target_code)
                if normalized != new_tuv:
                    changes.append(f"normalize_target_lang:{lang}->{target_code}")
                    new_tuv = normalized
                    any_changed = True
            result_parts.append(new_tuv)
            if is_source:
                seen_source = True
            if is_target:
                seen_target = True
        else:
            changes.append(f"remove_unselected_tuv:{lang or '(no lang)'}")
            any_changed = True
        last = match.end()

    result_parts.append(tu_bytes[last:])
    if not any_changed:
        return tu_bytes, []
    return b"".join(result_parts), changes


def build_language_stats(tuvs):
    stats = {}
    seen_in_tu = set()
    for tuv in tuvs or []:
        lang = tuv.get("lang") or "(no lang)"
        text = (tuv.get("text") or "").strip()
        tag_only = bool(tuv.get("tag_only"))
        row = stats.setdefault(lang, {
            "tuv_count": 0,
            "tu_count": 0,
            "non_empty_seg_count": 0,
            "empty_seg_count": 0,
            "tag_only_seg_count": 0,
        })
        row["tuv_count"] += 1
        if text:
            row["non_empty_seg_count"] += 1
        elif tag_only:
            row["tag_only_seg_count"] += 1
        else:
            row["empty_seg_count"] += 1
        seen_in_tu.add(lang)
    for lang in seen_in_tu:
        stats[lang]["tu_count"] += 1
    return stats


def merge_language_stats(total_stats, tuvs):
    per_tu = build_language_stats(tuvs)
    for lang, vals in per_tu.items():
        row = total_stats.setdefault(lang, {
            "tuv_count": 0,
            "tu_count": 0,
            "non_empty_seg_count": 0,
            "empty_seg_count": 0,
            "tag_only_seg_count": 0,
        })
        for key, value in vals.items():
            row[key] += value

def iter_tu_blocks(path):
    with open(path, "rb") as f:
        in_tu = False
        block = []
        line_no = 0
        start_line = 0
        while True:
            line = f.readline()
            if not line:
                break
            line_no += 1
            if not in_tu:
                if TU_START_RE.search(line):
                    in_tu = True
                    start_line = line_no
                    block = [line]
                    if TU_END_RE.search(line):
                        yield start_line, b"".join(block)
                        in_tu = False
                        block = []
            else:
                block.append(line)
                if TU_END_RE.search(line):
                    yield start_line, b"".join(block)
                    in_tu = False
                    block = []


def write_closing(writer):
    writer.write(b"  </body>\n</tmx>\n")


def build_error_rows(ok_rows, missing_source, missing_target, empty_source, empty_target, tag_only_source, tag_only_target, xml_parse_error, no_tuv):
    rows = [
        ("Potentially importable TU", ok_rows),
        ("Total detected issues", missing_source + missing_target + empty_source + empty_target + tag_only_source + tag_only_target + xml_parse_error + no_tuv),
        ("Missing source-language segment", missing_source),
        ("Missing target-language segment", missing_target),
        ("Empty source-language segment", empty_source),
        ("Empty target-language segment", empty_target),
        ("Source segment is tag-only", tag_only_source),
        ("Target segment is tag-only", tag_only_target),
        ("XML parse error / malformed inline tags", xml_parse_error),
        ("No TUV segments found", no_tuv),
    ]
    return [(name, count) for name, count in rows if name in ("Potentially importable TU", "Total detected issues") or count > 0]

def xlsx_col_name(index):
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _xlsx_sanitize_text(value):
    """Remove XML characters that are not valid in XLSX inline strings."""
    if value is None:
        return ""
    text = str(value)
    return ''.join(ch for ch in text if ch in ('\t', '\n', '\r') or ord(ch) >= 32)


def _xlsx_style_for_sheet(sheet_name, row_idx):
    """Return style id for a cell in the given report sheet."""
    if row_idx == 1:
        return 1
    name = (sheet_name or '').lower()
    if any(token in name for token in ('removed', 'duplicates')):
        return 3
    if any(token in name for token in ('warning', 'warnings')):
        return 2
    if 'changed' in name:
        return 4
    if 'summary' in name:
        return 5
    return 0


def xlsx_cell(value, row, col, style_id=0):
    ref = f"{xlsx_col_name(col)}{row}"
    style_attr = f' s="{style_id}"' if style_id else ""
    if value is None:
        value = ""
    if isinstance(value, bool):
        return f'<c r="{ref}"{style_attr} t="b"><v>{1 if value else 0}</v></c>'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}"{style_attr}><v>{value}</v></c>'
    text = escape(_xlsx_sanitize_text(value), {'"': '&quot;'})
    return f'<c r="{ref}"{style_attr} t="inlineStr"><is><t>{text}</t></is></c>'


def _xlsx_column_widths(rows):
    widths = []
    for row in rows:
        for idx, value in enumerate(row):
            text = _xlsx_sanitize_text(value)
            first_line = max((len(part) for part in text.splitlines()), default=0)
            length = min(max(first_line + 2, 10), 80)
            if idx >= len(widths):
                widths.append(length)
            else:
                widths[idx] = max(widths[idx], length)
    return widths


def _xlsx_ref(row_count, col_count):
    if row_count < 1 or col_count < 1:
        return "A1:A1"
    return f"A1:{xlsx_col_name(col_count)}{row_count}"


def make_sheet_xml(rows, sheet_name=""):
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
    out.append('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">')

    if rows:
        out.append('<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>')

    widths = _xlsx_column_widths(rows)
    if widths:
        out.append('<cols>')
        for idx, width in enumerate(widths, 1):
            out.append(f'<col min="{idx}" max="{idx}" width="{width}" customWidth="1"/>')
        out.append('</cols>')

    out.append('<sheetData>')
    for r_idx, row in enumerate(rows, 1):
        out.append(f'<row r="{r_idx}">')
        style_id = _xlsx_style_for_sheet(sheet_name, r_idx)
        for c_idx, value in enumerate(row, 1):
            out.append(xlsx_cell(value, r_idx, c_idx, style_id))
        out.append('</row>')
    out.append('</sheetData>')

    if len(rows) > 1 and rows[0]:
        out.append(f'<autoFilter ref="{_xlsx_ref(len(rows), len(rows[0]))}"/>')

    out.append('</worksheet>')
    return ''.join(out)


def safe_sheet_name(title, used):
    clean = re.sub(r'[\\/\?\*\[\]:]', '_', title)[:31].strip() or 'Sheet'
    base = clean
    n = 2
    while clean.lower() in used:
        suffix = f"_{n}"
        clean = base[:31 - len(suffix)] + suffix
        n += 1
    used.add(clean.lower())
    return clean


def _xlsx_styles_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="3">
    <font><sz val="11"/><color theme="1"/><name val="Calibri"/><family val="2"/></font>
    <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/><family val="2"/></font>
    <font><b/><sz val="11"/><color theme="1"/><name val="Calibri"/><family val="2"/></font>
  </fonts>
  <fills count="7">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1F4E79"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFF4CCCC"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFD9EAD3"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFD9EAF7"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border><left style="thin"><color rgb="FFD9D9D9"/></left><right style="thin"><color rgb="FFD9D9D9"/></right><top style="thin"><color rgb="FFD9D9D9"/></top><bottom style="thin"><color rgb="FFD9D9D9"/></bottom><diagonal/></border>
  </borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="6">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="3" borderId="1" xfId="0" applyFill="1" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyFill="1" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="6" borderId="1" xfId="0" applyFill="1" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="5" borderId="1" xfId="0" applyFill="1" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
  <dxfs count="0"/><tableStyles count="0" defaultTableStyle="TableStyleMedium2" defaultPivotStyle="PivotStyleLight16"/>
</styleSheet>"""


def write_xlsx(path, sheets):
    safe_sheets = []
    used = set()
    for title, rows in sheets:
        safe_sheets.append((safe_sheet_name(title, used), rows))

    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
    ]
    for idx in range(1, len(safe_sheets) + 1):
        content_types.append(f'<Override PartName="/xl/worksheets/sheet{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
    content_types.append('</Types>')

    workbook = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>',
    ]
    rels = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    ]
    for idx, (title, _rows) in enumerate(safe_sheets, 1):
        title_xml = escape(title, {'"': '&quot;'})
        workbook.append(f'<sheet name="{title_xml}" sheetId="{idx}" r:id="rId{idx}"/>')
        rels.append(f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>')
    styles_rid = len(safe_sheets) + 1
    rels.append(f'<Relationship Id="rId{styles_rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>')
    workbook.append('</sheets></workbook>')
    rels.append('</Relationships>')

    root_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>\n</Relationships>'

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", ''.join(content_types))
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("xl/workbook.xml", ''.join(workbook))
        zf.writestr("xl/_rels/workbook.xml.rels", ''.join(rels))
        zf.writestr("xl/styles.xml", _xlsx_styles_xml())
        for idx, (title, rows) in enumerate(safe_sheets, 1):
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", make_sheet_xml(rows, title))


class TmxSplitterApp:
    def _install_centered_messageboxes(self):
        """Replace standard message dialogs with centered TOST dialogs.

        Native Windows messagebox dialogs do not reliably honor the Tk parent
        geometry in all cases, so passing parent=... is not enough. These custom
        modal dialogs are ordinary Toplevel windows and are explicitly centered
        relative to the current owner window.
        """
        if getattr(messagebox, "_tost_custom_centered", False):
            return

        def _parse_title_message(args, kwargs):
            title = args[0] if len(args) >= 1 else kwargs.pop("title", APP_TITLE)
            message = args[1] if len(args) >= 2 else kwargs.pop("message", "")
            parent = kwargs.pop("parent", None) or self.root
            return title, message, parent

        def _center_child(win, parent):
            try:
                owner = parent.winfo_toplevel() if parent is not None else self.root
                if not owner.winfo_ismapped():
                    owner = self.root
                owner.update_idletasks()
                win.update_idletasks()

                pw = owner.winfo_width()
                ph = owner.winfo_height()
                if pw <= 1:
                    pw = owner.winfo_reqwidth()
                if ph <= 1:
                    ph = owner.winfo_reqheight()
                px = owner.winfo_rootx()
                py = owner.winfo_rooty()

                ww = win.winfo_reqwidth()
                wh = win.winfo_reqheight()
                if ww <= 1:
                    ww = win.winfo_width()
                if wh <= 1:
                    wh = win.winfo_height()

                x = px + max(0, (pw - ww) // 2)
                y = py + max(0, (ph - wh) // 2)
                sw = win.winfo_screenwidth()
                sh = win.winfo_screenheight()
                x = max(0, min(x, sw - ww - 8))
                y = max(0, min(y, sh - wh - 40))
                win.geometry(f"{ww}x{wh}+{x}+{y}")
                win.update_idletasks()
            except Exception:
                pass

        def _dialog(kind, title, message, parent, buttons):
            result = {"value": None}
            owner = parent.winfo_toplevel() if parent is not None else self.root
            if not owner.winfo_ismapped():
                owner = self.root
            win = tk.Toplevel(owner)
            win.withdraw()
            win.title(title or APP_TITLE)
            win.transient(owner)
            win.resizable(False, False)
            try:
                win.iconbitmap(resource_path("tost.ico"))
            except Exception:
                pass

            outer = ttk.Frame(win, padding=(18, 16, 18, 12))
            outer.grid(row=0, column=0, sticky="nsew")
            outer.columnconfigure(1, weight=1)

            icon_map = {
                "info": ("i", "#1f8fd5"),
                "warning": ("!", "#d99000"),
                "error": ("×", "#d93025"),
                "question": ("?", "#1f8fd5"),
            }
            icon_text, icon_color = icon_map.get(kind, icon_map["info"])
            icon = tk.Label(
                outer,
                text=icon_text,
                width=2,
                height=1,
                fg="white",
                bg=icon_color,
                font=("Segoe UI", 15, "bold"),
                relief="flat",
            )
            icon.grid(row=0, column=0, padx=(0, 14), pady=(0, 10), sticky="n")

            msg = ttk.Label(outer, text=str(message), justify="left", wraplength=420)
            msg.grid(row=0, column=1, sticky="w", pady=(0, 10))

            btn_frame = ttk.Frame(outer)
            btn_frame.grid(row=1, column=0, columnspan=2, sticky="e", pady=(8, 0))

            def close(value):
                result["value"] = value
                try:
                    win.grab_release()
                except Exception:
                    pass
                win.destroy()

            for idx, (label, value, default) in enumerate(buttons):
                btn = ttk.Button(btn_frame, text=label, width=10, command=lambda v=value: close(v))
                btn.grid(row=0, column=idx, padx=(6, 0))
                if default:
                    btn.focus_set()
                    win.bind("<Return>", lambda event, v=value: close(v))

            cancel_value = buttons[-1][1] if buttons else None
            win.protocol("WM_DELETE_WINDOW", lambda: close(cancel_value))
            win.bind("<Escape>", lambda event: close(cancel_value))

            _center_child(win, owner)
            win.deiconify()
            try:
                win.lift(owner)
            except Exception:
                win.lift()
            win.grab_set()
            owner.wait_window(win)
            return result["value"]

        def showinfo(*args, **kwargs):
            title, message, parent = _parse_title_message(args, kwargs)
            return _dialog("info", title, message, parent, [("OK", "ok", True)])

        def showwarning(*args, **kwargs):
            title, message, parent = _parse_title_message(args, kwargs)
            return _dialog("warning", title, message, parent, [("OK", "ok", True)])

        def showerror(*args, **kwargs):
            title, message, parent = _parse_title_message(args, kwargs)
            return _dialog("error", title, message, parent, [("OK", "ok", True)])

        def askyesno(*args, **kwargs):
            title, message, parent = _parse_title_message(args, kwargs)
            return _dialog("question", title, message, parent, [(self.tr("Yes"), True, True), (self.tr("No"), False, False)])

        def askyesnocancel(*args, **kwargs):
            title, message, parent = _parse_title_message(args, kwargs)
            return _dialog("question", title, message, parent, [(self.tr("Yes"), True, True), (self.tr("No"), False, False), (self.tr("Cancel"), None, False)])

        def askokcancel(*args, **kwargs):
            title, message, parent = _parse_title_message(args, kwargs)
            return _dialog("question", title, message, parent, [("OK", True, True), (self.tr("Cancel"), False, False)])

        messagebox.showinfo = showinfo
        messagebox.showwarning = showwarning
        messagebox.showerror = showerror
        messagebox.askyesno = askyesno
        messagebox.askyesnocancel = askyesnocancel
        messagebox.askokcancel = askokcancel
        messagebox._tost_custom_centered = True

    def __init__(self, root):
        self.root = root
        self._install_centered_messageboxes()
        self.root.title(APP_TITLE)
        self.root.geometry("980x805")
        self.queue = queue.Queue()
        self.worker = None
        self.cancel_event = threading.Event()
        self.files = []
        self.last_report_path = None
        self.last_optimized_tmx_path = None
        self.last_problem_tus = []
        self.last_removed_tus = []
        self.last_duplicate_tus = []
        self.last_noisy_warnings = []
        self.last_inline_tag_warnings = []
        self.last_changed_tus = []
        self.ui_language = tk.StringVar(value="English")
        self.result_summary = tk.StringVar(value="Result summary: no analysis or optimization has been run yet.")
        self.compare_files_a = []
        self.compare_files_b = []
        self.compare_files_a_label = tk.StringVar(value=self.tr("No TMX files selected"))
        self.compare_files_b_label = tk.StringVar(value=self.tr("No TMX files selected"))
        self.compare_recursive = tk.BooleanVar(value=False)
        # v4.7.1: lightweight UI state. These values are saved automatically on exit.
        self.last_export_format = tk.StringVar(value="XLSX report")
        self._saved_selected_tab_index = 0
        self._saved_window_geometry = ""

        self.output_dir = tk.StringVar(value=os.path.abspath("output"))
        self.max_mb = tk.StringVar(value=DEFAULT_MAX_MB)
        self.part_tu_count = tk.StringVar(value=DEFAULT_PART_TU_COUNT)
        self.split_mode = tk.StringVar(value="mb")
        self.post_check_after_split = tk.BooleanVar(value=True)
        self.prefix = tk.StringVar(value=DEFAULT_PREFIX)
        self.source_langs = tk.StringVar(value=DEFAULT_SOURCE_LANGS)
        self.target_langs = tk.StringVar(value=DEFAULT_TARGET_LANGS)
        self.analyze_before_split = tk.BooleanVar(value=True)

        # Optimize TMX v3.0 options. These options create new optimized TMX files; source files are never modified.
        self.opt_remove_missing_source = tk.BooleanVar(value=True)
        self.opt_remove_missing_target = tk.BooleanVar(value=True)
        self.opt_remove_empty = tk.BooleanVar(value=True)
        self.opt_remove_tag_only = tk.BooleanVar(value=True)
        self.opt_remove_xml_errors = tk.BooleanVar(value=False)

        # Optimize TMX v3.1.1 options: duplicate and noisy short segment handling.
        self.opt_remove_duplicates = tk.BooleanVar(value=False)
        self.opt_warn_noisy = tk.BooleanVar(value=True)
        self.opt_remove_noisy = tk.BooleanVar(value=False)
        self.opt_remove_one_char_punct = tk.BooleanVar(value=False)
        self.opt_noisy_segments = tk.StringVar(value="-, :, ;, ., •, *, +, %")
        self.opt_noisy_match_mode = tk.StringVar(value="Both source and target")
        self.opt_warn_min_length = tk.BooleanVar(value=False)
        self.opt_min_text_length = tk.StringVar(value="2")

        # Optimize TMX v3.2.4 options: inline tag mismatch checks and optional stripping.
        self.opt_report_inline_tag_mismatch = tk.BooleanVar(value=True)
        self.opt_strip_mismatched_inline_tags = tk.BooleanVar(value=False)
        self.opt_strip_all_inline_tags = tk.BooleanVar(value=False)

        # Optimize TMX v3.4 options: selected language pair and user-defined language-code normalization.
        self.opt_keep_selected_pair = tk.BooleanVar(value=False)
        self.opt_normalize_source_lang = tk.BooleanVar(value=False)
        self.opt_normalize_target_lang = tk.BooleanVar(value=False)
        self.opt_normalize_source_code = tk.StringVar(value=DEFAULT_NORMALIZE_SOURCE_LANG)
        self.opt_normalize_target_code = tk.StringVar(value=DEFAULT_NORMALIZE_TARGET_LANG)

        # Optimize TMX v4.0.1: dry run creates reports only and does not leave an optimized TMX file.
        self.opt_dry_run = tk.BooleanVar(value=False)

        # Optimize TMX v3.3: optimization profiles. Profiles only set option defaults; all processing remains explicit and local.
        self.opt_profile = tk.StringVar(value="General CAT-safe")
        self.opt_profile_display = tk.StringVar(value="General CAT-safe")
        self.profile_descriptions = {
            "General CAT-safe": "Safe default profile. Removes missing, empty and tag-only TU; reports noisy pairs and inline-tag mismatch. Does not remove duplicates, normalize language codes or strip inline tags.",
            "Strict import": "Stricter cleanup profile. Removes missing, empty, tag-only and malformed TU, removes exact duplicate source-target pairs, and reports noisy pairs and inline-tag mismatch. Does not normalize language codes by default.",
            "Smartcat-oriented": "CAT import-oriented profile using Smartcat as a practical reference. Keeps only the selected source-target pair, normalizes language codes to the user-defined values, removes missing/empty/tag-only TU, exact duplicates, configured noisy pairs and one-character/punctuation-only pairs, and reports inline-tag mismatch.",
            "Custom": "Manual profile. Keeps the current checkbox settings unchanged so you can tune cleanup rules yourself.",
        }
        self.builtin_profile_values = ("General CAT-safe", "Strict import", "Smartcat-oriented", "Custom")
        self.user_profiles = {}

        self.load_settings()
        self.compare_files_a_label.set(self.tr("No TMX files selected"))
        self.compare_files_b_label.set(self.tr("No TMX files selected"))
        self.set_profile_value(self.opt_profile.get())
        if self.is_ru():
            self.opt_noisy_match_mode.set(self.noisy_mode_label(self.noisy_mode_key(self.opt_noisy_match_mode.get())))
        self.result_summary.set(self.tr("Result summary: no analysis or optimization has been run yet."))
        self.build_ui()
        if self.is_ru():
            self.translate_widget_tree(self.root)
        self.restore_ui_state()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(100, self.process_queue)

    def is_ru(self):
        return self.ui_language.get() in ("Русский", "Russian", "ru")

    def tr(self, text):
        if self.is_ru():
            return UI_TRANSLATIONS_RU.get(text, text)
        return text


    def profile_label(self, profile):
        if not self.is_ru():
            return profile
        labels = {
            "General CAT-safe": "Общий CAT-safe",
            "Strict import": "Строгий импорт",
            "Smartcat-oriented": "Ориентированный на Smartcat",
            "Custom": "Пользовательский",
        }
        return labels.get(profile, profile)

    def profile_key_from_label(self, label):
        if not self.is_ru():
            return label
        reverse_labels = {
            "Общий CAT-safe": "General CAT-safe",
            "Строгий импорт": "Strict import",
            "Ориентированный на Smartcat": "Smartcat-oriented",
            "Пользовательский": "Custom",
        }
        return reverse_labels.get(label, label)

    def set_profile_value(self, profile):
        # Store the internal profile key in English, but show a localized label in the UI.
        if hasattr(self, "opt_profile"):
            self.opt_profile.set(profile)
        if hasattr(self, "opt_profile_display"):
            self.opt_profile_display.set(self.profile_label(profile))

    def noisy_mode_label(self, mode):
        if self.is_ru():
            return {
                "Both source and target": "Оба: оригинал и перевод",
                "Either source or target": "Любой: оригинал или перевод",
            }.get(mode, mode)
        return mode

    def noisy_mode_key(self, mode):
        return {
            "Оба: оригинал и перевод": "Both source and target",
            "Любой: оригинал или перевод": "Either source or target",
        }.get(mode, mode)

    def translate_widget_tree(self, widget):
        """Best-effort translation of static Tk/ttk text created from English base strings."""
        try:
            current = widget.cget("text")
            translated = self.tr(current)
            if translated != current:
                widget.configure(text=translated)
        except Exception:
            pass
        try:
            if isinstance(widget, ttk.Notebook):
                for tab_id in widget.tabs():
                    txt = widget.tab(tab_id, "text")
                    widget.tab(tab_id, text=self.tr(txt))
        except Exception:
            pass
        for child in widget.winfo_children():
            self.translate_widget_tree(child)

    def help_topics_localized(self):
        base = self.help_topics_base()
        if not self.is_ru():
            return base
        return {HELP_TOPICS_RU.get(k, (k, v))[0]: HELP_TOPICS_RU.get(k, (k, v))[1] for k, v in base.items()}

    def build_ui(self):
        main = ttk.Frame(self.root, padding=6)
        main.pack(fill=tk.BOTH, expand=True)

        # File selection is shared by all modes.
        file_frame = ttk.LabelFrame(main, text="TMX files", padding=5)
        file_frame.pack(fill=tk.BOTH, expand=False)

        buttons = ttk.Frame(file_frame)
        buttons.pack(fill=tk.X)
        ttk.Button(buttons, text="Add TMX files...", command=self.add_files).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Remove selected", command=self.remove_selected).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="Clear", command=self.clear_files).pack(side=tk.LEFT)

        self.settings_icon = None
        for icon_name in ("settings_icon.png",):
            settings_icon_path = resource_path(icon_name)
            try:
                if os.path.exists(settings_icon_path):
                    self.settings_icon = tk.PhotoImage(file=settings_icon_path)
                    break
            except Exception:
                self.settings_icon = None

        self.help_icon = None
        for icon_name in ("help_icon.png",):
            help_icon_path = resource_path(icon_name)
            try:
                if os.path.exists(help_icon_path):
                    self.help_icon = tk.PhotoImage(file=help_icon_path)
                    break
            except Exception:
                self.help_icon = None

        # Pack from right to left: Help is rightmost, Settings is to its left.
        # Both icons use matching 24 px images so the buttons have the same visual size.
        if self.help_icon:
            help_button = ttk.Button(buttons, image=self.help_icon, command=self.show_help, width=3)
            help_button.pack(side=tk.RIGHT)
            ToolTip(help_button, self.tr("Help"))
        else:
            ttk.Button(buttons, text="Help", command=self.show_help).pack(side=tk.RIGHT)

        if self.settings_icon:
            settings_button = ttk.Button(buttons, image=self.settings_icon, command=self.show_settings_about, width=3)
            settings_button.pack(side=tk.RIGHT, padx=(0, 6))
            ToolTip(settings_button, self.tr("Settings / About"))
        else:
            ttk.Button(buttons, text="Settings / About", command=self.show_settings_about).pack(side=tk.RIGHT, padx=(0, 6))

        self.file_list = tk.Listbox(file_frame, height=3, selectmode=tk.EXTENDED)
        self.file_list.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        self.notebook = ttk.Notebook(main, height=430)
        self.notebook.pack(fill=tk.X, expand=False, pady=(3, 2))
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # ------------------------------------------------------------------
        # Tab 1: Split / Analyze
        # ------------------------------------------------------------------
        split_tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(split_tab, text="Split / Analyze")

        ttk.Label(
            split_tab,
            text="Safe split preserves original TU content and splits only on <tu> boundaries. Original TMX files are never modified.",
            wraplength=880,
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 3))

        output_box = ttk.LabelFrame(split_tab, text="Output", padding=5)
        output_box.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 4))
        ttk.Label(output_box, text="Output folder:").grid(row=0, column=0, sticky="w")
        ttk.Entry(output_box, textvariable=self.output_dir).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(output_box, text="Browse...", command=self.choose_output).grid(row=0, column=2)
        output_box.columnconfigure(1, weight=1)

        lang_box = ttk.LabelFrame(split_tab, text="Language pair / language variants", padding=5)
        lang_box.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 4))
        ttk.Label(lang_box, text="Source langs:").grid(row=0, column=0, sticky="w")
        ttk.Entry(lang_box, textvariable=self.source_langs).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Label(lang_box, text="Target langs:").grid(row=1, column=0, sticky="w", pady=(1, 0))
        ttk.Entry(lang_box, textvariable=self.target_langs).grid(row=1, column=1, sticky="ew", padx=6, pady=(1, 0))
        ttk.Label(
            lang_box,
            text="Use comma-separated variants, for example: en,en-us,en-gb and ru,ru-ru.",
            foreground="#555555",
        ).grid(row=2, column=1, sticky="w", padx=6, pady=(1, 0))
        lang_box.columnconfigure(1, weight=1)

        split_box = ttk.LabelFrame(split_tab, text="Safe split settings", padding=5)
        split_box.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 4))
        ttk.Label(split_box, text="Split mode:").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(split_box, text="By file size, MB", variable=self.split_mode, value="mb").grid(row=0, column=1, sticky="w", padx=6)
        ttk.Entry(split_box, textvariable=self.max_mb, width=12).grid(row=0, column=2, sticky="w", padx=6)
        ttk.Radiobutton(split_box, text="By TU count", variable=self.split_mode, value="tu").grid(row=1, column=1, sticky="w", padx=6, pady=(1, 0))
        ttk.Entry(split_box, textvariable=self.part_tu_count, width=12).grid(row=1, column=2, sticky="w", padx=6, pady=(1, 0))
        ttk.Label(split_box, text="Prefix:").grid(row=2, column=0, sticky="w", pady=(2, 0))
        ttk.Entry(split_box, textvariable=self.prefix, width=12).grid(row=2, column=1, sticky="w", padx=6, pady=(2, 0))
        ttk.Checkbutton(
            split_box,
            text="Analyze TMX before splitting and create XLSX report",
            variable=self.analyze_before_split,
        ).grid(row=3, column=1, columnspan=2, sticky="w", padx=6, pady=(2, 0))
        ttk.Checkbutton(
            split_box,
            text="Post-check created files after splitting",
            variable=self.post_check_after_split,
        ).grid(row=4, column=1, columnspan=2, sticky="w", padx=6, pady=(1, 0))
        ttk.Label(
            split_box,
            text="TU count mode counts written <tu> blocks only. Safe split still preserves TU content.",
            foreground="#555555",
        ).grid(row=5, column=1, columnspan=2, sticky="w", padx=6, pady=(1, 0))
        split_box.columnconfigure(2, weight=1)

        split_actions = ttk.Frame(split_tab)
        split_actions.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(2, 0))
        self.analyze_btn = ttk.Button(split_actions, text="Analyze", command=self.start_analyze_only)
        self.analyze_btn.pack(side=tk.LEFT)
        self.start_btn = ttk.Button(split_actions, text="Safe Split", command=self.start_split)
        self.start_btn.pack(side=tk.LEFT, padx=6)
        self.cancel_btn = ttk.Button(split_actions, text="Cancel", command=self.cancel, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT)
        ttk.Button(split_actions, text="Open output folder", command=self.open_output_folder).pack(side=tk.LEFT, padx=6)
        ttk.Button(split_actions, text="Open report", command=self.open_last_report).pack(side=tk.LEFT)
        ttk.Button(split_actions, text="View problem TUs", command=self.view_problem_tus).pack(side=tk.LEFT, padx=6)
        ttk.Button(split_actions, text="Export problem TUs", command=lambda: self.export_result_groups_dialog(default_groups=("Problem TUs",))).pack(side=tk.LEFT)

        split_tab.columnconfigure(1, weight=1)

        # ------------------------------------------------------------------
        # Tab 2: Optimize TMX
        # ------------------------------------------------------------------
        optimize_tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(optimize_tab, text="Optimize TMX")

        opt_lang_box = ttk.LabelFrame(optimize_tab, text="Profile and language pair", padding=3)
        opt_lang_box.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 2))
        ttk.Label(opt_lang_box, text="Optimization profile:").grid(row=0, column=0, sticky="w")
        profile_row = ttk.Frame(opt_lang_box)
        profile_row.grid(row=0, column=1, columnspan=2, sticky="w", padx=6)
        profile_button = ttk.Menubutton(profile_row, textvariable=self.opt_profile_display, width=24)
        profile_button.pack(side="left")
        profile_menu = tk.Menu(profile_button, tearoff=False)
        profile_button["menu"] = profile_menu
        self.profile_button = profile_button
        self.profile_menu = profile_menu
        self.rebuild_profile_menu()
        self.profile_menu_tooltip = MenuItemToolTip(
            profile_menu,
            text_func=self.get_profile_description,
            delay_ms=2000,
        )
        ttk.Button(profile_row, text="Apply profile", command=self.apply_optimization_profile).pack(side="left", padx=(6, 0))
        ttk.Button(profile_row, text="Save as preset", command=self.save_current_optimization_preset).pack(side="left", padx=(6, 0))
        ttk.Button(profile_row, text="Delete preset", command=self.delete_selected_optimization_preset).pack(side="left", padx=(6, 0))
        ttk.Button(profile_row, text="Import presets", command=self.import_optimization_presets).pack(side="left", padx=(6, 0))
        ttk.Label(opt_lang_box, text="Source langs:").grid(row=1, column=0, sticky="w", pady=(1, 0))
        ttk.Entry(opt_lang_box, textvariable=self.source_langs).grid(row=1, column=1, sticky="ew", padx=6, pady=(1, 0))
        ttk.Label(opt_lang_box, text="Target langs:").grid(row=2, column=0, sticky="w", pady=(1, 0))
        ttk.Entry(opt_lang_box, textvariable=self.target_langs).grid(row=2, column=1, sticky="ew", padx=6, pady=(1, 0))
        ttk.Checkbutton(
            opt_lang_box,
            text="Keep only selected source-target language pair",
            variable=self.opt_keep_selected_pair,
        ).grid(row=3, column=1, columnspan=2, sticky="w", padx=6, pady=(2, 0))
        norm_line = ttk.Frame(opt_lang_box)
        norm_line.grid(row=4, column=1, columnspan=2, sticky="ew", padx=6, pady=(2, 0))
        ttk.Checkbutton(norm_line, text="Normalize source language code to:", variable=self.opt_normalize_source_lang).pack(side=tk.LEFT)
        ttk.Entry(norm_line, textvariable=self.opt_normalize_source_code, width=10).pack(side=tk.LEFT, padx=(4, 12))
        ttk.Checkbutton(norm_line, text="Normalize target language code to:", variable=self.opt_normalize_target_lang).pack(side=tk.LEFT)
        ttk.Entry(norm_line, textvariable=self.opt_normalize_target_code, width=10).pack(side=tk.LEFT, padx=(4, 0))
        opt_lang_box.columnconfigure(1, weight=1)

        cleanup_box = ttk.LabelFrame(optimize_tab, text="Basic cleanup options", padding=3)
        cleanup_box.grid(row=1, column=0, sticky="nsew", pady=(0, 2))
        ttk.Checkbutton(
            cleanup_box,
            text="Remove TU without source language",
            variable=self.opt_remove_missing_source,
        ).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(
            cleanup_box,
            text="Remove TU without target language",
            variable=self.opt_remove_missing_target,
        ).grid(row=1, column=0, sticky="w", pady=(1, 0))
        ttk.Checkbutton(
            cleanup_box,
            text="Remove TU with empty source or target segment",
            variable=self.opt_remove_empty,
        ).grid(row=2, column=0, sticky="w", pady=(1, 0))
        ttk.Checkbutton(
            cleanup_box,
            text="Remove TU with tag-only source or target segment",
            variable=self.opt_remove_tag_only,
        ).grid(row=3, column=0, sticky="w", pady=(1, 0))
        ttk.Checkbutton(
            cleanup_box,
            text="Remove TU with XML parse errors / malformed TU",
            variable=self.opt_remove_xml_errors,
        ).grid(row=4, column=0, sticky="w", pady=(1, 0))

        dedupe_box = ttk.LabelFrame(optimize_tab, text="Duplicates and short/noisy segments", padding=3)
        dedupe_box.grid(row=1, column=1, columnspan=2, sticky="nsew", padx=(6, 0), pady=(0, 2))
        ttk.Checkbutton(
            dedupe_box,
            text="Remove exact duplicate source-target pairs; keep the first occurrence",
            variable=self.opt_remove_duplicates,
        ).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(
            dedupe_box,
            text="Warn about short/noisy source-target pairs",
            variable=self.opt_warn_noisy,
        ).grid(row=1, column=0, sticky="w", pady=(1, 0))
        ttk.Checkbutton(
            dedupe_box,
            text="Remove pairs matching the noisy segment list",
            variable=self.opt_remove_noisy,
        ).grid(row=2, column=0, sticky="w", pady=(1, 0))
        ttk.Checkbutton(
            dedupe_box,
            text="Remove one-character or punctuation-only pairs",
            variable=self.opt_remove_one_char_punct,
        ).grid(row=3, column=0, sticky="w", pady=(1, 0))
        noisy_line = ttk.Frame(dedupe_box)
        noisy_line.grid(row=4, column=0, sticky="ew", pady=(2, 0))
        ttk.Label(noisy_line, text="Noisy segment list:").pack(side=tk.LEFT)
        ttk.Entry(noisy_line, textvariable=self.opt_noisy_segments, width=55).pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)

        noisy_rules_line = ttk.Frame(dedupe_box)
        noisy_rules_line.grid(row=5, column=0, sticky="ew", pady=(2, 0))
        ttk.Label(noisy_rules_line, text="List match:").pack(side=tk.LEFT)
        ttk.Combobox(
            noisy_rules_line,
            textvariable=self.opt_noisy_match_mode,
            values=(self.noisy_mode_label("Both source and target"), self.noisy_mode_label("Either source or target")),
            state="readonly",
            width=24,
        ).pack(side=tk.LEFT, padx=(6, 14))
        ttk.Checkbutton(
            noisy_rules_line,
            text="Warn if both texts are <=",
            variable=self.opt_warn_min_length,
        ).pack(side=tk.LEFT)
        ttk.Entry(noisy_rules_line, textvariable=self.opt_min_text_length, width=4).pack(side=tk.LEFT, padx=4)
        ttk.Label(noisy_rules_line, text="chars").pack(side=tk.LEFT)
        dedupe_box.columnconfigure(0, weight=1)

        inline_box = ttk.LabelFrame(optimize_tab, text="Inline tags", padding=3)
        inline_box.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 2))
        ttk.Checkbutton(
            inline_box,
            text="Report inline-tag mismatch between source and target",
            variable=self.opt_report_inline_tag_mismatch,
        ).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(
            inline_box,
            text="Strip inline tags only from mismatched TUs",
            variable=self.opt_strip_mismatched_inline_tags,
        ).grid(row=0, column=1, sticky="w", padx=(18, 0))
        ttk.Checkbutton(
            inline_box,
            text="Strip inline tags from all kept TUs",
            variable=self.opt_strip_all_inline_tags,
        ).grid(row=1, column=0, sticky="w", pady=(1, 0))

        opt_actions = ttk.Frame(optimize_tab)
        opt_actions.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 1))
        ttk.Checkbutton(opt_actions, text="Dry run (report only)", variable=self.opt_dry_run).pack(side=tk.RIGHT)
        self.optimize_btn = ttk.Button(opt_actions, text="Optimize TMX", command=self.start_optimize)
        self.optimize_btn.pack(side=tk.LEFT)
        ttk.Button(opt_actions, text="Open optimized TMX", command=self.open_optimized_tmx).pack(side=tk.LEFT, padx=6)
        ttk.Button(opt_actions, text="Open report", command=self.open_last_report).pack(side=tk.LEFT)
        ttk.Button(opt_actions, text="Open output folder", command=self.open_output_folder).pack(side=tk.LEFT, padx=6)

        opt_view_actions = ttk.Frame(optimize_tab)
        opt_view_actions.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 0))
        ttk.Button(opt_view_actions, text="View removed TUs", command=self.view_removed_tus).pack(side=tk.LEFT)
        ttk.Button(opt_view_actions, text="View duplicates", command=self.view_duplicate_tus).pack(side=tk.LEFT, padx=6)
        ttk.Button(opt_view_actions, text="View noisy warnings", command=self.view_noisy_warnings).pack(side=tk.LEFT)
        ttk.Button(opt_view_actions, text="View inline-tag warnings", command=self.view_inline_tag_warnings).pack(side=tk.LEFT, padx=6)
        ttk.Button(opt_view_actions, text="View changed TUs", command=self.view_changed_tus).pack(side=tk.LEFT)
        ttk.Button(opt_view_actions, text="Export result groups", command=self.export_result_groups_dialog).pack(side=tk.LEFT, padx=6)

        optimize_tab.columnconfigure(0, weight=1)
        optimize_tab.columnconfigure(1, weight=1)

        # ------------------------------------------------------------------
        # Tab 3: Compare TMX
        # ------------------------------------------------------------------
        compare_tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(compare_tab, text="Compare TMX")

        ttk.Label(
            compare_tab,
            text="Compare two TMX files or two sets of TMX files using the current Source langs and Target langs settings. This is useful for comparing an original TMX with an optimized TMX, two exports, or two versions of the same base.",
            wraplength=900,
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))

        files_a_box = ttk.LabelFrame(compare_tab, padding=5)
        files_a_box.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 4))
        ttk.Label(files_a_box, text="TMX A:").grid(row=0, column=0, sticky="w")
        ttk.Label(files_a_box, textvariable=self.compare_files_a_label).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(files_a_box, text="Select TMX...", command=self.choose_compare_files_a).grid(row=0, column=2)
        ttk.Button(files_a_box, text="Clear", command=self.clear_compare_files_a).grid(row=0, column=3, padx=(6, 0))
        files_a_box.columnconfigure(1, weight=1)

        files_b_box = ttk.LabelFrame(compare_tab, padding=5)
        files_b_box.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 4))
        ttk.Label(files_b_box, text="TMX B:").grid(row=0, column=0, sticky="w")
        ttk.Label(files_b_box, textvariable=self.compare_files_b_label).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(files_b_box, text="Select TMX...", command=self.choose_compare_files_b).grid(row=0, column=2)
        ttk.Button(files_b_box, text="Clear", command=self.clear_compare_files_b).grid(row=0, column=3, padx=(6, 0))
        files_b_box.columnconfigure(1, weight=1)

        compare_options = ttk.LabelFrame(compare_tab, text="Compare options", padding=5)
        compare_options.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 4))
        ttk.Label(compare_options, text="If one TMX is selected on each side, files are compared directly even if their file names differ. If multiple TMX files are selected, matching uses file name.", foreground="#555555", wraplength=900).grid(row=0, column=0, sticky="w")

        compare_actions = ttk.Frame(compare_tab)
        compare_actions.grid(row=4, column=0, columnspan=3, sticky="w", pady=(2, 0))
        self.compare_btn = ttk.Button(compare_actions, text="Compare TMX", command=self.start_compare)
        self.compare_btn.pack(side=tk.LEFT)
        ttk.Button(compare_actions, text="Open report", command=self.open_last_report).pack(side=tk.LEFT, padx=6)
        ttk.Button(compare_actions, text="Open output folder", command=self.open_output_folder).pack(side=tk.LEFT)

        compare_tab.columnconfigure(1, weight=1)

        # ------------------------------------------------------------------
        # Shared progress and log area
        # ------------------------------------------------------------------
        status_frame = ttk.Frame(main)
        status_frame.pack(fill=tk.X, pady=0)
        self.overall_label = ttk.Label(status_frame, text=self.tr("Overall: idle"))
        self.overall_label.pack(side=tk.LEFT)

        progress_frame = ttk.Frame(main)
        progress_frame.pack(fill=tk.X, pady=0)
        style = ttk.Style(self.root)
        style.configure("Thin.Horizontal.TProgressbar", thickness=1, borderwidth=0, troughrelief="flat")
        self.progress = ttk.Progressbar(progress_frame, mode="determinate", style="Thin.Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, pady=0, ipady=0)

        summary_frame = ttk.LabelFrame(main, text="Result summary", padding=1)
        summary_frame.pack(fill=tk.X, pady=(1, 1))
        self.result_summary_label = ttk.Label(
            summary_frame,
            textvariable=self.result_summary,
            justify=tk.LEFT,
            wraplength=940,
        )
        self.result_summary_label.pack(fill=tk.X, anchor="w")

        log_frame = ttk.LabelFrame(main, text="Log", padding=3)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(log_frame, wrap="word", height=24)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scroll.set)

    def show_help(self):
        win = tk.Toplevel(self.root)
        win.title(self.tr("Help"))
        help_win_width = 900
        help_win_height = 640
        win.geometry(f"{help_win_width}x{help_win_height}")
        win.transient(self.root)
        apply_window_icon(win)

        container = ttk.Frame(win, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text=self.tr("TMX Optimization and Splitting Tool Help"),
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        help_topics = {
            "Overview": """TMX Optimization and Splitting Tool prepares TMX translation memories for safer CAT import.

Main areas:
- Split / Analyze: inspect TMX files and split large databases safely.
- Optimize TMX: create cleaned TMX copies using selected rules and profiles.
- Compare TMX: compare two TMX files or two sets of TMX files.
- Export problem/result groups: export selected diagnostic groups for review or testing.
- Settings / About: default settings, output paths, and program information.

Original TMX files are never modified. New TMX files and XLSX reports are created in the selected output folder.""",
            "Safety principle": """Original TMX files are treated as read-only input.

Safe Split preserves original TU content whenever possible and splits only on <tu> boundaries.

Optimize TMX creates new cleaned files in the output folder. Potentially risky actions, such as duplicate removal, noisy pair removal, language normalization, or inline-tag stripping, show warnings before processing.

Dry run can be used to preview optimization results without creating an optimized TMX.""",
            "Input files": """Use Add TMX files to select one or more TMX files.

Remove selected removes highlighted files from the list. Clear removes all selected files from the list.

Most operations support multiple files. For multi-file operations, TOST can also create пакетные сводные отчеты.""",
            "Output folder": """Output folder is where TOST saves split files, optimized TMX files, exported groups, and XLSX reports.

The original TMX files remain unchanged.

Open output folder opens the selected output directory in the operating system file manager.""",
            "Source and target languages": """Source langs and Target langs define which language codes should be treated as source and target.

Use comma-separated variants. Example:
Source langs: en,en-us,en-gb
Target langs: ru,ru-ru

This is useful when TMX files contain mixed language-code variants such as en, en-US, en-GB, ru, and ru-RU.""",
            "Safe Split": """Safe Split divides TMX files into smaller valid TMX files.

It can split by file size or by TU count. It does not rewrite segment text, remove tags, or normalize language codes.

Safe Split is intended for situations where the original TU content should be preserved as much as possible.""",
            "Split by file size": """Split by file size creates output parts close to the specified size in MB.

TOST still writes complete <tu> blocks only. It does not cut a translation unit in the middle.

A single very large TU may make one part larger than the requested limit.""",
            "Split by TU count": """Split by TU count creates a new output part after the selected number of written <tu> blocks.

This is useful when a CAT system is sensitive to the number of translation units rather than file size.

TU count mode counts written TU blocks only.""",
            "Analyze": """Analyze checks selected TMX files and creates XLSX reports.

It reports:
- total TU;
- potentially importable TU;
- problem TU;
- total detected issues;
- error counts;
- language statistics;
- problem TU details with raw XML.

Use Analyze before optimization to understand what is inside the database.""",
            "Analyze before split": """Analyze TMX before splitting and create XLSX report runs analysis before Safe Split.

This helps you see whether the input database already contains missing languages, empty segments, tag-only segments, XML parse problems, or language-code variants.""",
            "Post-check after split": """Post-check created files after splitting analyzes the created split files after Safe Split.

It confirms how many files were created and counts total TU, potentially importable TU, problem TU, and detected issues in the output parts.

The post-check creates a separate XLSX report.""",
            "Potentially importable TU": """Potentially importable TU is the number of translation units that contain the selected source and target languages and have no detected blocking issues.

It is an estimate. A specific CAT system may still reject some units for its own internal reasons.""",
            "Problem TU and detected issues": """Problem TU is the number of translation units that have at least one detected problem.

Total detected issues can be higher than Problem TU because one TU can have several issues.

Example: one TU can have both a tag-only source segment and a tag-only target segment.""",
            "Language statistics": """Language statistics show which xml:lang values are present in the TMX.

The report includes counts such as TUV count, TU count, non-empty segments, empty segments, and tag-only segments for each language code.

This helps identify mixed variants such as en, en-US, en-GB, ru, and ru-RU.""",
            "View problem TUs": """View problem TUs opens a table with problem translation units from the latest analysis.

When you select a row, TOST shows the original raw TU XML below the table.

This makes it possible to inspect problematic units without opening the source TMX manually.""",
            "Open report": """Open report opens the latest relevant XLSX report created by Analyze, Optimize TMX, Compare TMX, Export, or post-check operations.

If no report has been created yet, run the corresponding operation first.""",
            "Open optimized TMX": """Open optimized TMX opens the latest optimized TMX file created by Optimize TMX.

This button is not available for Dry run results because Dry run creates a report only and does not create an optimized TMX.""",
            "Optimize TMX": """Optimize TMX creates a cleaned copy of the selected TMX files.

Depending on selected options, it can remove missing, empty, tag-only, duplicate, noisy, one-character, punctuation-only, and malformed units.

It can also normalize language codes, keep only the selected language pair, report inline-tag mismatches, and strip inline tags if requested.""",
            "Basic cleanup options": """Basic cleanup options remove translation units that are likely to cause import problems.

Available options:
- remove TU without source language;
- remove TU without target language;
- remove TU with empty source or target segment;
- remove TU with tag-only source or target segment;
- remove TU with XML parse errors or malformed TU.

Removed TU blocks are recorded in the optimization report.""",
            "Tag-only TU": """A tag-only segment contains inline tags but no real text.

Example: <seg><ph x=\"1\"/></seg>

Such units are usually not useful for translation memory import and can be removed by Optimize TMX.""",
            "Duplicate removal": """Remove exact duplicate source-target pairs keeps the first occurrence and removes later duplicate pairs.

Duplicate detection is based on the selected source and target segment pair.

Removed duplicates are written to the Removed duplicates sheet and can be reviewed or exported.""",
            "Noisy segment rules": """Noisy rules detect short or technical-looking pairs such as punctuation-only entries.

Available controls include:
- a custom Noisy segment list;
- list match mode: both source and target, or either source or target;
- warnings for pairs where both texts are shorter than a selected character limit;
- optional removal of pairs matching the noisy list;
- optional removal of one-character or punctuation-only pairs.

Review reports before using aggressive removal because short UI strings can sometimes be valid translations.""",
            "Inline tags": """Inline tags are placeholders or formatting markers inside a segment, such as <ph>, <bpt>, <ept>, <it>, <ut>, <hi>, and <sub>.

They can represent formatting, variables, links, line breaks, or other non-text elements.""",
            "Inline-tag mismatch": """Inline-tag mismatch means the source and target do not have the same inline-tag sequence.

By default TOST reports mismatches but does not remove the TU.

The Inline-tag warnings result group stores tag sequences, previews, and raw TU XML for review.""",
            "Strip inline tags": """Strip inline tags removes inline tags from kept TUs.

Available options:
- strip inline tags only from mismatched TUs;
- strip inline tags from all kept TUs.

This changes segment content. Use it only when the target CAT system rejects tagged units or when you intentionally want a plain-text memory.

Changed TUs are recorded in the report with before and after XML.""",
            "Language normalization": """Language normalization rewrites xml:lang values in the optimized output.

For example, source en and target ru can be written as en-US and ru-RU.

Segment text is not translated or changed by normalization. Only the language code attribute is changed.

The target normalization codes are user-defined in the Normalize source language code to and Normalize target language code to fields.""",
            "Keep selected language pair": """Keep only selected source-target language pair removes extra language variants from optimized output.

TOST finds source and target TUVs using Source langs and Target langs. If this option is enabled, only the selected source and target TUVs are kept in the output TU.

This is useful for preparing a clean bilingual TMX from a multilingual or mixed-code TMX.""",
            "Optimization profiles": """Optimization profiles are presets that set optimization options.

Built-in profiles:
- General CAT-safe: conservative cleanup.
- Strict import: stronger cleanup for stricter import workflows.
- Smartcat-oriented: uses Smartcat-like strict import expectations as a practical reference, but the logic is general and can help with other CAT systems too.
- Custom: keeps your current manual settings.

Apply profile applies the selected profile to the current controls.""",
            "User presets": """User presets let you save, delete, and import your own optimization settings.

Save as preset stores the current optimization controls under a custom name.
Delete preset removes a user preset.
Import presets imports presets from JSON files.

Built-in profiles cannot be overwritten or deleted. Imported presets are stored in tost_settings.json and become available in the same profile menu.""",
            "Dry run": """Dry run creates a report only and does not create an optimized TMX.

Use it before aggressive cleanup to see what would be removed or changed.

Dry run is useful for testing duplicate removal, noisy pair removal, language normalization, selected language-pair filtering, and inline-tag stripping.""",
            "Result summary": """Result summary shows compact before/after metrics after Analyze, Safe Split, or Optimize TMX.

For optimization, it shows input status, output post-check status, removed counts, duplicate counts, noisy counts, one-character/punctuation removals, and changed TU counts.""",
            "View optimization results": """After Optimize TMX, TOST can display result groups directly in the program.

Available viewers:
- View removed TUs;
- View duplicates;
- View noisy warnings;
- View inline-tag warnings;
- View changed TUs.

Selecting a row shows raw XML or detailed information below the table.""",
            "Compare TMX": """Compare TMX compares two TMX files or two sets of TMX files using the current source and target language settings.

If one file is selected on each side, they are compared directly even if names differ.

If multiple files are selected, TOST matches files by filename.

The compare report includes summary metrics, per-file metrics, matched files, файлы только в A, файлы только в B, and language statistics for both sides.""",
            "Export problem/result groups": """Export selected problem or optimization result groups to XLSX, Raw XML TXT, or TMX.

Groups include:
- Problem TUs;
- Removed TUs;
- Removed duplicates;
- Noisy warnings;
- Inline-tag warnings;
- Changed TUs.

Use Export problem TUs after Analyze. Use Export result groups after Optimize TMX.""",
            "Export formats": """XLSX report creates a spreadsheet with all available columns.

Raw XML TXT writes original raw <tu> XML blocks to a text file for manual inspection.

TMX file wraps selected TU blocks into a valid TMX file for testing or re-importing selected units.""",
            "Batch summary reports": """When multiple files are processed, TOST can create пакетные сводные отчеты.

Batch reports summarize totals across all processed files and also list per-file metrics.

They are useful for large translation memories split into many parts.""",
            "Reports": """TOST creates XLSX reports for analysis, optimization, dry run, split post-check, compare, export, and batch operations.

Reports are intended to make every removal, warning, or change auditable.

Typical sheets include Summary, Error counts, Language statistics, Problems, Removed TUs, Removed duplicates, Noisy warnings, Inline-tag warnings, Changed TUs, and batch/file summaries.""",
            "Settings / About": """Settings / About contains default output folder, default split settings, default language variants, default prefix, and default analysis/post-check settings.

Save writes settings to tost_settings.json.
Reset restores defaults.
Open settings folder opens the folder containing the settings file.

TOST also restores the last selected tab, window size, and export format after restart. Input TMX file lists are intentionally not restored.

About explains the basic safety principle and application version.""",
            "Safety checks and warnings": """Before running operations, TOST checks required input and settings.

Examples:
- selected TMX files;
- output folder availability;
- valid split size or TU count;
- non-empty source and target language lists;
- non-conflicting source and target language sets;
- valid language normalization codes.

Risky optimization actions show a confirmation warning before processing.""",
        }

        if self.is_ru():
            help_topics = {HELP_TOPICS_RU.get(k, (k, v))[0]: HELP_TOPICS_RU.get(k, (k, v))[1] for k, v in help_topics.items()}

        body = ttk.Frame(container)
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.LabelFrame(body, text=self.tr("Function"), padding=6)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        topic_list = tk.Listbox(left, width=30, height=24, exportselection=False)
        topic_scroll = ttk.Scrollbar(left, orient="vertical", command=topic_list.yview)
        topic_list.configure(yscrollcommand=topic_scroll.set)
        topic_list.pack(side=tk.LEFT, fill=tk.Y)
        topic_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        right = ttk.LabelFrame(body, text=self.tr("Description"), padding=6)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        title_var = tk.StringVar(value="")
        ttk.Label(right, textvariable=title_var, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))

        text_frame = ttk.Frame(right)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_widget = tk.Text(text_frame, wrap="word", height=26, borderwidth=1, relief="solid")
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        topics = list(help_topics.keys())
        for topic in topics:
            topic_list.insert(tk.END, topic)

        def show_topic(event=None):
            selection = topic_list.curselection()
            if not selection:
                return
            topic = topics[selection[0]]
            title_var.set(topic)
            text_widget.configure(state="normal")
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", help_topics[topic])
            text_widget.configure(state="disabled")

        topic_list.bind("<<ListboxSelect>>", show_topic)
        topic_list.selection_set(0)
        topic_list.activate(0)
        show_topic()

        ttk.Button(container, text=self.tr("Close"), command=win.destroy).pack(anchor="e", pady=(8, 0))

        def center_help_window():
            try:
                win.update_idletasks()
                self.root.update_idletasks()

                width = max(help_win_width, win.winfo_width())
                height = max(help_win_height, win.winfo_height())

                root_x = self.root.winfo_rootx()
                root_y = self.root.winfo_rooty()
                root_w = self.root.winfo_width()
                root_h = self.root.winfo_height()

                x = root_x + max(0, (root_w - width) // 2)
                y = root_y + max(0, (root_h - height) // 2)

                screen_w = win.winfo_screenwidth()
                screen_h = win.winfo_screenheight()
                x = max(0, min(x, screen_w - width))
                y = max(0, min(y, screen_h - height))

                win.geometry(f"{int(width)}x{int(height)}+{int(x)}+{int(y)}")
            except Exception:
                pass

        win.after_idle(center_help_window)

    def on_tab_changed(self, _event=None):
        try:
            self._saved_selected_tab_index = self.notebook.index(self.notebook.select())
        except Exception:
            pass

    def restore_ui_state(self):
        # Restore only lightweight UI state. Input TMX file lists are intentionally not restored.
        try:
            if self._saved_window_geometry:
                # Apply only size, not saved screen coordinates, to avoid reopening off-screen.
                geom = str(self._saved_window_geometry)
                size_part = geom.split("+")[0]
                if "x" in size_part:
                    w, h = size_part.split("x", 1)
                    if w.isdigit() and h.isdigit() and int(w) >= 800 and int(h) >= 650:
                        self.root.geometry(size_part)
        except Exception:
            pass
        try:
            tabs = self.notebook.tabs()
            idx = int(self._saved_selected_tab_index)
            if 0 <= idx < len(tabs):
                self.notebook.select(tabs[idx])
        except Exception:
            pass

    def on_close(self):
        self.save_settings(silent=True)
        try:
            self.root.destroy()
        except Exception:
            pass

    def show_settings_about(self):
        win = tk.Toplevel(self.root)
        win.title(self.tr("Settings / About"))
        # Keep the Settings / About window compact. The final width is
        # recalculated after layout so the right edge is anchored about
        # 30 px after the Browse button in both UI languages.
        settings_win_width = 610 if self.is_ru() else 555
        win.geometry(f"{settings_win_width}x560")
        win.minsize(520, 520)
        win.transient(self.root)
        apply_window_icon(win)

        container = ttk.Frame(win, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        settings_box = ttk.LabelFrame(container, text=self.tr("Default settings"), padding=8)
        settings_box.pack(fill=tk.X)

        ttk.Label(settings_box, text=self.tr("Interface language:")).grid(row=0, column=0, sticky="w")
        lang_row = ttk.Frame(settings_box)
        lang_row.grid(row=0, column=1, columnspan=2, sticky="w", padx=(6, 0))
        ttk.Combobox(
            lang_row,
            textvariable=self.ui_language,
            values=("English", "Русский"),
            state="readonly",
            width=16,
        ).pack(side=tk.LEFT)
        self.language_restart_note = ttk.Label(
            lang_row,
            text=self.tr("Note: Restart TOST to apply language settings"),
            foreground="#555555",
            wraplength=245 if self.is_ru() else 195,
            justify=tk.LEFT,
        )
        self.language_restart_note.pack(side=tk.LEFT, padx=(4, 0))

        ttk.Label(settings_box, text=self.tr("Default output folder:")).grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(settings_box, textvariable=self.output_dir, width=46).grid(row=1, column=1, sticky="w", padx=(6, 0), pady=(6, 0))
        self.settings_browse_btn = ttk.Button(settings_box, text=self.tr("Browse..."), command=self.choose_output)
        self.settings_browse_btn.grid(row=1, column=2, sticky="w", padx=(6, 0), pady=(6, 0))

        ttk.Label(settings_box, text=self.tr("Default part size, MB:")).grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(settings_box, textvariable=self.max_mb, width=12).grid(row=2, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(settings_box, text=self.tr("Default part TU count:")).grid(row=3, column=0, sticky="w")
        ttk.Entry(settings_box, textvariable=self.part_tu_count, width=12).grid(row=3, column=1, sticky="w", padx=6)

        ttk.Label(settings_box, text=self.tr("Default split mode:")).grid(row=4, column=0, sticky="w", pady=4)
        ttk.Radiobutton(settings_box, text=self.tr("By MB"), variable=self.split_mode, value="mb").grid(row=4, column=1, sticky="w", padx=6, pady=4)
        ttk.Radiobutton(settings_box, text=self.tr("By TU count"), variable=self.split_mode, value="tu").grid(row=4, column=1, sticky="w", padx=(90, 6), pady=4)

        ttk.Label(settings_box, text=self.tr("Default prefix:")).grid(row=5, column=0, sticky="w")
        ttk.Entry(settings_box, textvariable=self.prefix, width=12).grid(row=5, column=1, sticky="w", padx=6)

        ttk.Label(settings_box, text=self.tr("Default source langs:")).grid(row=6, column=0, sticky="w", pady=4)
        ttk.Entry(settings_box, textvariable=self.source_langs, width=46).grid(row=6, column=1, columnspan=2, sticky="w", padx=6, pady=4)

        ttk.Label(settings_box, text=self.tr("Default target langs:")).grid(row=7, column=0, sticky="w")
        ttk.Entry(settings_box, textvariable=self.target_langs, width=46).grid(row=7, column=1, columnspan=2, sticky="w", padx=6)

        ttk.Checkbutton(
            settings_box,
            text=self.tr("Analyze TMX before splitting by default"),
            variable=self.analyze_before_split,
        ).grid(row=8, column=1, columnspan=2, sticky="w", padx=6, pady=(6, 0))
        ttk.Checkbutton(
            settings_box,
            text=self.tr("Post-check created files after splitting by default"),
            variable=self.post_check_after_split,
        ).grid(row=9, column=1, columnspan=2, sticky="w", padx=6, pady=(1, 0))

        settings_actions = ttk.Frame(settings_box)
        settings_actions.grid(row=10, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Button(settings_actions, text=self.tr("Reset"), command=self.reset_settings).pack(side=tk.LEFT)
        ttk.Button(settings_actions, text=self.tr("Open settings folder"), command=self.open_settings_folder).pack(side=tk.LEFT, padx=(6, 0))
        self.save_settings_btn = ttk.Button(settings_box, text=self.tr("Apply"), command=self.save_settings)
        self.save_settings_btn.grid(row=10, column=2, sticky="w", padx=(6, 0), pady=(10, 0))

        settings_box.columnconfigure(1, weight=0)
        settings_box.columnconfigure(2, weight=0)

        about_box = ttk.LabelFrame(container, text=self.tr("About"), padding=8)
        about_box.pack(fill=tk.BOTH, expand=True, pady=10)
        about_text_en = (
            f"{APP_TITLE}\n"
            "A safe TMX preparation utility for CAT import workflows.\n"
            "Current principle: preserve original TU content as much as possible and split only on <tu> boundaries.\n"
            "Original TMX files are read-only input and are never modified.\n\n"
            "Smartcat is used as one strict import reference point, but the optimization workflow is intended to be CAT-system neutral."
        )
        about_text_ru = (
            f"{APP_TITLE}\n"
            "Безопасная утилита подготовки TMX к импорту в CAT-системы.\n"
            "Основной принцип: по возможности сохранять исходное содержимое TU и разделять файл только по границам <tu>.\n"
            "Исходные TMX-файлы используются только для чтения и никогда не изменяются.\n\n"
            "Smartcat используется как один из ориентиров строгого импорта, но workflow оптимизации остается нейтральным к CAT-системам."
        )
        about_label = ttk.Label(
            about_box,
            text=about_text_ru if self.is_ru() else about_text_en,
            wraplength=585,
            justify=tk.LEFT,
        )
        about_label.pack(anchor="w")

        def center_settings_window(width=None, height=560):
            try:
                win.update_idletasks()
                self.root.update_idletasks()

                if width is None:
                    width = win.winfo_width()
                height = max(height, win.winfo_height())

                root_x = self.root.winfo_rootx()
                root_y = self.root.winfo_rooty()
                root_w = self.root.winfo_width()
                root_h = self.root.winfo_height()

                x = root_x + max(0, (root_w - width) // 2)
                y = root_y + max(0, (root_h - height) // 2)

                # Keep the dialog visible on screen even if the main window is near an edge.
                screen_w = win.winfo_screenwidth()
                screen_h = win.winfo_screenheight()
                x = max(0, min(x, screen_w - width))
                y = max(0, min(y, screen_h - height))

                win.geometry(f"{int(width)}x{int(height)}+{int(x)}+{int(y)}")
            except Exception:
                pass

        def adjust_settings_window_width():
            try:
                win.update_idletasks()
                margin = 30

                # The Browse button is the visual anchor requested for this dialog.
                # Compute the final window width from its actual on-screen right edge,
                # not from the requested width of longer labels or the About text.
                browse_right = (
                    self.settings_browse_btn.winfo_rootx()
                    - win.winfo_rootx()
                    + self.settings_browse_btn.winfo_width()
                )
                desired_width = int(browse_right + margin)

                # Keep Apply visually under Browse and inside the same right edge.
                # Do not let Apply expand the window; it should align to the existing layout.
                desired_width = max(desired_width, 520)

                if hasattr(self, "language_restart_note"):
                    self.language_restart_note.configure(wraplength=245 if self.is_ru() else 190)
                about_label.configure(wraplength=max(380, desired_width - 55))

                win.geometry(f"{desired_width}x560")
                win.minsize(desired_width, 520)

                # Re-check once after geometry is applied. Tk can slightly change widget
                # sizes after the first resize; this keeps the Browse-to-edge gap stable.
                win.update_idletasks()
                browse_right_2 = (
                    self.settings_browse_btn.winfo_rootx()
                    - win.winfo_rootx()
                    + self.settings_browse_btn.winfo_width()
                )
                corrected_width = int(browse_right_2 + margin)
                if abs(corrected_width - desired_width) > 2:
                    corrected_width = max(corrected_width, 520)
                    about_label.configure(wraplength=max(380, corrected_width - 55))
                    win.geometry(f"{corrected_width}x560")
                    win.minsize(corrected_width, 520)
                    desired_width = corrected_width

                center_settings_window(desired_width, 560)
            except Exception:
                pass

        win.after_idle(adjust_settings_window_width)

    def load_settings(self):
        path = get_settings_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.ui_language.set(data.get("ui_language", self.ui_language.get()) if data.get("ui_language") in ("English", "Русский", "Russian") else self.ui_language.get())
                if self.ui_language.get() == "Russian":
                    self.ui_language.set("Русский")
                self.output_dir.set(data.get("output_dir", self.output_dir.get()))
                self.max_mb.set(data.get("max_mb", self.max_mb.get()))
                self.part_tu_count.set(data.get("part_tu_count", self.part_tu_count.get()))
                self.split_mode.set(data.get("split_mode", self.split_mode.get()) if data.get("split_mode") in ("mb", "tu") else self.split_mode.get())
                self.post_check_after_split.set(bool(data.get("post_check_after_split", self.post_check_after_split.get())))
                self.prefix.set(data.get("prefix", self.prefix.get()) or DEFAULT_PREFIX)
                self.source_langs.set(data.get("source_langs", self.source_langs.get()))
                self.target_langs.set(data.get("target_langs", self.target_langs.get()))
                self.analyze_before_split.set(bool(data.get("analyze_before_split", self.analyze_before_split.get())))
                self.opt_remove_missing_source.set(bool(data.get("opt_remove_missing_source", self.opt_remove_missing_source.get())))
                self.opt_remove_missing_target.set(bool(data.get("opt_remove_missing_target", self.opt_remove_missing_target.get())))
                self.opt_remove_empty.set(bool(data.get("opt_remove_empty", self.opt_remove_empty.get())))
                self.opt_remove_tag_only.set(bool(data.get("opt_remove_tag_only", self.opt_remove_tag_only.get())))
                self.opt_remove_xml_errors.set(bool(data.get("opt_remove_xml_errors", self.opt_remove_xml_errors.get())))
                self.opt_remove_duplicates.set(bool(data.get("opt_remove_duplicates", self.opt_remove_duplicates.get())))
                self.opt_warn_noisy.set(bool(data.get("opt_warn_noisy", self.opt_warn_noisy.get())))
                self.opt_remove_noisy.set(bool(data.get("opt_remove_noisy", self.opt_remove_noisy.get())))
                self.opt_remove_one_char_punct.set(bool(data.get("opt_remove_one_char_punct", self.opt_remove_one_char_punct.get())))
                self.opt_noisy_segments.set(data.get("opt_noisy_segments", self.opt_noisy_segments.get()))
                mode = data.get("opt_noisy_match_mode", self.opt_noisy_match_mode.get())
                mode = self.noisy_mode_key(mode)
                if mode in ("Both source and target", "Either source or target"):
                    self.opt_noisy_match_mode.set(self.noisy_mode_label(mode) if self.is_ru() else mode)
                self.opt_warn_min_length.set(bool(data.get("opt_warn_min_length", self.opt_warn_min_length.get())))
                self.opt_min_text_length.set(str(data.get("opt_min_text_length", self.opt_min_text_length.get()) or "2"))
                self.opt_report_inline_tag_mismatch.set(bool(data.get("opt_report_inline_tag_mismatch", self.opt_report_inline_tag_mismatch.get())))
                self.opt_strip_mismatched_inline_tags.set(bool(data.get("opt_strip_mismatched_inline_tags", self.opt_strip_mismatched_inline_tags.get())))
                self.opt_strip_all_inline_tags.set(bool(data.get("opt_strip_all_inline_tags", self.opt_strip_all_inline_tags.get())))
                self.opt_keep_selected_pair.set(bool(data.get("opt_keep_selected_pair", self.opt_keep_selected_pair.get())))
                self.opt_normalize_source_lang.set(bool(data.get("opt_normalize_source_lang", self.opt_normalize_source_lang.get())))
                self.opt_normalize_target_lang.set(bool(data.get("opt_normalize_target_lang", self.opt_normalize_target_lang.get())))
                self.opt_normalize_source_code.set(data.get("opt_normalize_source_code", self.opt_normalize_source_code.get()) or DEFAULT_NORMALIZE_SOURCE_LANG)
                self.opt_normalize_target_code.set(data.get("opt_normalize_target_code", self.opt_normalize_target_code.get()) or DEFAULT_NORMALIZE_TARGET_LANG)
                self.opt_dry_run.set(bool(data.get("opt_dry_run", self.opt_dry_run.get())))
                saved_profiles = data.get("user_profiles", {})
                if isinstance(saved_profiles, dict):
                    self.user_profiles = {}
                    for name, state in saved_profiles.items():
                        clean_name = str(name).strip()
                        if clean_name and clean_name not in self.builtin_profile_values and isinstance(state, dict):
                            self.user_profiles[clean_name] = state
                self.last_export_format.set(data.get("last_export_format", self.last_export_format.get()) if data.get("last_export_format") in ("XLSX report", "Raw XML TXT", "TMX file") else self.last_export_format.get())
                try:
                    self._saved_selected_tab_index = int(data.get("last_selected_tab_index", self._saved_selected_tab_index))
                except Exception:
                    self._saved_selected_tab_index = 0
                self._saved_window_geometry = str(data.get("window_geometry", "") or "")
                profile = data.get("opt_profile", self.opt_profile.get())
                if profile in self.builtin_profile_values or profile in self.user_profiles:
                    self.set_profile_value(profile)
        except Exception:
            pass

    def _get_current_tab_index(self):
        try:
            if hasattr(self, "notebook"):
                return int(self.notebook.index(self.notebook.select()))
        except Exception:
            pass
        return int(getattr(self, "_saved_selected_tab_index", 0) or 0)

    def _get_window_geometry(self):
        try:
            return self.root.winfo_geometry()
        except Exception:
            return ""

    def save_settings(self, silent=False):
        data = {
            "ui_language": self.ui_language.get(),
            "output_dir": self.output_dir.get(),
            "max_mb": self.max_mb.get(),
            "part_tu_count": self.part_tu_count.get(),
            "split_mode": self.split_mode.get(),
            "post_check_after_split": bool(self.post_check_after_split.get()),
            "prefix": self.prefix.get().strip() or DEFAULT_PREFIX,
            "source_langs": self.source_langs.get(),
            "target_langs": self.target_langs.get(),
            "analyze_before_split": bool(self.analyze_before_split.get()),
            "opt_remove_missing_source": bool(self.opt_remove_missing_source.get()),
            "opt_remove_missing_target": bool(self.opt_remove_missing_target.get()),
            "opt_remove_empty": bool(self.opt_remove_empty.get()),
            "opt_remove_tag_only": bool(self.opt_remove_tag_only.get()),
            "opt_remove_xml_errors": bool(self.opt_remove_xml_errors.get()),
            "opt_remove_duplicates": bool(self.opt_remove_duplicates.get()),
            "opt_warn_noisy": bool(self.opt_warn_noisy.get()),
            "opt_remove_noisy": bool(self.opt_remove_noisy.get()),
            "opt_remove_one_char_punct": bool(self.opt_remove_one_char_punct.get()),
            "opt_noisy_segments": self.opt_noisy_segments.get(),
            "opt_noisy_match_mode": self.noisy_mode_key(self.opt_noisy_match_mode.get()),
            "opt_warn_min_length": bool(self.opt_warn_min_length.get()),
            "opt_min_text_length": self.opt_min_text_length.get().strip() or "2",
            "opt_report_inline_tag_mismatch": bool(self.opt_report_inline_tag_mismatch.get()),
            "opt_strip_mismatched_inline_tags": bool(self.opt_strip_mismatched_inline_tags.get()),
            "opt_strip_all_inline_tags": bool(self.opt_strip_all_inline_tags.get()),
            "opt_keep_selected_pair": bool(self.opt_keep_selected_pair.get()),
            "opt_normalize_source_lang": bool(self.opt_normalize_source_lang.get()),
            "opt_normalize_target_lang": bool(self.opt_normalize_target_lang.get()),
            "opt_normalize_source_code": self.opt_normalize_source_code.get().strip() or DEFAULT_NORMALIZE_SOURCE_LANG,
            "opt_normalize_target_code": self.opt_normalize_target_code.get().strip() or DEFAULT_NORMALIZE_TARGET_LANG,
            "opt_profile": self.opt_profile.get(),
            "opt_dry_run": bool(self.opt_dry_run.get()),
            "user_profiles": self.user_profiles,
            "last_export_format": self.last_export_format.get(),
            "last_selected_tab_index": self._get_current_tab_index(),
            "window_geometry": self._get_window_geometry(),
        }
        path = get_settings_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if not silent:
                messagebox.showinfo(APP_TITLE, self.tr("Settings saved:") + f"\n{path}")
        except Exception as exc:
            if not silent:
                messagebox.showerror(APP_TITLE, self.tr("Could not save settings:") + f"\n{exc}")

    def reset_settings(self):
        self.ui_language.set("English")
        self.output_dir.set(os.path.abspath("output"))
        self.max_mb.set(DEFAULT_MAX_MB)
        self.part_tu_count.set(DEFAULT_PART_TU_COUNT)
        self.split_mode.set("mb")
        self.post_check_after_split.set(True)
        self.prefix.set(DEFAULT_PREFIX)
        self.source_langs.set(DEFAULT_SOURCE_LANGS)
        self.target_langs.set(DEFAULT_TARGET_LANGS)
        self.analyze_before_split.set(True)
        self.opt_remove_missing_source.set(True)
        self.opt_remove_missing_target.set(True)
        self.opt_remove_empty.set(True)
        self.opt_remove_tag_only.set(True)
        self.opt_remove_xml_errors.set(False)
        self.opt_remove_duplicates.set(False)
        self.opt_warn_noisy.set(True)
        self.opt_remove_noisy.set(False)
        self.opt_remove_one_char_punct.set(False)
        self.opt_noisy_segments.set("-, :, ;, ., •, *, +, %")
        self.opt_noisy_match_mode.set(self.noisy_mode_label("Both source and target"))
        self.opt_warn_min_length.set(False)
        self.opt_min_text_length.set("2")
        self.opt_report_inline_tag_mismatch.set(True)
        self.opt_strip_mismatched_inline_tags.set(False)
        self.opt_strip_all_inline_tags.set(False)
        self.opt_keep_selected_pair.set(False)
        self.opt_normalize_source_lang.set(False)
        self.opt_normalize_target_lang.set(False)
        self.opt_normalize_source_code.set(DEFAULT_NORMALIZE_SOURCE_LANG)
        self.opt_normalize_target_code.set(DEFAULT_NORMALIZE_TARGET_LANG)
        self.set_profile_value("General CAT-safe")
        self.opt_dry_run.set(False)
        self.last_export_format.set("XLSX report")
        self._saved_selected_tab_index = 0
        self._saved_window_geometry = ""
        messagebox.showinfo(APP_TITLE, self.tr("Settings reset to defaults. Click Apply to persist them."))

    def rebuild_profile_menu(self):
        menu = getattr(self, "profile_menu", None)
        if menu is None:
            return
        try:
            menu.delete(0, tk.END)
        except Exception:
            return
        self.profile_values = tuple(self.builtin_profile_values) + tuple(sorted(self.user_profiles.keys(), key=str.lower))
        for profile_name in self.builtin_profile_values:
            menu.add_command(
                label=self.profile_label(profile_name),
                command=lambda p=profile_name: (self.set_profile_value(p), self.hide_profile_menu_tooltip()),
            )
        if self.user_profiles:
            menu.add_separator()
            for profile_name in sorted(self.user_profiles.keys(), key=str.lower):
                menu.add_command(
                    label=profile_name,
                    command=lambda p=profile_name: (self.set_profile_value(p), self.hide_profile_menu_tooltip()),
                )

    def get_current_optimization_preset_state(self):
        return {
            "source_langs": self.source_langs.get(),
            "target_langs": self.target_langs.get(),
            "opt_remove_missing_source": bool(self.opt_remove_missing_source.get()),
            "opt_remove_missing_target": bool(self.opt_remove_missing_target.get()),
            "opt_remove_empty": bool(self.opt_remove_empty.get()),
            "opt_remove_tag_only": bool(self.opt_remove_tag_only.get()),
            "opt_remove_xml_errors": bool(self.opt_remove_xml_errors.get()),
            "opt_remove_duplicates": bool(self.opt_remove_duplicates.get()),
            "opt_warn_noisy": bool(self.opt_warn_noisy.get()),
            "opt_remove_noisy": bool(self.opt_remove_noisy.get()),
            "opt_remove_one_char_punct": bool(self.opt_remove_one_char_punct.get()),
            "opt_noisy_segments": self.opt_noisy_segments.get(),
            "opt_noisy_match_mode": self.noisy_mode_key(self.opt_noisy_match_mode.get()),
            "opt_warn_min_length": bool(self.opt_warn_min_length.get()),
            "opt_min_text_length": self.opt_min_text_length.get().strip() or "2",
            "opt_report_inline_tag_mismatch": bool(self.opt_report_inline_tag_mismatch.get()),
            "opt_strip_mismatched_inline_tags": bool(self.opt_strip_mismatched_inline_tags.get()),
            "opt_strip_all_inline_tags": bool(self.opt_strip_all_inline_tags.get()),
            "opt_keep_selected_pair": bool(self.opt_keep_selected_pair.get()),
            "opt_normalize_source_lang": bool(self.opt_normalize_source_lang.get()),
            "opt_normalize_target_lang": bool(self.opt_normalize_target_lang.get()),
            "opt_normalize_source_code": self.opt_normalize_source_code.get().strip() or DEFAULT_NORMALIZE_SOURCE_LANG,
            "opt_normalize_target_code": self.opt_normalize_target_code.get().strip() or DEFAULT_NORMALIZE_TARGET_LANG,
            "opt_dry_run": bool(self.opt_dry_run.get()),
        }

    def apply_optimization_preset_state(self, state):
        if not isinstance(state, dict):
            return
        if "source_langs" in state:
            self.source_langs.set(state.get("source_langs") or self.source_langs.get())
        if "target_langs" in state:
            self.target_langs.set(state.get("target_langs") or self.target_langs.get())
        bool_map = {
            "opt_remove_missing_source": self.opt_remove_missing_source,
            "opt_remove_missing_target": self.opt_remove_missing_target,
            "opt_remove_empty": self.opt_remove_empty,
            "opt_remove_tag_only": self.opt_remove_tag_only,
            "opt_remove_xml_errors": self.opt_remove_xml_errors,
            "opt_remove_duplicates": self.opt_remove_duplicates,
            "opt_warn_noisy": self.opt_warn_noisy,
            "opt_remove_noisy": self.opt_remove_noisy,
            "opt_remove_one_char_punct": self.opt_remove_one_char_punct,
            "opt_warn_min_length": self.opt_warn_min_length,
            "opt_report_inline_tag_mismatch": self.opt_report_inline_tag_mismatch,
            "opt_strip_mismatched_inline_tags": self.opt_strip_mismatched_inline_tags,
            "opt_strip_all_inline_tags": self.opt_strip_all_inline_tags,
            "opt_keep_selected_pair": self.opt_keep_selected_pair,
            "opt_normalize_source_lang": self.opt_normalize_source_lang,
            "opt_normalize_target_lang": self.opt_normalize_target_lang,
            "opt_dry_run": self.opt_dry_run,
        }
        for key, var in bool_map.items():
            if key in state:
                var.set(bool(state.get(key)))
        if "opt_noisy_segments" in state:
            self.opt_noisy_segments.set(state.get("opt_noisy_segments") or "-, :, ;, ., •, *, +, %")
        mode = self.noisy_mode_key(state.get("opt_noisy_match_mode"))
        if mode in ("Both source and target", "Either source or target"):
            self.opt_noisy_match_mode.set(self.noisy_mode_label(mode) if self.is_ru() else mode)
        if "opt_min_text_length" in state:
            self.opt_min_text_length.set(str(state.get("opt_min_text_length") or "2"))
        if "opt_normalize_source_code" in state:
            self.opt_normalize_source_code.set(state.get("opt_normalize_source_code") or DEFAULT_NORMALIZE_SOURCE_LANG)
        if "opt_normalize_target_code" in state:
            self.opt_normalize_target_code.set(state.get("opt_normalize_target_code") or DEFAULT_NORMALIZE_TARGET_LANG)

    def save_current_optimization_preset(self):
        name = simpledialog.askstring(APP_TITLE, self.tr("Preset name:"), parent=self.root)
        if name is None:
            return
        name = name.strip()
        if not name:
            messagebox.showwarning(APP_TITLE, self.tr("Preset name cannot be empty."))
            return
        if name in self.builtin_profile_values:
            messagebox.showwarning(APP_TITLE, self.tr("Built-in profile names cannot be overwritten. Choose another name."))
            return
        if name in self.user_profiles:
            if not messagebox.askyesno(APP_TITLE, f"{self.tr('Preset already exists:')}\n{name}\n\n{self.tr('Overwrite it?')}"):
                return
        self.user_profiles[name] = self.get_current_optimization_preset_state()
        self.set_profile_value(name)
        self.rebuild_profile_menu()
        self.save_settings(silent=True)
        self.log(f"Saved user optimization preset: {name}")

    def delete_selected_optimization_preset(self):
        name = self.opt_profile.get()
        if name not in self.user_profiles:
            messagebox.showinfo(APP_TITLE, self.tr("Only user presets can be deleted. Built-in profiles are always available."))
            return
        if not messagebox.askyesno(APP_TITLE, f"{self.tr('Delete user preset?')}\n\n{name}"):
            return
        del self.user_profiles[name]
        self.set_profile_value("Custom")
        self.rebuild_profile_menu()
        self.save_settings(silent=True)
        self.log(f"Deleted user optimization preset: {name}")

    def sanitize_imported_preset_state(self, state):
        if not isinstance(state, dict):
            return None
        allowed_keys = set(self.get_current_optimization_preset_state().keys())
        cleaned = {key: value for key, value in state.items() if key in allowed_keys}
        return cleaned if cleaned else None

    def collect_imported_presets(self, data):
        if not isinstance(data, dict):
            return {}
        raw_presets = None
        if isinstance(data.get("tost_presets"), dict):
            raw_presets = data.get("tost_presets")
        elif isinstance(data.get("user_profiles"), dict):
            raw_presets = data.get("user_profiles")
        elif isinstance(data.get("presets"), dict):
            raw_presets = data.get("presets")
        elif isinstance(data.get("name"), str) and isinstance(data.get("state"), dict):
            raw_presets = {data.get("name"): data.get("state")}
        else:
            raw_presets = data

        presets = {}
        if not isinstance(raw_presets, dict):
            return presets
        for name, state in raw_presets.items():
            clean_name = str(name).strip()
            if not clean_name or clean_name in self.builtin_profile_values:
                continue
            clean_state = self.sanitize_imported_preset_state(state)
            if clean_state is not None:
                presets[clean_name] = clean_state
        return presets

    def import_optimization_presets(self):
        path = filedialog.askopenfilename(
            parent=self.root,
            title=self.tr("Import optimization presets"),
            filetypes=[(self.tr("JSON files"), "*.json"), (self.tr("All files"), "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            imported = self.collect_imported_presets(data)
            if not imported:
                messagebox.showwarning(APP_TITLE, self.tr("No valid user presets were found in the selected file."))
                return

            conflicts = [name for name in imported if name in self.user_profiles]
            if conflicts:
                conflict_preview = "\n".join(conflicts[:20])
                if len(conflicts) > 20:
                    conflict_preview += f"\n... and {len(conflicts) - 20} more"
                answer = messagebox.askyesnocancel(
                    APP_TITLE,
                    f"{self.tr('Some presets already exist.')}\n\n"
                    f"{conflict_preview}\n\n"
                    f"{self.tr('Yes - overwrite existing presets.')}\n"
                    f"{self.tr('No - import only new presets.')}\n"
                    f"{self.tr('Cancel - do not import.')}",
                )
                if answer is None:
                    return
                overwrite = bool(answer)
            else:
                overwrite = True

            added = 0
            skipped = 0
            overwritten = 0
            for name, state in imported.items():
                if name in self.user_profiles:
                    if not overwrite:
                        skipped += 1
                        continue
                    overwritten += 1
                else:
                    added += 1
                self.user_profiles[name] = state

            self.rebuild_profile_menu()
            self.save_settings(silent=True)
            self.log(f"Imported optimization presets from: {path}")
            self.log(f"Preset import result: added {added}, overwritten {overwritten}, skipped {skipped}")
            messagebox.showinfo(
                APP_TITLE,
                f"{self.tr('Preset import completed.')}\n\n{self.tr('Added:')} {added}\n{self.tr('Overwritten:')} {overwritten}\n{self.tr('Skipped:')} {skipped}",
            )
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"{self.tr('Could not import presets:')}\n{exc}")

    def get_profile_description(self, profile):
        profile = self.profile_key_from_label(profile)
        # Menu passes localized labels; convert built-in profile labels back to internal keys.
        if profile in self.profile_descriptions:
            if self.is_ru():
                ru_desc = {
                    "General CAT-safe": "Осторожный профиль по умолчанию. Удаляет TU без языка, пустые и tag-only TU; сообщает о мусорных парах и расхождениях inline-тегов. Не удаляет дубли, не нормализует языковые коды и не удаляет inline-теги.",
                    "Strict import": "Более строгий профиль очистки. Удаляет TU без языка, пустые, tag-only и поврежденные TU, удаляет точные дубли пар оригинал-перевод, сообщает о мусорных парах и расхождениях inline-тегов. По умолчанию не нормализует языковые коды.",
                    "Smartcat-oriented": "Профиль для строгого импорта в CAT, ориентированный на Smartcat. Оставляет выбранную пару оригинал-перевод, нормализует языковые коды, удаляет TU без языка, пустые и tag-only TU, точные дубли, пары из списка мусорных сегментов и односимвольные/пунктуационные пары, сообщает о расхождении inline-тегов.",
                    "Custom": "Ручной профиль. Оставляет текущие настройки галочек без изменений, чтобы вы могли настроить правила очистки самостоятельно.",
                }
                return ru_desc.get(profile, self.profile_descriptions.get(profile, ""))
            return self.profile_descriptions.get(profile, "")
        if profile in self.user_profiles:
            return "Пользовательский пресет. Применяет сохраненные под этим именем настройки оптимизации." if self.is_ru() else "User preset. Applies the optimization settings that were saved under this name."
        return ""

    def get_current_profile_description(self):
        return self.get_profile_description(self.opt_profile.get())

    def hide_profile_menu_tooltip(self):
        tooltip = getattr(self, "profile_menu_tooltip", None)
        if tooltip is not None:
            try:
                tooltip._hide()
            except Exception:
                pass

    def apply_optimization_profile(self):
        profile = self.opt_profile.get()

        if profile in self.user_profiles:
            self.apply_optimization_preset_state(self.user_profiles[profile])
            self.log(f"Applied user optimization preset: {profile}")
            return

        if profile == "General CAT-safe":
            self.opt_remove_missing_source.set(True)
            self.opt_remove_missing_target.set(True)
            self.opt_remove_empty.set(True)
            self.opt_remove_tag_only.set(True)
            self.opt_remove_xml_errors.set(False)
            self.opt_remove_duplicates.set(False)
            self.opt_warn_noisy.set(True)
            self.opt_remove_noisy.set(False)
            self.opt_remove_one_char_punct.set(False)
            self.opt_noisy_match_mode.set(self.noisy_mode_label("Both source and target"))
            self.opt_warn_min_length.set(False)
            self.opt_min_text_length.set("2")
            self.opt_report_inline_tag_mismatch.set(True)
            self.opt_strip_mismatched_inline_tags.set(False)
            self.opt_strip_all_inline_tags.set(False)
            self.opt_keep_selected_pair.set(False)
            self.opt_normalize_source_lang.set(False)
            self.opt_normalize_target_lang.set(False)
            self.log("Applied optimization profile: General CAT-safe")

        elif profile == "Strict import":
            self.opt_remove_missing_source.set(True)
            self.opt_remove_missing_target.set(True)
            self.opt_remove_empty.set(True)
            self.opt_remove_tag_only.set(True)
            self.opt_remove_xml_errors.set(True)
            self.opt_remove_duplicates.set(True)
            self.opt_warn_noisy.set(True)
            self.opt_remove_noisy.set(False)
            self.opt_remove_one_char_punct.set(False)
            self.opt_noisy_match_mode.set(self.noisy_mode_label("Both source and target"))
            self.opt_warn_min_length.set(False)
            self.opt_min_text_length.set("2")
            self.opt_report_inline_tag_mismatch.set(True)
            self.opt_strip_mismatched_inline_tags.set(False)
            self.opt_strip_all_inline_tags.set(False)
            self.opt_keep_selected_pair.set(False)
            self.opt_normalize_source_lang.set(False)
            self.opt_normalize_target_lang.set(False)
            self.log("Applied optimization profile: Strict import")

        elif profile == "Smartcat-oriented":
            self.opt_remove_missing_source.set(True)
            self.opt_remove_missing_target.set(True)
            self.opt_remove_empty.set(True)
            self.opt_remove_tag_only.set(True)
            self.opt_remove_xml_errors.set(False)
            self.opt_remove_duplicates.set(True)
            self.opt_warn_noisy.set(True)
            self.opt_remove_noisy.set(True)
            self.opt_remove_one_char_punct.set(True)
            self.opt_noisy_segments.set("-, :, ;, ., •, *, +, %")
            self.opt_noisy_match_mode.set(self.noisy_mode_label("Both source and target"))
            self.opt_warn_min_length.set(False)
            self.opt_min_text_length.set("2")
            self.opt_report_inline_tag_mismatch.set(True)
            self.opt_strip_mismatched_inline_tags.set(False)
            self.opt_strip_all_inline_tags.set(False)
            self.opt_keep_selected_pair.set(True)
            self.opt_normalize_source_lang.set(True)
            self.opt_normalize_target_lang.set(True)
            if not self.opt_normalize_source_code.get().strip():
                self.opt_normalize_source_code.set(DEFAULT_NORMALIZE_SOURCE_LANG)
            if not self.opt_normalize_target_code.get().strip():
                self.opt_normalize_target_code.set(DEFAULT_NORMALIZE_TARGET_LANG)
            self.log("Applied optimization profile: Smartcat-oriented")

        else:
            self.log("Optimization profile is Custom. No options were changed.")

    def open_output_folder(self):
        path = self.output_dir.get().strip() or os.path.abspath("output")
        try:
            os.makedirs(path, exist_ok=True)
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"{self.tr('Could not open output folder:')}\n{exc}")

    def open_settings_folder(self):
        path = get_app_dir()
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"{self.tr('Could not open settings folder:')}\n{exc}")

    def add_files(self):
        paths = filedialog.askopenfilenames(title="Select TMX files", filetypes=[("TMX files", "*.tmx"), ("All files", "*.*")])
        for path in paths:
            if path not in self.files:
                self.files.append(path)
                self.file_list.insert(tk.END, path)
        if paths and not self.output_dir.get():
            self.output_dir.set(os.path.join(os.path.dirname(paths[0]), "output"))

    def remove_selected(self):
        selected = list(self.file_list.curselection())
        selected.reverse()
        for idx in selected:
            self.file_list.delete(idx)
            del self.files[idx]

    def clear_files(self):
        self.files.clear()
        self.file_list.delete(0, tk.END)

    def choose_output(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.output_dir.set(path)

    def set_running(self, running):
        state = tk.DISABLED if running else tk.NORMAL
        self.start_btn.config(state=state)
        self.analyze_btn.config(state=state)
        if hasattr(self, "optimize_btn"):
            self.optimize_btn.config(state=state)
        if hasattr(self, "compare_btn"):
            self.compare_btn.config(state=state)
        self.cancel_btn.config(state=tk.NORMAL if running else tk.DISABLED)
        if hasattr(self, "save_settings_btn") and self.save_settings_btn.winfo_exists():
            self.save_settings_btn.config(state=state)

    def log(self, text):
        self.queue.put(("log", text))

    def set_result_summary_text(self, text):
        self.queue.put(("result_summary", text))

    def open_path(self, path, label="file"):
        if not path or not os.path.exists(path):
            messagebox.showinfo(APP_TITLE, self.tr("No {label} has been created yet.").format(label=label))
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as exc:
            messagebox.showerror(APP_TITLE, self.tr("Could not open {label}:").format(label=label) + f"\n{exc}")

    def open_last_report(self):
        self.open_path(self.last_report_path, "report")

    def open_optimized_tmx(self):
        self.open_path(self.last_optimized_tmx_path, "optimized TMX")

    def view_problem_tus(self):
        if not self.last_problem_tus:
            messagebox.showinfo(APP_TITLE, self.tr("No problem TUs are available. Run Analyze first."))
            return

        win = tk.Toplevel(self.root)
        win.title("Problem TUs")
        win.geometry("980x620")
        win.transient(self.root)
        apply_window_icon(win)

        container = ttk.Frame(win, padding=8)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="Problem TUs from the latest analysis. Select a row to view the original TU XML.").pack(anchor="w", pady=(0, 6))

        columns = ("tu_number", "line", "problems", "languages", "source_preview", "target_preview")

        tree_frame = ttk.Frame(container)
        tree_frame.pack(fill=tk.BOTH, expand=False)

        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        headings = {
            "tu_number": "TU number",
            "line": "Line",
            "problems": "Problems",
            "languages": "Languages",
            "source_preview": "Source preview",
            "target_preview": "Target preview",
        }
        widths = {
            "tu_number": 90,
            "line": 90,
            "problems": 220,
            "languages": 110,
            "source_preview": 260,
            "target_preview": 260,
        }
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col], anchor="w", stretch=False)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        raw_box = ttk.LabelFrame(container, text="Original TU XML", padding=4)
        raw_box.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        raw_text = tk.Text(raw_box, wrap="none", height=18)
        raw_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        raw_scroll_y = ttk.Scrollbar(raw_box, orient=tk.VERTICAL, command=raw_text.yview)
        raw_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        raw_text.configure(yscrollcommand=raw_scroll_y.set)

        for idx, item in enumerate(self.last_problem_tus):
            tree.insert("", tk.END, iid=str(idx), values=(
                item.get("tu_number", ""),
                item.get("line", ""),
                item.get("problems", ""),
                item.get("languages", ""),
                item.get("source_preview", ""),
                item.get("target_preview", ""),
            ))

        def on_select(_event=None):
            selected = tree.selection()
            raw_text.delete("1.0", tk.END)
            if not selected:
                return
            item = self.last_problem_tus[int(selected[0])]
            raw_text.insert(tk.END, item.get("raw_tu_xml", ""))

        tree.bind("<<TreeviewSelect>>", on_select)
        if self.last_problem_tus:
            tree.selection_set("0")
            tree.focus("0")
            on_select()


    @staticmethod
    def _rows_to_dicts(rows):
        if not rows or len(rows) < 2:
            return []
        header = [str(x) for x in rows[0]]
        out = []
        for row in rows[1:]:
            item = {}
            for idx, key in enumerate(header):
                item[key] = row[idx] if idx < len(row) else ""
            out.append(item)
        return out

    def _view_result_rows(self, title, rows, columns, xml_column=None, message_if_empty="No rows are available yet."):
        if not rows:
            messagebox.showinfo(APP_TITLE, self.tr(message_if_empty))
            return

        display_title = self.tr(title)
        win = tk.Toplevel(self.root)
        win.title(display_title)
        win.geometry("1120x660")
        win.transient(self.root)
        apply_window_icon(win)

        container = ttk.Frame(win, padding=8)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text=f"{display_title}. {self.tr('Select a row to view details below.')}").pack(anchor="w", pady=(0, 6))

        tree_frame = ttk.Frame(container)
        tree_frame.pack(fill=tk.BOTH, expand=False)

        tree = ttk.Treeview(tree_frame, columns=[c[0] for c in columns], show="headings", height=11)
        for key, heading, width in columns:
            tree.heading(key, text=heading)
            tree.column(key, width=width, anchor="w", stretch=False)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        detail_box = ttk.LabelFrame(container, text=self.tr("Details / raw XML"), padding=4)
        detail_box.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        detail_text = tk.Text(detail_box, wrap="none", height=18)
        detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scroll_y = ttk.Scrollbar(detail_box, orient=tk.VERTICAL, command=detail_text.yview)
        detail_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        detail_scroll_x = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=detail_text.xview)
        detail_scroll_x.pack(fill=tk.X)
        detail_text.configure(yscrollcommand=detail_scroll_y.set, xscrollcommand=detail_scroll_x.set)

        for idx, item in enumerate(rows):
            values = []
            for key, _heading, _width in columns:
                val = item.get(key, "")
                if isinstance(val, (list, tuple)):
                    val = ";".join(str(x) for x in val)
                values.append(str(val))
            tree.insert("", tk.END, iid=str(idx), values=values)

        def on_select(_event=None):
            selected = tree.selection()
            detail_text.delete("1.0", tk.END)
            if not selected:
                return
            item = rows[int(selected[0])]
            if xml_column and item.get(xml_column):
                detail_text.insert(tk.END, str(item.get(xml_column, "")))
            else:
                for key, heading, _width in columns:
                    detail_text.insert(tk.END, f"{heading}: {item.get(key, '')}\n")
                # Also show any non-column fields, which is useful for before/after XML fields.
                shown = {key for key, _heading, _width in columns}
                for key, value in item.items():
                    if key not in shown and value not in (None, ""):
                        detail_text.insert(tk.END, f"\n{key}:\n{value}\n")

        tree.bind("<<TreeviewSelect>>", on_select)
        if rows:
            tree.selection_set("0")
            tree.focus("0")
            on_select()

    def view_removed_tus(self):
        self._view_result_rows(
            "Removed TUs",
            self.last_removed_tus,
            [
                ("tu_number", "TU number", 90),
                ("line", "Line", 90),
                ("remove_reason", "Remove reason", 240),
                ("detected_problems", "Detected problems", 240),
                ("languages", "Languages", 110),
                ("source_preview", "Source preview", 260),
                ("target_preview", "Target preview", 260),
                ("duplicate_kept_tu_number", "Kept duplicate TU", 130),
            ],
            xml_column="raw_tu_xml",
            message_if_empty="No removed TUs are available. Run Optimize TMX first.",
        )

    def view_duplicate_tus(self):
        self._view_result_rows(
            "Removed duplicate TUs",
            self.last_duplicate_tus,
            [
                ("removed_tu_number", "Removed TU", 100),
                ("removed_line", "Line", 90),
                ("kept_tu_number", "Kept TU", 100),
                ("reason", "Reason", 220),
                ("source_preview", "Source preview", 300),
                ("target_preview", "Target preview", 300),
            ],
            xml_column="removed_raw_tu_xml",
            message_if_empty="No removed duplicate TUs are available. Run Optimize TMX with duplicate removal enabled.",
        )

    def view_noisy_warnings(self):
        self._view_result_rows(
            "Noisy segment warnings",
            self.last_noisy_warnings,
            [
                ("tu_number", "TU number", 90),
                ("line", "Line", 90),
                ("action", "Action", 110),
                ("reason", "Reason", 220),
                ("source_text", "Source text", 300),
                ("target_text", "Target text", 300),
            ],
            xml_column="raw_tu_xml",
            message_if_empty="No noisy segment warnings are available. Run Optimize TMX first.",
        )

    def view_inline_tag_warnings(self):
        self._view_result_rows(
            "Inline-tag warnings",
            self.last_inline_tag_warnings,
            [
                ("tu_number", "TU number", 90),
                ("line", "Line", 90),
                ("action", "Action", 110),
                ("reason", "Reason", 220),
                ("source_tag_sequence", "Source tags", 260),
                ("target_tag_sequence", "Target tags", 260),
                ("source_preview", "Source preview", 240),
                ("target_preview", "Target preview", 240),
            ],
            xml_column="raw_tu_xml",
            message_if_empty="No inline-tag warnings are available. Run Optimize TMX first.",
        )

    def view_changed_tus(self):
        self._view_result_rows(
            "Changed TUs",
            self.last_changed_tus,
            [
                ("tu_number", "TU number", 90),
                ("line", "Line", 90),
                ("change_type", "Change type", 220),
                ("reason", "Reason", 240),
                ("source_tag_sequence_before", "Source tags before", 260),
                ("target_tag_sequence_before", "Target tags before", 260),
            ],
            xml_column="raw_tu_xml_after",
            message_if_empty="No changed TUs are available. Run Optimize TMX with language normalization or inline-tag stripping enabled.",
        )


    def _available_export_groups(self):
        groups = [
            ("Problem TUs", self.last_problem_tus),
            ("Removed TUs", self.last_removed_tus),
            ("Removed duplicates", self.last_duplicate_tus),
            ("Noisy warnings", self.last_noisy_warnings),
            ("Inline-tag warnings", self.last_inline_tag_warnings),
            ("Changed TUs", self.last_changed_tus),
        ]
        return [(name, rows) for name, rows in groups if rows]

    @staticmethod
    def _dict_rows_to_sheet(rows):
        if not rows:
            return [["No rows"]]
        preferred = [
            "tu_number", "line", "problems", "remove_reason", "detected_problems", "action", "reason",
            "languages", "source_preview", "target_preview", "source_text", "target_text",
            "removed_tu_number", "removed_line", "kept_tu_number", "duplicate_kept_tu_number",
            "change_type", "source_tag_sequence", "target_tag_sequence",
            "source_tag_sequence_before", "target_tag_sequence_before",
            "raw_tu_xml", "removed_raw_tu_xml", "kept_raw_tu_xml", "raw_tu_xml_before", "raw_tu_xml_after",
            "xml_error",
        ]
        keys = []
        for key in preferred:
            if any(key in row for row in rows):
                keys.append(key)
        for row in rows:
            for key in row.keys():
                if key not in keys:
                    keys.append(key)
        sheet = [keys]
        for row in rows:
            sheet.append([row.get(key, "") for key in keys])
        return sheet

    @staticmethod
    def _extract_raw_xml_from_row(row):
        for key in ("raw_tu_xml", "removed_raw_tu_xml", "raw_tu_xml_after", "raw_tu_xml_before"):
            val = row.get(key)
            if val:
                return str(val)
        return ""

    def export_result_groups_dialog(self, default_groups=None):
        groups = self._available_export_groups()
        if not groups:
            messagebox.showinfo(APP_TITLE, self.tr("No result groups are available yet. Run Analyze or Optimize TMX first."))
            return

        default_groups = set(default_groups or [])
        win = tk.Toplevel(self.root)
        win.title("Export result groups")
        win.geometry("560x385")
        win.transient(self.root)
        win.grab_set()
        apply_window_icon(win)

        container = ttk.Frame(win, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text="Select result groups and output format.",
            wraplength=520,
        ).pack(anchor="w", pady=(0, 8))

        vars_by_name = {}
        group_box = ttk.LabelFrame(container, text="Groups", padding=6)
        group_box.pack(fill=tk.X, pady=(0, 8))
        for name, rows in groups:
            selected = (name in default_groups) if default_groups else True
            var = tk.BooleanVar(value=selected)
            vars_by_name[name] = var
            ttk.Checkbutton(group_box, text=f"{name} ({len(rows)})", variable=var).pack(anchor="w")

        format_var = self.last_export_format
        if format_var.get() not in ("XLSX report", "Raw XML TXT", "TMX file"):
            format_var.set("XLSX report")
        format_row = ttk.Frame(container)
        format_row.pack(fill=tk.X, pady=(0, 0))
        ttk.Label(format_row, text="Format:").pack(side=tk.LEFT)
        ttk.Combobox(
            format_row,
            textvariable=format_var,
            values=("XLSX report", "Raw XML TXT", "TMX file"),
            width=18,
            state="readonly",
        ).pack(side=tk.LEFT, padx=6)

        format_help_frame = ttk.Frame(container)
        format_help_frame.pack(anchor="w", fill=tk.X, pady=(8, 10))

        help_rows = (
            ("XLSX report", "Exports selected groups as workbook sheets with all available columns."),
            ("Raw XML TXT", "Exports original TU XML blocks as plain text for manual inspection."),
            ("TMX file", "Exports available TU XML blocks into a valid TMX file for reimport/testing."),
        )
        for i, (fmt_name, fmt_desc) in enumerate(help_rows):
            row = ttk.Frame(format_help_frame)
            row.grid(row=i, column=0, sticky="w", pady=(0, 2 if i < len(help_rows) - 1 else 0))
            name_lbl = ttk.Label(row, text=f"{fmt_name}:", font=("TkDefaultFont", 9, "bold"), foreground="#555555", width=13, anchor="e")
            name_lbl.grid(row=0, column=0, sticky="ne", padx=(0, 8))
            desc_lbl = ttk.Label(row, text=fmt_desc, foreground="#555555", wraplength=390, justify=tk.LEFT)
            desc_lbl.grid(row=0, column=1, sticky="w")

        def ask_save(**kwargs):
            # With a grabbed modal dialog, native file dialogs can appear behind the
            # export window on some Windows setups unless we temporarily release the grab.
            try:
                win.grab_release()
            except Exception:
                pass
            try:
                return filedialog.asksaveasfilename(parent=win, **kwargs)
            finally:
                try:
                    if win.winfo_exists():
                        win.grab_set()
                        win.lift()
                except Exception:
                    pass

        def do_export():
            try:
                selected_groups = [(name, rows) for name, rows in groups if vars_by_name[name].get()]
                if not selected_groups:
                    messagebox.showwarning(APP_TITLE, self.tr("Select at least one result group to export."), parent=win)
                    return

                out_dir = self.output_dir.get().strip() or os.getcwd()
                os.makedirs(out_dir, exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                fmt = format_var.get()
                if fmt == "XLSX report":
                    path = ask_save(
                        title="Save exported result groups",
                        initialdir=out_dir,
                        initialfile=f"tost_exported_result_groups_{timestamp}.xlsx",
                        defaultextension=".xlsx",
                        filetypes=[("Excel workbook", "*.xlsx")],
                    )
                    if not path:
                        return
                    sheets = []
                    for name, rows in selected_groups:
                        sheets.append((name, self._dict_rows_to_sheet(rows)))
                    write_xlsx(path, sheets)
                elif fmt == "Raw XML TXT":
                    path = ask_save(
                        title="Save exported raw XML",
                        initialdir=out_dir,
                        initialfile=f"tost_exported_result_groups_{timestamp}.txt",
                        defaultextension=".txt",
                        filetypes=[("Text file", "*.txt")],
                    )
                    if not path:
                        return
                    parts = []
                    for name, rows in selected_groups:
                        parts.append(f"===== {name} ({len(rows)}) =====\n")
                        for idx, row in enumerate(rows, 1):
                            xml = self._extract_raw_xml_from_row(row)
                            parts.append(f"\n--- {name} #{idx} ---\n")
                            if xml:
                                parts.append(xml.rstrip() + "\n")
                            else:
                                parts.append("No raw TU XML available for this row.\n")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("".join(parts))
                else:
                    path = ask_save(
                        title="Save exported TMX",
                        initialdir=out_dir,
                        initialfile=f"tost_exported_result_groups_{timestamp}.tmx",
                        defaultextension=".tmx",
                        filetypes=[("TMX file", "*.tmx")],
                    )
                    if not path:
                        return
                    tu_blocks = []
                    seen = set()
                    for _name, rows in selected_groups:
                        for row in rows:
                            xml = self._extract_raw_xml_from_row(row).strip()
                            if xml and xml not in seen:
                                seen.add(xml)
                                tu_blocks.append(xml)
                    if not tu_blocks:
                        messagebox.showwarning(APP_TITLE, self.tr("Selected groups do not contain raw TU XML blocks that can be exported as TMX."), parent=win)
                        return
                    source_lang = (sorted(parse_lang_set(self.source_langs.get())) or ["en"])[0]
                    with open(path, "w", encoding="utf-8", newline="\n") as f:
                        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                        f.write('<tmx version="1.4">\n')
                        f.write(f'  <header creationtool="{escape(APP_SHORT_NAME)}" creationtoolversion="5.0" segtype="sentence" adminlang="en" srclang="{escape(source_lang)}" datatype="PlainText"/>\n')
                        f.write('  <body>\n')
                        for xml in tu_blocks:
                            f.write(xml.rstrip() + "\n")
                        f.write('  </body>\n</tmx>\n')

                self.last_report_path = path
                self.log(f"Exported selected result groups: {path}")
                messagebox.showinfo(APP_TITLE, f"{self.tr('Export completed:')}\n{path}", parent=win)
                win.destroy()
            except Exception as exc:
                messagebox.showerror(APP_TITLE, f"{self.tr('Export failed:')}\n{exc}", parent=win)
                self.log(f"Export failed: {exc}")

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(actions, text="Export", command=do_export).pack(side=tk.LEFT)
        ttk.Button(actions, text="Cancel", command=win.destroy).pack(side=tk.LEFT, padx=6)

    def format_compare_files_label(self, files):
        if not files:
            return self.tr("No TMX files selected")
        if len(files) == 1:
            return files[0]
        return f"{len(files)} TMX files selected"

    def choose_compare_files_a(self):
        initial_dir = os.path.dirname(self.compare_files_a[0]) if self.compare_files_a else os.getcwd()
        paths = filedialog.askopenfilenames(
            title=self.tr("Select TMX file(s) for side A"),
            initialdir=initial_dir,
            filetypes=[(self.tr("TMX files"), "*.tmx"), (self.tr("All files"), "*.*")],
        )
        if paths:
            self.compare_files_a = [os.path.abspath(p) for p in paths]
            self.compare_files_a_label.set(self.format_compare_files_label(self.compare_files_a))

    def choose_compare_files_b(self):
        initial_dir = os.path.dirname(self.compare_files_b[0]) if self.compare_files_b else os.getcwd()
        paths = filedialog.askopenfilenames(
            title=self.tr("Select TMX file(s) for side B"),
            initialdir=initial_dir,
            filetypes=[(self.tr("TMX files"), "*.tmx"), (self.tr("All files"), "*.*")],
        )
        if paths:
            self.compare_files_b = [os.path.abspath(p) for p in paths]
            self.compare_files_b_label.set(self.format_compare_files_label(self.compare_files_b))

    def clear_compare_files_a(self):
        self.compare_files_a = []
        self.compare_files_a_label.set(self.format_compare_files_label(self.compare_files_a))

    def clear_compare_files_b(self):
        self.compare_files_b = []
        self.compare_files_b_label.set(self.format_compare_files_label(self.compare_files_b))

    def start_compare(self):
        files_a = [p for p in self.compare_files_a if os.path.isfile(p) and p.lower().endswith(".tmx")]
        files_b = [p for p in self.compare_files_b if os.path.isfile(p) and p.lower().endswith(".tmx")]
        output_dir = self.output_dir.get().strip()
        if not files_a:
            messagebox.showerror(APP_TITLE, self.tr("TMX A is not selected or does not contain valid TMX files."))
            return
        if not files_b:
            messagebox.showerror(APP_TITLE, self.tr("TMX B is not selected or does not contain valid TMX files."))
            return
        if not self.validate_output_folder(output_dir):
            return
        source_langs = parse_lang_set(self.source_langs.get())
        target_langs = parse_lang_set(self.target_langs.get())
        if not source_langs or not target_langs:
            messagebox.showerror(APP_TITLE, self.tr("Source langs and target langs cannot be empty."))
            return
        if source_langs & target_langs:
            overlap = ", ".join(sorted(source_langs & target_langs))
            if not messagebox.askyesno(APP_TITLE, f"{self.tr('Source and target language lists overlap:')} {overlap}\n\n{self.tr('Continue anyway?')}"):
                return

        self.cancel_event.clear()
        self.set_running(True)
        self.progress.config(value=0, maximum=100)
        self.log_text.delete("1.0", tk.END)
        self.last_report_path = None
        self.result_summary.set(self.tr("Result summary: comparing TMX files..."))
        self.log(APP_TITLE)
        self.log("Comparing selected TMX files. Original TMX files will not be modified.")
        args = (files_a, files_b, output_dir, source_langs, target_langs)
        self.worker = threading.Thread(target=self.compare_worker_main, args=args, daemon=True)
        self.worker.start()

    def start_split(self):
        self.start_worker(mode="split")

    def start_analyze_only(self):
        self.start_worker(mode="analyze")

    def start_optimize(self):
        self.start_worker(mode="optimize")

    def is_valid_language_code(self, value):
        value = (value or "").strip()
        if not value:
            return False
        # Accept common BCP-47-like values such as en, en-US, pt-BR, zh-Hans, sr-Cyrl-RS.
        return bool(re.fullmatch(r"[A-Za-z]{2,8}([_-][A-Za-z0-9]{2,8})*", value))

    def validate_output_folder(self, output_dir):
        if not output_dir or not output_dir.strip():
            messagebox.showerror(APP_TITLE, self.tr("Output folder cannot be empty."))
            return False
        output_dir = output_dir.strip()
        try:
            os.makedirs(output_dir, exist_ok=True)
            test_path = os.path.join(output_dir, ".tost_write_test.tmp")
            with open(test_path, "w", encoding="utf-8") as f:
                f.write("ok")
            try:
                os.remove(test_path)
            except Exception:
                pass
            return True
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"{self.tr('Output folder is not writable:')}\n{output_dir}\n\n{exc}")
            return False

    def collect_optimize_warnings(self):
        warnings = []
        if getattr(self, "opt_dry_run", None) is not None and self.opt_dry_run.get():
            warnings.append(self.tr("Dry run is enabled: TOST will create an XLSX report only and will not leave an optimized TMX file."))
        if self.opt_remove_duplicates.get():
            warnings.append(self.tr("Remove exact duplicates keeps only the first source-target pair and removes later duplicates."))
        if self.opt_remove_noisy.get():
            warnings.append(self.tr("Remove pairs matching the noisy segment list may delete valid short UI strings if the list is too broad."))
        if self.opt_remove_one_char_punct.get():
            warnings.append(self.tr("Remove one-character or punctuation-only pairs can delete legitimate UI labels such as symbols or numbered options."))
        if self.opt_strip_mismatched_inline_tags.get():
            warnings.append(self.tr("Strip inline tags only from mismatched TUs changes segment content in affected TU blocks."))
        if self.opt_strip_all_inline_tags.get():
            warnings.append(self.tr("Strip inline tags from all kept TUs changes segment content across the optimized TMX."))
        if self.opt_normalize_source_lang.get() or self.opt_normalize_target_lang.get():
            warnings.append(self.tr("Language normalization rewrites xml:lang values in the optimized TMX."))
        if self.opt_keep_selected_pair.get():
            warnings.append(self.tr("Keep only selected source-target language pair removes other languages from multilingual TU blocks."))
        if self.opt_remove_xml_errors.get():
            warnings.append(self.tr("Remove XML parse errors / malformed TU is aggressive; malformed blocks will be excluded from the optimized TMX."))
        return warnings

    def confirm_optimize_warnings(self):
        warnings = self.collect_optimize_warnings()
        if not warnings:
            return True
        text = self.tr("The selected optimization settings may change or remove TMX content:") + "\n\n"
        text += "\n".join(f"- {w}" for w in warnings)
        text += "\n\n" + self.tr("Original TMX files are never modified. Continue?")
        return messagebox.askyesno(APP_TITLE, text)

    def start_worker(self, mode):
        if not self.files:
            messagebox.showwarning(APP_TITLE, self.tr("Please add at least one TMX file."))
            return

        output_dir = self.output_dir.get().strip()
        if not self.validate_output_folder(output_dir):
            return

        split_mode = self.split_mode.get() if self.split_mode.get() in ("mb", "tu") else "mb"
        max_mb = 0.0
        part_tu_count = 0
        if mode == "split":
            if split_mode == "mb":
                try:
                    max_mb = float(self.max_mb.get().replace(",", "."))
                    if max_mb <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror(APP_TITLE, self.tr("Part size must be a positive number."))
                    return
            else:
                try:
                    part_tu_count = int(self.part_tu_count.get().strip())
                    if part_tu_count <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror(APP_TITLE, self.tr("Part TU count must be a positive integer."))
                    return

        source_langs = parse_lang_set(self.source_langs.get())
        target_langs = parse_lang_set(self.target_langs.get())
        if not source_langs or not target_langs:
            messagebox.showerror(APP_TITLE, self.tr("Source langs and target langs cannot be empty."))
            return
        if source_langs & target_langs:
            overlap = ", ".join(sorted(source_langs & target_langs))
            if not messagebox.askyesno(APP_TITLE, f"{self.tr('Source and target language lists overlap:')} {overlap}\n\n{self.tr('Continue anyway?')}"):
                return

        if mode == "optimize":
            if self.opt_remove_noisy.get() and not parse_noisy_set(self.opt_noisy_segments.get()):
                messagebox.showerror(APP_TITLE, self.tr("Noisy segment list is empty, but noisy segment removal is enabled."))
                return
            if self.opt_warn_min_length.get():
                try:
                    min_len = int(self.opt_min_text_length.get().strip())
                    if min_len <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror(APP_TITLE, self.tr("Minimum text length must be a positive integer."))
                    return
            if self.opt_normalize_source_lang.get():
                code = self.opt_normalize_source_code.get().strip()
                if code and not self.is_valid_language_code(code):
                    messagebox.showerror(APP_TITLE, f"{self.tr('Invalid source language code for normalization:')} {code}")
                    return
            if self.opt_normalize_target_lang.get():
                code = self.opt_normalize_target_code.get().strip()
                if code and not self.is_valid_language_code(code):
                    messagebox.showerror(APP_TITLE, f"{self.tr('Invalid target language code for normalization:')} {code}")
                    return
            if not self.confirm_optimize_warnings():
                return

        self.cancel_event.clear()
        self.set_running(True)
        self.progress.config(value=0, maximum=100)
        self.log_text.delete("1.0", tk.END)
        self.last_report_path = None
        self.last_optimized_tmx_path = None
        self.last_problem_tus = []
        self.last_removed_tus = []
        self.last_duplicate_tus = []
        self.last_noisy_warnings = []
        self.last_inline_tag_warnings = []
        self.last_changed_tus = []
        self.clear_analysis_table()
        self.result_summary.set("Result summary: running...")
        self.log(APP_TITLE)
        if mode == "optimize":
            self.log("Safety pre-check passed. Original TMX files will not be modified.")
            if self.opt_dry_run.get():
                self.log("Dry run enabled: report only, no optimized TMX will be kept.")
        args = (list(self.files), output_dir, max_mb, part_tu_count, split_mode, self.prefix.get().strip() or DEFAULT_PREFIX, source_langs, target_langs, mode)
        self.worker = threading.Thread(target=self.worker_main, args=args, daemon=True)
        self.worker.start()

    def cancel(self):
        self.cancel_event.set()
        self.log("Cancel requested. Waiting for current operation to stop...")

    def clear_analysis_table(self):
        # The visible analysis table was removed in v2.2.
        # Error counts are printed directly in the Log area.
        pass

    def update_analysis_table(self, payload):
        # Kept for compatibility with queued messages from worker code.
        # Error counts are printed directly in the Log area.
        pass

    def process_queue(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "log":
                    self.log_text.insert(tk.END, payload + "\n")
                    self.log_text.see(tk.END)
                elif kind == "progress":
                    self.progress.config(value=payload)
                elif kind == "overall":
                    self.overall_label.config(text=payload)
                elif kind == "result_summary":
                    self.result_summary.set(payload)
                elif kind == "analysis_table":
                    self.update_analysis_table(payload)
                elif kind == "done":
                    self.set_running(False)
                    self.overall_label.config(text=self.tr("Overall: done"))
                    messagebox.showinfo(APP_TITLE, payload)
                elif kind == "error":
                    self.set_running(False)
                    self.overall_label.config(text=self.tr("Overall: error"))
                    messagebox.showerror(APP_TITLE, payload)
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def worker_main(self, files, output_dir, max_mb, part_tu_count, split_mode, prefix, source_langs, target_langs, mode):
        try:
            os.makedirs(output_dir, exist_ok=True)
            batch_rows = []
            for index, path in enumerate(files, 1):
                if self.cancel_event.is_set():
                    self.queue.put(("done", "Canceled."))
                    return
                self.queue.put(("overall", f"{self.tr('Overall')}: {index} / {len(files)}"))
                self.log(f"Processing file: {os.path.basename(path)}")
                self.log("Please wait...")
                if mode == "optimize":
                    result = self.optimize_file(path, output_dir, source_langs, target_langs)
                    if result:
                        batch_rows.append(result)
                    continue
                analyze_result = None
                if mode == "analyze" or self.analyze_before_split.get():
                    analyze_result = self.analyze_file(path, output_dir, source_langs, target_langs)
                    if mode == "analyze" and analyze_result:
                        batch_rows.append(analyze_result)
                if mode == "split":
                    created_files = self.split_file(path, output_dir, max_mb, part_tu_count, split_mode, prefix)
                    post_result = None
                    if created_files and self.post_check_after_split.get() and not self.cancel_event.is_set():
                        post_result = self.post_check_split_outputs(path, created_files, output_dir, source_langs, target_langs)
                    if created_files:
                        batch_rows.append(self.build_split_batch_result(path, created_files, post_result))
            if len(files) > 1 and batch_rows:
                self.write_batch_summary_report(output_dir, mode, batch_rows)
            self.queue.put(("progress", 100))
            self.queue.put(("done", "Finished."))
        except Exception as exc:
            self.queue.put(("error", str(exc)))

    def list_tmx_files_in_folder(self, folder, recursive=False):
        files = {}
        folder = os.path.abspath(folder)
        if recursive:
            for root_dir, _dirs, names in os.walk(folder):
                for name in names:
                    if name.lower().endswith(".tmx"):
                        path = os.path.join(root_dir, name)
                        rel = os.path.relpath(path, folder).replace("\\", "/")
                        files[rel.lower()] = {"key": rel, "path": path}
        else:
            for name in os.listdir(folder):
                path = os.path.join(folder, name)
                if os.path.isfile(path) and name.lower().endswith(".tmx"):
                    files[name.lower()] = {"key": name, "path": path}
        return files


    def build_compare_file_map(self, paths):
        files = {}
        valid_paths = [os.path.abspath(p) for p in paths if os.path.isfile(p) and p.lower().endswith(".tmx")]
        if len(valid_paths) == 1:
            name = os.path.basename(valid_paths[0])
            return {"selected_tmx_file": {"key": name, "path": valid_paths[0]}}
        for path in valid_paths:
            name = os.path.basename(path)
            key = name.lower()
            if key in files:
                base, ext = os.path.splitext(name)
                i = 2
                while f"{base}_{i}{ext}".lower() in files:
                    i += 1
                key = f"{base}_{i}{ext}".lower()
                name = f"{base}_{i}{ext}"
            files[key] = {"key": name, "path": path}
        return files

    def analyze_tmx_for_comparison(self, path, source_langs, target_langs):
        total = 0
        ok = 0
        counts = {
            "missing_source_lang": 0,
            "missing_target_lang": 0,
            "empty_source_seg": 0,
            "empty_target_seg": 0,
            "tag_only_source_seg": 0,
            "tag_only_target_seg": 0,
            "xml_parse_error": 0,
            "no_tuv_found": 0,
        }
        language_stats = {}
        last_update = time.time()
        for _line_no, tu_bytes in iter_tu_blocks(path):
            if self.cancel_event.is_set():
                return None
            total += 1
            info = analyze_tu(tu_bytes, source_langs, target_langs)
            merge_language_stats(language_stats, info.get("tuvs") or [])
            if info.get("ok"):
                ok += 1
            else:
                for problem in set(info.get("problems") or []):
                    if problem in counts:
                        counts[problem] += 1
            now = time.time()
            if now - last_update > 0.8:
                self.log(f"Compare analysis: {os.path.basename(path)} - TU {total}")
                last_update = now
        issues = sum(counts.values())
        return {
            "file": path,
            "file_name": os.path.basename(path),
            "size_bytes": os.path.getsize(path),
            "total_tu": total,
            "potentially_importable_tu": ok,
            "problem_tu": total - ok,
            "issues": issues,
            **counts,
            "language_stats": language_stats,
        }

    def comparison_file_row(self, side, key, data):
        if not data:
            return [side, key, "", "", "", "", "", "", "", "", "", "", "", "", ""]
        return [
            side,
            key,
            data.get("file", ""),
            data.get("size_bytes", 0),
            data.get("total_tu", 0),
            data.get("potentially_importable_tu", 0),
            data.get("problem_tu", 0),
            data.get("issues", 0),
            data.get("missing_source_lang", 0),
            data.get("missing_target_lang", 0),
            data.get("empty_source_seg", 0),
            data.get("empty_target_seg", 0),
            data.get("tag_only_source_seg", 0),
            data.get("tag_only_target_seg", 0),
            data.get("xml_parse_error", 0) + data.get("no_tuv_found", 0),
        ]

    def aggregate_comparison_metrics(self, items):
        metrics = {
            "files": len(items),
            "size_bytes": 0,
            "total_tu": 0,
            "potentially_importable_tu": 0,
            "problem_tu": 0,
            "issues": 0,
            "missing_source_lang": 0,
            "missing_target_lang": 0,
            "empty_source_seg": 0,
            "empty_target_seg": 0,
            "tag_only_source_seg": 0,
            "tag_only_target_seg": 0,
            "xml_parse_or_no_tuv": 0,
        }
        for data in items:
            if not data:
                continue
            metrics["size_bytes"] += data.get("size_bytes", 0)
            metrics["total_tu"] += data.get("total_tu", 0)
            metrics["potentially_importable_tu"] += data.get("potentially_importable_tu", 0)
            metrics["problem_tu"] += data.get("problem_tu", 0)
            metrics["issues"] += data.get("issues", 0)
            metrics["missing_source_lang"] += data.get("missing_source_lang", 0)
            metrics["missing_target_lang"] += data.get("missing_target_lang", 0)
            metrics["empty_source_seg"] += data.get("empty_source_seg", 0)
            metrics["empty_target_seg"] += data.get("empty_target_seg", 0)
            metrics["tag_only_source_seg"] += data.get("tag_only_source_seg", 0)
            metrics["tag_only_target_seg"] += data.get("tag_only_target_seg", 0)
            metrics["xml_parse_or_no_tuv"] += data.get("xml_parse_error", 0) + data.get("no_tuv_found", 0)
        return metrics

    def language_stats_sheet_for_compare(self, side, analyzed):
        rows = [["side", "file", "language", "tuv_count", "tu_count", "non_empty_seg_count", "empty_seg_count", "tag_only_seg_count"]]
        for key, data in sorted(analyzed.items()):
            for lang, vals in sorted((data.get("language_stats") or {}).items(), key=lambda x: (-x[1]["tuv_count"], x[0])):
                rows.append([
                    side,
                    key,
                    lang,
                    vals["tuv_count"],
                    vals["tu_count"],
                    vals["non_empty_seg_count"],
                    vals["empty_seg_count"],
                    vals["tag_only_seg_count"],
                ])
        return rows

    def compare_worker_main(self, selected_files_a, selected_files_b, output_dir, source_langs, target_langs):
        try:
            os.makedirs(output_dir, exist_ok=True)
            files_a = self.build_compare_file_map(selected_files_a)
            files_b = self.build_compare_file_map(selected_files_b)
            if not files_a:
                self.queue.put(("error", "TMX A selection does not contain valid TMX files."))
                return
            if not files_b:
                self.queue.put(("error", "TMX B selection does not contain valid TMX files."))
                return

            self.log(f"TMX A files: {len(files_a)}")
            self.log(f"TMX B files: {len(files_b)}")
            analyzed_a = {}
            analyzed_b = {}
            total_files = len(files_a) + len(files_b)
            done = 0

            for key, item in sorted(files_a.items(), key=lambda x: x[1]["key"].lower()):
                if self.cancel_event.is_set():
                    self.queue.put(("done", "Canceled."))
                    return
                self.queue.put(("overall", f"Compare: A {len(analyzed_a) + 1} / {len(files_a)}"))
                self.log(f"Analyzing TMX A: {item['key']}")
                analyzed_a[key] = self.analyze_tmx_for_comparison(item["path"], source_langs, target_langs)
                done += 1
                self.queue.put(("progress", done * 100 / max(1, total_files)))

            for key, item in sorted(files_b.items(), key=lambda x: x[1]["key"].lower()):
                if self.cancel_event.is_set():
                    self.queue.put(("done", "Canceled."))
                    return
                self.queue.put(("overall", f"Compare: B {len(analyzed_b) + 1} / {len(files_b)}"))
                self.log(f"Analyzing TMX B: {item['key']}")
                analyzed_b[key] = self.analyze_tmx_for_comparison(item["path"], source_langs, target_langs)
                done += 1
                self.queue.put(("progress", done * 100 / max(1, total_files)))

            all_keys = sorted(set(files_a) | set(files_b))
            matched = [key for key in all_keys if key in analyzed_a and key in analyzed_b]
            only_a = [key for key in all_keys if key in analyzed_a and key not in analyzed_b]
            only_b = [key for key in all_keys if key in analyzed_b and key not in analyzed_a]

            agg_a = self.aggregate_comparison_metrics([analyzed_a[k] for k in analyzed_a])
            agg_b = self.aggregate_comparison_metrics([analyzed_b[k] for k in analyzed_b])

            summary = [["metric", "folder_a", "folder_b", "delta_b_minus_a"]]
            for metric in [
                "files", "size_bytes", "total_tu", "potentially_importable_tu", "problem_tu", "issues",
                "missing_source_lang", "missing_target_lang", "empty_source_seg", "empty_target_seg",
                "tag_only_source_seg", "tag_only_target_seg", "xml_parse_or_no_tuv",
            ]:
                summary.append([metric, agg_a.get(metric, 0), agg_b.get(metric, 0), agg_b.get(metric, 0) - agg_a.get(metric, 0)])
            summary.extend([
                ["matched_files", len(matched), "", ""],
                ["only_in_tmx_a", len(only_a), "", ""],
                ["only_in_tmx_b", len(only_b), "", ""],
                ["tmx_a_files", "; ".join(selected_files_a), "", ""],
                ["tmx_b_files", "; ".join(selected_files_b), "", ""],
                ["source_langs", ",".join(sorted(source_langs)), "", ""],
                ["target_langs", ",".join(sorted(target_langs)), "", ""],
            ])

            header = [
                "side", "file_key", "path", "size_bytes", "total_tu", "potentially_importable_tu", "problem_tu", "issues",
                "missing_source_lang", "missing_target_lang", "empty_source_seg", "empty_target_seg",
                "tag_only_source_seg", "tag_only_target_seg", "xml_parse_or_no_tuv",
            ]
            files_sheet = [header]
            for key in sorted(analyzed_a):
                files_sheet.append(self.comparison_file_row("A", key, analyzed_a[key]))
            for key in sorted(analyzed_b):
                files_sheet.append(self.comparison_file_row("B", key, analyzed_b[key]))

            matched_sheet = [[
                "file_key", "a_total_tu", "b_total_tu", "delta_total_tu",
                "a_importable", "b_importable", "delta_importable",
                "a_problem_tu", "b_problem_tu", "delta_problem_tu",
                "a_issues", "b_issues", "delta_issues",
            ]]
            for key in matched:
                a = analyzed_a[key]
                b = analyzed_b[key]
                matched_sheet.append([
                    key,
                    a.get("total_tu", 0), b.get("total_tu", 0), b.get("total_tu", 0) - a.get("total_tu", 0),
                    a.get("potentially_importable_tu", 0), b.get("potentially_importable_tu", 0), b.get("potentially_importable_tu", 0) - a.get("potentially_importable_tu", 0),
                    a.get("problem_tu", 0), b.get("problem_tu", 0), b.get("problem_tu", 0) - a.get("problem_tu", 0),
                    a.get("issues", 0), b.get("issues", 0), b.get("issues", 0) - a.get("issues", 0),
                ])

            only_a_sheet = [["file_key", "path", "total_tu", "potentially_importable_tu", "problem_tu", "issues"]]
            for key in only_a:
                d = analyzed_a[key]
                only_a_sheet.append([key, d.get("file", ""), d.get("total_tu", 0), d.get("potentially_importable_tu", 0), d.get("problem_tu", 0), d.get("issues", 0)])
            only_b_sheet = [["file_key", "path", "total_tu", "potentially_importable_tu", "problem_tu", "issues"]]
            for key in only_b:
                d = analyzed_b[key]
                only_b_sheet.append([key, d.get("file", ""), d.get("total_tu", 0), d.get("potentially_importable_tu", 0), d.get("problem_tu", 0), d.get("issues", 0)])

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(output_dir, f"tost_compare_tmx_{timestamp}.xlsx")
            write_xlsx(report_path, [
                ("Summary", summary),
                ("Files", files_sheet),
                ("Matched files", matched_sheet),
                ("Only in A", only_a_sheet),
                ("Only in B", only_b_sheet),
                ("Language stats A", self.language_stats_sheet_for_compare("A", analyzed_a)),
                ("Language stats B", self.language_stats_sheet_for_compare("B", analyzed_b)),
            ])
            self.last_report_path = report_path
            self.log(f"Compare XLSX report: {report_path}")
            self.log("Compare summary:")
            self.log(f"  TMX A: files {agg_a['files']}, TU {agg_a['total_tu']}, importable {agg_a['potentially_importable_tu']}, problems {agg_a['problem_tu']}, issues {agg_a['issues']}")
            self.log(f"  TMX B: files {agg_b['files']}, TU {agg_b['total_tu']}, importable {agg_b['potentially_importable_tu']}, problems {agg_b['problem_tu']}, issues {agg_b['issues']}")
            self.log(f"  Matched files: {len(matched)} | Only in A: {len(only_a)} | Only in B: {len(only_b)}")
            self.set_result_summary_text(
                "Compare: "
                f"A files {agg_a['files']} / TU {agg_a['total_tu']} / importable {agg_a['potentially_importable_tu']} / problems {agg_a['problem_tu']} | "
                f"B files {agg_b['files']} / TU {agg_b['total_tu']} / importable {agg_b['potentially_importable_tu']} / problems {agg_b['problem_tu']} | "
                f"Matched {len(matched)} / Only A {len(only_a)} / Only B {len(only_b)}"
            )
            self.queue.put(("progress", 100))
            self.queue.put(("done", "Finished."))
        except Exception as exc:
            self.queue.put(("error", str(exc)))

    def optimize_file(self, path, output_dir, source_langs, target_langs):
        base = sanitize_filename(os.path.splitext(os.path.basename(path))[0])
        dry_run = bool(self.opt_dry_run.get())
        final_out_path = os.path.join(output_dir, f"{base}__tost_optimized.tmx")
        report_path = os.path.join(output_dir, f"{base}__tost_dry_run_report.xlsx" if dry_run else f"{base}__tost_optimization_report.xlsx")
        temp_dir = None
        if dry_run:
            temp_dir = tempfile.TemporaryDirectory(prefix="tost_dry_run_")
            out_path = os.path.join(temp_dir.name, f"{base}__tost_dry_run_temp.tmx")
        else:
            out_path = final_out_path
        input_size = os.path.getsize(path)

        remove_missing_source = bool(self.opt_remove_missing_source.get())
        remove_missing_target = bool(self.opt_remove_missing_target.get())
        remove_empty = bool(self.opt_remove_empty.get())
        remove_tag_only = bool(self.opt_remove_tag_only.get())
        remove_xml_errors = bool(self.opt_remove_xml_errors.get())
        remove_duplicates = bool(self.opt_remove_duplicates.get())
        warn_noisy = bool(self.opt_warn_noisy.get())
        remove_noisy = bool(self.opt_remove_noisy.get())
        remove_one_char_punct = bool(self.opt_remove_one_char_punct.get())
        noisy_set = parse_noisy_set(self.opt_noisy_segments.get())
        noisy_match_mode = self.noisy_mode_key(self.opt_noisy_match_mode.get()) if self.noisy_mode_key(self.opt_noisy_match_mode.get()) in ("Both source and target", "Either source or target") else "Both source and target"
        warn_min_length = bool(self.opt_warn_min_length.get())
        try:
            min_text_length = int(self.opt_min_text_length.get().strip())
            if min_text_length <= 0:
                min_text_length = 0
        except ValueError:
            min_text_length = 0
        report_inline_tag_mismatch = bool(self.opt_report_inline_tag_mismatch.get())
        strip_mismatched_inline_tags = bool(self.opt_strip_mismatched_inline_tags.get())
        strip_all_inline_tags = bool(self.opt_strip_all_inline_tags.get())
        keep_selected_pair = bool(self.opt_keep_selected_pair.get())
        normalize_source_lang = bool(self.opt_normalize_source_lang.get())
        normalize_target_lang = bool(self.opt_normalize_target_lang.get())
        normalize_source_code = self.opt_normalize_source_code.get().strip() or DEFAULT_NORMALIZE_SOURCE_LANG
        normalize_target_code = self.opt_normalize_target_code.get().strip() or DEFAULT_NORMALIZE_TARGET_LANG

        # If the user normalizes to a code that is not listed among source/target variants,
        # treat that code as part of the same selected language set for duplicate checks,
        # reports and output post-check. This keeps custom normalization usable without
        # forcing the user to duplicate the same value in Source langs / Target langs.
        source_langs = set(source_langs)
        target_langs = set(target_langs)
        if normalize_source_lang and normalize_source_code:
            source_langs.add(normalize_source_code.lower().replace("_", "-"))
        if normalize_target_lang and normalize_target_code:
            target_langs.add(normalize_target_code.lower().replace("_", "-"))

        header = []
        in_tu = False
        block = []
        line_no = 0
        start_line = 0
        bytes_read = 0
        writer = None

        total = 0
        kept = 0
        removed = 0
        issue_total = 0
        problem_tu_before = 0
        missing_source = 0
        missing_target = 0
        empty_source = 0
        empty_target = 0
        tag_only_source = 0
        tag_only_target = 0
        xml_parse_error = 0
        no_tuv = 0
        removed_duplicates = 0
        noisy_warnings = 0
        removed_noisy = 0
        removed_one_char = 0
        inline_tag_warnings = 0
        changed_inline_tag_tu = 0
        changed_language_pair_tu = 0
        language_stats_before = {}
        language_stats_after = {}
        duplicate_seen = {}

        removed_rows = [[
            "tu_number", "line", "remove_reason", "detected_problems", "languages", "tuv_count",
            "source_preview", "target_preview", "duplicate_kept_tu_number", "raw_tu_xml", "xml_error"
        ]]
        duplicate_rows = [[
            "removed_tu_number", "removed_line", "kept_tu_number", "reason",
            "source_preview", "target_preview", "removed_raw_tu_xml", "kept_raw_tu_xml"
        ]]
        noisy_rows = [[
            "tu_number", "line", "action", "reason", "source_text", "target_text", "raw_tu_xml"
        ]]
        inline_tag_rows = [[
            "tu_number", "line", "action", "reason", "source_tag_sequence", "target_tag_sequence",
            "source_preview", "target_preview", "raw_tu_xml"
        ]]
        changed_rows = [[
            "tu_number", "line", "change_type", "reason", "source_tag_sequence_before", "target_tag_sequence_before",
            "raw_tu_xml_before", "raw_tu_xml_after"
        ]]
        last_update = time.time()

        def basic_removal_reasons(info):
            problems = set(info.get("problems") or [])
            reasons = []
            if remove_missing_source and "missing_source_lang" in problems:
                reasons.append("missing_source_lang")
            if remove_missing_target and "missing_target_lang" in problems:
                reasons.append("missing_target_lang")
            if remove_empty and ("empty_source_seg" in problems or "empty_target_seg" in problems):
                if "empty_source_seg" in problems:
                    reasons.append("empty_source_seg")
                if "empty_target_seg" in problems:
                    reasons.append("empty_target_seg")
            if remove_tag_only and ("tag_only_source_seg" in problems or "tag_only_target_seg" in problems):
                if "tag_only_source_seg" in problems:
                    reasons.append("tag_only_source_seg")
                if "tag_only_target_seg" in problems:
                    reasons.append("tag_only_target_seg")
            if remove_xml_errors and "xml_parse_error" in problems:
                reasons.append("xml_parse_error")
            if remove_xml_errors and "no_tuv_found" in problems:
                reasons.append("no_tuv_found")
            return reasons

        def open_writer_once():
            nonlocal writer
            if writer is None:
                writer = open(out_path, "wb")
                for h in header:
                    writer.write(h)

        def append_removed_row(tu_number, tu_start_line, reasons, info, tuvs, tu_bytes, duplicate_kept_tu=""):
            source_preview = get_preview(select_text_for_langs(tuvs, source_langs))
            target_preview = get_preview(select_text_for_langs(tuvs, target_langs))
            removed_rows.append([
                tu_number,
                tu_start_line,
                ";".join(reasons),
                ";".join(info.get("problems") or []),
                ";".join(info.get("langs") or []),
                info.get("tuv_count", 0),
                source_preview,
                target_preview,
                duplicate_kept_tu,
                get_raw_xml_preview(tu_bytes),
                info.get("xml_error", ""),
            ])

        def handle_tu(tu_bytes, tu_start_line):
            nonlocal total, kept, removed, issue_total, problem_tu_before
            nonlocal missing_source, missing_target, empty_source, empty_target, tag_only_source, tag_only_target, xml_parse_error, no_tuv
            nonlocal removed_duplicates, noisy_warnings, removed_noisy, removed_one_char
            nonlocal inline_tag_warnings, changed_inline_tag_tu, changed_language_pair_tu
            total += 1
            info = analyze_tu(tu_bytes, source_langs, target_langs)
            tuvs = info.get("tuvs") or []
            merge_language_stats(language_stats_before, tuvs)

            problems = set(info.get("problems") or [])
            if problems:
                problem_tu_before += 1
            if "missing_source_lang" in problems:
                missing_source += 1
            if "missing_target_lang" in problems:
                missing_target += 1
            if "empty_source_seg" in problems:
                empty_source += 1
            if "empty_target_seg" in problems:
                empty_target += 1
            if "tag_only_source_seg" in problems:
                tag_only_source += 1
            if "tag_only_target_seg" in problems:
                tag_only_target += 1
            if "xml_parse_error" in problems:
                xml_parse_error += 1
            if "no_tuv_found" in problems:
                no_tuv += 1
            issue_total += len(problems)

            reasons = basic_removal_reasons(info)
            if reasons:
                removed += 1
                append_removed_row(total, tu_start_line, reasons, info, tuvs, tu_bytes)
                return

            original_tu_for_lang_changes = tu_bytes
            tu_bytes, lang_pair_changes = filter_and_normalize_tuvs(
                tu_bytes,
                source_langs,
                target_langs,
                keep_only_pair=keep_selected_pair,
                normalize_source=normalize_source_lang,
                normalize_target=normalize_target_lang,
                source_code=normalize_source_code,
                target_code=normalize_target_code,
            )
            if lang_pair_changes:
                changed_language_pair_tu += 1
                changed_rows.append([
                    total,
                    tu_start_line,
                    "language_pair_filter_or_normalize",
                    ";".join(lang_pair_changes),
                    "",
                    "",
                    get_raw_xml_preview(original_tu_for_lang_changes),
                    get_raw_xml_preview(tu_bytes),
                ])
                info = analyze_tu(tu_bytes, source_langs, target_langs)
                tuvs = info.get("tuvs") or []

            source_text, target_text = get_source_target_texts(tuvs, source_langs, target_langs)

            # Short/noisy segment checks are only applied to otherwise valid source-target pairs.
            noisy_pair = bool(source_text and target_text and noisy_list_pair_matches(source_text, target_text, noisy_set, noisy_match_mode))
            one_char_pair = bool(source_text and target_text and is_one_char_or_punctuation(source_text) and is_one_char_or_punctuation(target_text))
            short_length_pair = bool(warn_min_length and is_short_length_pair(source_text, target_text, min_text_length))
            if warn_noisy and (noisy_pair or one_char_pair or short_length_pair):
                noisy_warnings += 1
                reason = []
                if noisy_pair:
                    reason.append("noisy_segment_list_match")
                if one_char_pair:
                    reason.append("one_character_or_punctuation_pair")
                if short_length_pair:
                    reason.append("short_length_pair")
                noisy_rows.append([
                    total,
                    tu_start_line,
                    "warning",
                    ";".join(reason),
                    source_text,
                    target_text,
                    get_raw_xml_preview(tu_bytes),
                ])

            noisy_remove_reasons = []
            if remove_noisy and noisy_pair:
                noisy_remove_reasons.append("short_noisy_pair")
            if remove_one_char_punct and one_char_pair:
                noisy_remove_reasons.append("one_character_or_punctuation_pair")
            if noisy_remove_reasons:
                removed += 1
                if "short_noisy_pair" in noisy_remove_reasons:
                    removed_noisy += 1
                if "one_character_or_punctuation_pair" in noisy_remove_reasons:
                    removed_one_char += 1
                append_removed_row(total, tu_start_line, noisy_remove_reasons, info, tuvs, tu_bytes)
                if not warn_noisy:
                    noisy_rows.append([
                        total,
                        tu_start_line,
                        "removed",
                        ";".join(noisy_remove_reasons),
                        source_text,
                        target_text,
                        get_raw_xml_preview(tu_bytes),
                    ])
                return

            source_tag_sequence, target_tag_sequence = get_inline_tag_sequences(tu_bytes, source_langs, target_langs)
            tag_mismatch_reason = inline_tag_mismatch_reason(source_tag_sequence, target_tag_sequence)
            if tag_mismatch_reason and report_inline_tag_mismatch:
                inline_tag_warnings += 1
                inline_tag_rows.append([
                    total,
                    tu_start_line,
                    "warning",
                    tag_mismatch_reason,
                    ";".join(source_tag_sequence),
                    ";".join(target_tag_sequence),
                    get_preview(source_text),
                    get_preview(target_text),
                    get_raw_xml_preview(tu_bytes),
                ])

            should_strip_inline_tags = bool(strip_all_inline_tags or (strip_mismatched_inline_tags and tag_mismatch_reason))
            if should_strip_inline_tags:
                original_tu_bytes = tu_bytes
                stripped_tu_bytes = strip_inline_tags_from_bytes(tu_bytes)
                if stripped_tu_bytes != tu_bytes:
                    tu_bytes = stripped_tu_bytes
                    changed_inline_tag_tu += 1
                    changed_rows.append([
                        total,
                        tu_start_line,
                        "strip_inline_tags",
                        tag_mismatch_reason if tag_mismatch_reason else "strip_all_inline_tags",
                        ";".join(source_tag_sequence),
                        ";".join(target_tag_sequence),
                        get_raw_xml_preview(original_tu_bytes),
                        get_raw_xml_preview(tu_bytes),
                    ])
                    # Re-analyze modified TU so duplicate detection and language stats after cleanup
                    # reflect the actual output that will be written.
                    info = analyze_tu(tu_bytes, source_langs, target_langs)
                    tuvs = info.get("tuvs") or []
                    source_text, target_text = get_source_target_texts(tuvs, source_langs, target_langs)

            duplicate_key = make_duplicate_key(tuvs, source_langs, target_langs)
            if remove_duplicates and duplicate_key:
                if duplicate_key in duplicate_seen:
                    kept_info = duplicate_seen[duplicate_key]
                    removed += 1
                    removed_duplicates += 1
                    append_removed_row(total, tu_start_line, ["duplicate_source_target_pair"], info, tuvs, tu_bytes, kept_info["tu_number"])
                    duplicate_rows.append([
                        total,
                        tu_start_line,
                        kept_info["tu_number"],
                        "duplicate_source_target_pair",
                        get_preview(source_text),
                        get_preview(target_text),
                        get_raw_xml_preview(tu_bytes),
                        kept_info["raw_tu_xml"],
                    ])
                    return
                duplicate_seen[duplicate_key] = {
                    "tu_number": total,
                    "line": tu_start_line,
                    "raw_tu_xml": get_raw_xml_preview(tu_bytes),
                }

            open_writer_once()
            writer.write(tu_bytes)
            kept += 1
            merge_language_stats(language_stats_after, tuvs)

        self.log("Optimizing TMX...")
        if dry_run:
            self.log("Dry run: no optimized TMX will be created. TOST will generate the report only.")
        else:
            self.log(f"Output TMX: {out_path}")
        try:
            with open(path, "rb") as f:
                while True:
                    line = f.readline()
                    if not line:
                        break
                    line_no += 1
                    bytes_read += len(line)
                    if not in_tu:
                        if TU_START_RE.search(line):
                            in_tu = True
                            start_line = line_no
                            block = [line]
                            if TU_END_RE.search(line):
                                handle_tu(b"".join(block), start_line)
                                in_tu = False
                                block = []
                        else:
                            if writer is None:
                                header.append(line)
                    else:
                        block.append(line)
                        if TU_END_RE.search(line):
                            handle_tu(b"".join(block), start_line)
                            in_tu = False
                            block = []

                    now = time.time()
                    if now - last_update > 0.5:
                        pct = 0 if input_size == 0 else min(100, bytes_read * 100 / input_size)
                        self.queue.put(("progress", pct))
                        self.log(f"Optimize: {pct:.1f}% - TU {total}, kept {kept}, removed {removed}")
                        last_update = now

                    if self.cancel_event.is_set():
                        break
        finally:
            if writer is None and not self.cancel_event.is_set():
                open_writer_once()
            if writer is not None:
                write_closing(writer)
                writer.close()

        if self.cancel_event.is_set():
            self.log("Canceled during optimization.")
            if temp_dir is not None:
                try:
                    temp_dir.cleanup()
                except Exception:
                    pass
            return

        # Post-check the optimized file so the user can clearly distinguish
        # issues found in the original input from issues remaining in the output.
        post_total = 0
        post_ok = 0
        post_missing_source = 0
        post_missing_target = 0
        post_empty_source = 0
        post_empty_target = 0
        post_tag_only_source = 0
        post_tag_only_target = 0
        post_xml_parse_error = 0
        post_no_tuv = 0
        post_language_stats = {}
        for _post_line, _post_tu_bytes in iter_tu_blocks(out_path):
            post_total += 1
            post_info = analyze_tu(_post_tu_bytes, source_langs, target_langs)
            post_tuvs = post_info.get("tuvs") or []
            merge_language_stats(post_language_stats, post_tuvs)
            if post_info.get("ok"):
                post_ok += 1
            else:
                post_problems = set(post_info.get("problems") or [])
                if "missing_source_lang" in post_problems:
                    post_missing_source += 1
                if "missing_target_lang" in post_problems:
                    post_missing_target += 1
                if "empty_source_seg" in post_problems:
                    post_empty_source += 1
                if "empty_target_seg" in post_problems:
                    post_empty_target += 1
                if "tag_only_source_seg" in post_problems:
                    post_tag_only_source += 1
                if "tag_only_target_seg" in post_problems:
                    post_tag_only_target += 1
                if "xml_parse_error" in post_problems:
                    post_xml_parse_error += 1
                if "no_tuv_found" in post_problems:
                    post_no_tuv += 1

        before_error_rows = build_error_rows(kept, missing_source, missing_target, empty_source, empty_target, tag_only_source, tag_only_target, xml_parse_error, no_tuv)
        post_error_rows = build_error_rows(post_ok, post_missing_source, post_missing_target, post_empty_source, post_empty_target, post_tag_only_source, post_tag_only_target, post_xml_parse_error, post_no_tuv)
        post_issue_total = post_missing_source + post_missing_target + post_empty_source + post_empty_target + post_tag_only_source + post_tag_only_target + post_xml_parse_error + post_no_tuv

        summary_sheet = [
            ["metric", "value"],
            ["input_file", path],
            ["dry_run", dry_run],
            ["output_file", "DRY RUN - no optimized TMX created" if dry_run else final_out_path],
            ["source_langs", ",".join(sorted(source_langs))],
            ["target_langs", ",".join(sorted(target_langs))],
            ["total_tu", total],
            ["potentially_importable_before_cleanup", total - problem_tu_before],
            ["problem_tu_before_cleanup", problem_tu_before],
            ["kept_tu", kept],
            ["removed_tu", removed],
            ["detected_issues_before_cleanup", issue_total],
            ["output_postcheck_total_tu", post_total],
            ["output_postcheck_importable_tu", post_ok],
            ["output_postcheck_problem_tu", post_total - post_ok],
            ["output_postcheck_detected_issues", post_issue_total],
            ["remove_missing_source", remove_missing_source],
            ["remove_missing_target", remove_missing_target],
            ["remove_empty_source_or_target", remove_empty],
            ["remove_tag_only_source_or_target", remove_tag_only],
            ["remove_xml_errors", remove_xml_errors],
            ["remove_duplicates", remove_duplicates],
            ["warn_noisy", warn_noisy],
            ["remove_noisy", remove_noisy],
            ["remove_one_char_punctuation", remove_one_char_punct],
            ["noisy_segment_list", ", ".join(sorted(noisy_set))],
            ["report_inline_tag_mismatch", report_inline_tag_mismatch],
            ["strip_mismatched_inline_tags", strip_mismatched_inline_tags],
            ["strip_all_inline_tags", strip_all_inline_tags],
            ["keep_only_selected_source_target_pair", keep_selected_pair],
            ["normalize_source_language_code", normalize_source_lang],
            ["normalize_source_language_code_to", normalize_source_code],
            ["normalize_target_language_code", normalize_target_lang],
            ["normalize_target_language_code_to", normalize_target_code],
            ["missing_source_lang", missing_source],
            ["missing_target_lang", missing_target],
            ["empty_source_seg", empty_source],
            ["empty_target_seg", empty_target],
            ["tag_only_source_seg", tag_only_source],
            ["tag_only_target_seg", tag_only_target],
            ["xml_parse_error", xml_parse_error],
            ["no_tuv_found", no_tuv],
            ["removed_duplicate_tu", removed_duplicates],
            ["noisy_warning_tu", noisy_warnings],
            ["removed_noisy_tu", removed_noisy],
            ["removed_one_char_or_punctuation_tu", removed_one_char],
            ["inline_tag_warning_tu", inline_tag_warnings],
            ["changed_inline_tag_tu", changed_inline_tag_tu],
            ["changed_language_pair_tu", changed_language_pair_tu],
        ]
        before_error_sheet = [["Before cleanup / removed", "Count"]]
        before_error_sheet.extend([[name, count] for name, count in before_error_rows])
        extra_counts = [
            ("Removed TU", removed),
            ("Removed exact source-target duplicates", removed_duplicates),
            ("Short/noisy segment warnings", noisy_warnings),
            ("Removed by noisy segment list", removed_noisy),
            ("Removed one-character or punctuation-only pairs", removed_one_char),
            ("Inline-tag mismatch warnings", inline_tag_warnings),
            ("Changed TU: inline tags stripped", changed_inline_tag_tu),
            ("Changed TU: language pair / language codes", changed_language_pair_tu),
        ]
        for name, count in extra_counts:
            if count > 0:
                before_error_sheet.append([name, count])

        post_error_sheet = [["After optimization / post-check", "Count"]]
        post_error_sheet.extend([[name, count] for name, count in post_error_rows])

        before_sheet = [["language", "tuv_count", "tu_count", "non_empty_seg_count", "empty_seg_count", "tag_only_seg_count"]]
        for lang, vals in sorted(language_stats_before.items(), key=lambda x: (-x[1]["tuv_count"], x[0])):
            before_sheet.append([lang, vals["tuv_count"], vals["tu_count"], vals["non_empty_seg_count"], vals["empty_seg_count"], vals["tag_only_seg_count"]])

        after_sheet = [["language", "tuv_count", "tu_count", "non_empty_seg_count", "empty_seg_count", "tag_only_seg_count"]]
        for lang, vals in sorted(language_stats_after.items(), key=lambda x: (-x[1]["tuv_count"], x[0])):
            after_sheet.append([lang, vals["tuv_count"], vals["tu_count"], vals["non_empty_seg_count"], vals["empty_seg_count"], vals["tag_only_seg_count"]])

        post_lang_sheet = [["language", "tuv_count", "tu_count", "non_empty_seg_count", "empty_seg_count", "tag_only_seg_count"]]
        for lang, vals in sorted(post_language_stats.items(), key=lambda x: (-x[1]["tuv_count"], x[0])):
            post_lang_sheet.append([lang, vals["tuv_count"], vals["tu_count"], vals["non_empty_seg_count"], vals["empty_seg_count"], vals["tag_only_seg_count"]])

        write_xlsx(report_path, [
            ("Summary", summary_sheet),
            ("Before cleanup counts", before_error_sheet),
            ("Output post-check", post_error_sheet),
            ("Removed TUs", removed_rows),
            ("Removed duplicates", duplicate_rows),
            ("Noisy warnings", noisy_rows),
            ("Inline tag warnings", inline_tag_rows),
            ("Changed TUs", changed_rows),
            ("Language stats before", before_sheet),
            ("Language stats after", after_sheet),
            ("Post-check lang stats", post_lang_sheet),
        ])
        self.last_report_path = report_path
        self.last_optimized_tmx_path = None if dry_run else final_out_path
        self.last_removed_tus = self._rows_to_dicts(removed_rows)
        self.last_duplicate_tus = self._rows_to_dicts(duplicate_rows)
        self.last_noisy_warnings = self._rows_to_dicts(noisy_rows)
        self.last_inline_tag_warnings = self._rows_to_dicts(inline_tag_rows)
        self.last_changed_tus = self._rows_to_dicts(changed_rows)
        self.log(f"Optimization finished: kept {kept} TU, removed {removed} TU")
        if dry_run:
            self.log("Dry run finished: optimized TMX was not created.")
        else:
            self.log(f"Optimized TMX: {final_out_path}")
        self.log(f"Optimization XLSX report: {report_path}")
        self.log("Optimization summary:")
        self.log(f"  Input TU: {total}")
        self.log(f"  Potentially importable before cleanup: {total - problem_tu_before}")
        self.log(f"  Problem TU before cleanup: {problem_tu_before}")
        self.log(f"  Kept TU: {kept}")
        self.log(f"  Removed TU: {removed}")
        self.log(f"  Detected issues before cleanup: {issue_total}")
        self.log(f"  Output post-check TU: {post_total}")
        self.log(f"  Output potentially importable TU: {post_ok}")
        self.log(f"  Output problem TU: {post_total - post_ok}")
        self.log(f"  Output detected issues: {post_issue_total}")
        self.log(f"  Removed duplicate TU: {removed_duplicates}")
        self.log(f"  Noisy warnings: {noisy_warnings}")
        self.log(f"  Removed noisy TU: {removed_noisy}")
        self.log(f"  Removed one-character/punctuation TU: {removed_one_char}")
        self.log(f"  Inline tag mismatch warnings: {inline_tag_warnings}")
        self.log(f"  Changed TU with stripped inline tags: {changed_inline_tag_tu}")
        self.log("")
        changed_total = changed_inline_tag_tu + changed_language_pair_tu
        result_prefix = "Dry run - report only. " if dry_run else ""
        removal_label = "Would remove" if dry_run else "Removed"
        self.set_result_summary_text(
            result_prefix + "Before: "
            f"Total {total} | Importable {total - problem_tu_before} | Problems {problem_tu_before} | Issues {issue_total}\n"
            "After: "
            f"Total {post_total} | Importable {post_ok} | Problems {post_total - post_ok} | Issues {post_issue_total} | "
            f"{removal_label} {removed} | Duplicates {removed_duplicates} | Noisy {removed_noisy} | One-char/punctuation {removed_one_char} | Changed {changed_total}"
        )
        if temp_dir is not None:
            try:
                temp_dir.cleanup()
            except Exception:
                pass
        return {
            "mode": "optimize",
            "file": path,
            "total_tu": total,
            "importable_before": total - problem_tu_before,
            "problem_tu_before": problem_tu_before,
            "issues_before": issue_total,
            "kept_tu": kept,
            "removed_tu": removed,
            "output_total_tu": post_total,
            "output_importable_tu": post_ok,
            "output_problem_tu": post_total - post_ok,
            "output_issues": post_issue_total,
            "removed_duplicates": removed_duplicates,
            "noisy_warnings": noisy_warnings,
            "removed_noisy": removed_noisy,
            "removed_one_char_punctuation": removed_one_char,
            "inline_tag_warnings": inline_tag_warnings,
            "changed_inline_tag_tu": changed_inline_tag_tu,
            "changed_language_pair_tu": changed_language_pair_tu,
            "changed_tu": changed_inline_tag_tu + changed_language_pair_tu,
            "output_file": "" if dry_run else final_out_path,
            "report_file": report_path,
            "dry_run": dry_run,
        }

    def analyze_file(self, path, output_dir, source_langs, target_langs):
        base = sanitize_filename(os.path.splitext(os.path.basename(path))[0])
        report_path = os.path.join(output_dir, f"{base}__tost_analysis_report.xlsx")

        total = 0
        ok = 0
        missing_source = 0
        missing_target = 0
        empty_source = 0
        empty_target = 0
        tag_only_source = 0
        tag_only_target = 0
        xml_parse_error = 0
        no_tuv = 0
        language_stats = {}
        problem_rows = [[
            "tu_number", "line", "problems", "languages", "tuv_count",
            "source_preview", "target_preview", "raw_tu_xml", "xml_error"
        ]]
        problem_view_items = []
        last_update = time.time()

        self.log("Analyzing TMX language pairs...")
        for line_no, tu_bytes in iter_tu_blocks(path):
            if self.cancel_event.is_set():
                return
            total += 1
            info = analyze_tu(tu_bytes, source_langs, target_langs)
            tuvs = info.get("tuvs") or []
            merge_language_stats(language_stats, tuvs)

            if info["ok"]:
                ok += 1
            else:
                problems = set(info["problems"])
                if "missing_source_lang" in problems:
                    missing_source += 1
                if "missing_target_lang" in problems:
                    missing_target += 1
                if "empty_source_seg" in problems:
                    empty_source += 1
                if "empty_target_seg" in problems:
                    empty_target += 1
                if "tag_only_source_seg" in problems:
                    tag_only_source += 1
                if "tag_only_target_seg" in problems:
                    tag_only_target += 1
                if "xml_parse_error" in problems:
                    xml_parse_error += 1
                if "no_tuv_found" in problems:
                    no_tuv += 1

                source_preview = get_preview(select_text_for_langs(tuvs, source_langs))
                target_preview = get_preview(select_text_for_langs(tuvs, target_langs))
                raw_xml = get_raw_xml_preview(tu_bytes)
                row = [
                    total,
                    line_no,
                    ";".join(info["problems"]),
                    ";".join(info["langs"]),
                    info["tuv_count"],
                    source_preview,
                    target_preview,
                    raw_xml,
                    info["xml_error"],
                ]
                problem_rows.append(row)
                problem_view_items.append({
                    "tu_number": total,
                    "line": line_no,
                    "problems": ";".join(info["problems"]),
                    "languages": ";".join(info["langs"]),
                    "tuv_count": info["tuv_count"],
                    "source_preview": source_preview,
                    "target_preview": target_preview,
                    "raw_tu_xml": raw_xml,
                    "xml_error": info["xml_error"],
                })

            now = time.time()
            if now - last_update > 0.5:
                self.queue.put(("progress", min(100, total % 100)))
                self.log(f"Analyze: TU {total}, potentially importable {ok}, problems {total - ok}")
                last_update = now

        issue_total = missing_source + missing_target + empty_source + empty_target + tag_only_source + tag_only_target + xml_parse_error + no_tuv
        error_rows = build_error_rows(ok, missing_source, missing_target, empty_source, empty_target, tag_only_source, tag_only_target, xml_parse_error, no_tuv)
        error_sheet = [["Issue", "Count"]]
        error_sheet.extend([[name, count] for name, count in error_rows])

        summary_sheet = [
            ["metric", "value"],
            ["file", path],
            ["source_langs", ",".join(sorted(source_langs))],
            ["target_langs", ",".join(sorted(target_langs))],
            ["total_tu", total],
            ["potentially_importable_tu", ok],
            ["problem_tu", total - ok],
            ["total_detected_issues", issue_total],
            ["missing_source_lang", missing_source],
            ["missing_target_lang", missing_target],
            ["empty_source_seg", empty_source],
            ["empty_target_seg", empty_target],
            ["tag_only_source_seg", tag_only_source],
            ["tag_only_target_seg", tag_only_target],
            ["xml_parse_error", xml_parse_error],
            ["no_tuv_found", no_tuv],
        ]

        lang_sheet = [["language", "tuv_count", "tu_count", "non_empty_seg_count", "empty_seg_count", "tag_only_seg_count"]]
        for lang, vals in sorted(language_stats.items(), key=lambda x: (-x[1]["tuv_count"], x[0])):
            lang_sheet.append([
                lang,
                vals["tuv_count"],
                vals["tu_count"],
                vals["non_empty_seg_count"],
                vals["empty_seg_count"],
                vals["tag_only_seg_count"],
            ])

        write_xlsx(report_path, [
            ("Summary", summary_sheet),
            ("Error counts", error_sheet),
            ("Language statistics", lang_sheet),
            ("Problems", problem_rows),
        ])

        self.last_report_path = report_path
        self.last_problem_tus = problem_view_items

        self.log(f"XLSX report: {report_path}")
        self.log("")
        self.log("=" * 60)
        self.log(f"Analysis result for: {os.path.basename(path)}")
        self.log(f"Total TU: {total}")
        self.log(f"Potentially importable TU: {ok}")
        self.log(f"Problem TU: {total - ok}")
        self.log(f"Total detected issues: {issue_total}")
        self.set_result_summary_text(
            "Analysis: "
            f"Total TU {total} | Potentially importable {ok} | Problem TU {total - ok} | Issues {issue_total}"
        )
        self.log("")
        self.log("Error counts table:")
        max_name_len = max((len(name) for name, _ in error_rows), default=0)
        for problem_name, count in error_rows:
            self.log(f"  {problem_name.ljust(max_name_len)}  {count}")
        self.log("")
        self.log("Language statistics:")
        for lang, vals in sorted(language_stats.items(), key=lambda x: (-x[1]["tuv_count"], x[0]))[:20]:
            self.log(
                f"  {lang}: TUV {vals['tuv_count']}, TU {vals['tu_count']}, "
                f"non-empty {vals['non_empty_seg_count']}, empty {vals['empty_seg_count']}, tag-only {vals['tag_only_seg_count']}"
            )
        if len(language_stats) > 20:
            self.log(f"  ...and {len(language_stats) - 20} more language codes. See XLSX report.")
        if problem_view_items:
            self.log("")
            self.log("Use 'View problem TUs' to inspect the original XML of problematic units.")
        self.log("=" * 60)
        self.log("")
        return {
            "mode": "analyze",
            "file": path,
            "total_tu": total,
            "importable_before": ok,
            "problem_tu_before": total - ok,
            "issues_before": issue_total,
            "kept_tu": "",
            "removed_tu": "",
            "output_total_tu": "",
            "output_importable_tu": "",
            "output_problem_tu": "",
            "output_issues": "",
            "removed_duplicates": "",
            "noisy_warnings": "",
            "removed_noisy": "",
            "removed_one_char_punctuation": "",
            "inline_tag_warnings": "",
            "changed_tu": "",
            "output_file": "",
            "report_file": report_path,
            "dry_run": "",
        }

    def summarize_tmx_file(self, path, source_langs, target_langs):
        total = 0
        ok = 0
        issue_count = 0
        problem_tu = 0
        lang_counts = {}
        for _line_no, tu_bytes in iter_tu_blocks(path):
            if self.cancel_event.is_set():
                break
            total += 1
            info = analyze_tu(tu_bytes, source_langs, target_langs)
            for lang in info["langs"]:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            if info["ok"]:
                ok += 1
            else:
                problem_tu += 1
                issue_count += len(info["problems"])
        return {
            "file": path,
            "total_tu": total,
            "ok_tu": ok,
            "problem_tu": problem_tu,
            "issues": issue_count,
            "lang_counts": lang_counts,
        }

    def post_check_split_outputs(self, original_path, created_files, output_dir, source_langs, target_langs):
        base = sanitize_filename(os.path.splitext(os.path.basename(original_path))[0])
        report_path = os.path.join(output_dir, f"{base}__tost_split_post_check.xlsx")
        self.log("Post-checking created files...")

        rows = [["file", "total_tu", "potentially_importable_tu", "problem_tu", "detected_issues", "languages"]]
        lang_rows = [["file", "language", "tu_count"]]
        total_tu = 0
        total_ok = 0
        total_problem = 0
        total_issues = 0

        for idx, out_path in enumerate(created_files, 1):
            if self.cancel_event.is_set():
                return
            summary = self.summarize_tmx_file(out_path, source_langs, target_langs)
            total_tu += summary["total_tu"]
            total_ok += summary["ok_tu"]
            total_problem += summary["problem_tu"]
            total_issues += summary["issues"]
            langs = ";".join(sorted(summary["lang_counts"].keys()))
            rows.append([
                os.path.basename(out_path),
                summary["total_tu"],
                summary["ok_tu"],
                summary["problem_tu"],
                summary["issues"],
                langs,
            ])
            for lang, count in sorted(summary["lang_counts"].items(), key=lambda x: (-x[1], x[0])):
                lang_rows.append([os.path.basename(out_path), lang, count])
            pct = idx * 100 / max(1, len(created_files))
            self.queue.put(("progress", pct))
            self.log(f"Post-check: {idx} / {len(created_files)} - {os.path.basename(out_path)}")

        summary_rows = [
            ["metric", "value"],
            ["original_file", original_path],
            ["created_files", len(created_files)],
            ["total_tu", total_tu],
            ["potentially_importable_tu", total_ok],
            ["problem_tu", total_problem],
            ["detected_issues", total_issues],
        ]
        write_xlsx(report_path, [
            ("Summary", summary_rows),
            ("Created files", rows),
            ("Language statistics", lang_rows),
        ])
        self.log(f"Post-check XLSX report: {report_path}")
        self.log("Post-check result:")
        self.log(f"  Created files: {len(created_files)}")
        self.log(f"  Total TU in output: {total_tu}")
        self.log(f"  Potentially importable TU: {total_ok}")
        self.log(f"  Problem TU: {total_problem}")
        self.log(f"  Detected issues: {total_issues}")
        self.log("")
        self.set_result_summary_text(
            "Split post-check: "
            f"Created files {len(created_files)} | Total TU {total_tu} | Importable {total_ok} | Problem TU {total_problem} | Issues {total_issues}"
        )
        return {
            "created_files": len(created_files),
            "output_total_tu": total_tu,
            "output_importable_tu": total_ok,
            "output_problem_tu": total_problem,
            "output_issues": total_issues,
            "report_file": report_path,
        }

    def build_split_batch_result(self, original_path, created_files, post_result):
        post_result = post_result or {}
        return {
            "mode": "split",
            "file": original_path,
            "total_tu": "",
            "importable_before": "",
            "problem_tu_before": "",
            "issues_before": "",
            "kept_tu": "",
            "removed_tu": "",
            "output_total_tu": post_result.get("output_total_tu", ""),
            "output_importable_tu": post_result.get("output_importable_tu", ""),
            "output_problem_tu": post_result.get("output_problem_tu", ""),
            "output_issues": post_result.get("output_issues", ""),
            "created_files": len(created_files),
            "removed_duplicates": "",
            "noisy_warnings": "",
            "removed_noisy": "",
            "removed_one_char_punctuation": "",
            "inline_tag_warnings": "",
            "changed_tu": "",
            "output_file": ";".join(created_files),
            "report_file": post_result.get("report_file", ""),
            "dry_run": "",
        }

    def write_batch_summary_report(self, output_dir, mode, batch_rows):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(output_dir, f"tost_batch_summary_{mode}_{timestamp}.xlsx")
        headers = [
            "mode", "file", "total_tu", "importable_before", "problem_tu_before", "issues_before",
            "kept_tu", "removed_tu", "output_total_tu", "output_importable_tu",
            "output_problem_tu", "output_issues", "created_files", "removed_duplicates",
            "noisy_warnings", "removed_noisy", "removed_one_char_punctuation",
            "inline_tag_warnings", "changed_tu", "dry_run", "output_file", "report_file",
        ]
        rows = [headers]
        totals = {key: 0 for key in headers}
        for item in batch_rows:
            rows.append([item.get(h, "") for h in headers])
            for h in headers:
                val = item.get(h, "")
                if isinstance(val, (int, float)):
                    totals[h] += val
        summary = [
            ["metric", "value"],
            ["batch_mode", mode],
            ["files_processed", len(batch_rows)],
            ["total_tu", totals.get("total_tu", 0)],
            ["importable_before", totals.get("importable_before", 0)],
            ["problem_tu_before", totals.get("problem_tu_before", 0)],
            ["issues_before", totals.get("issues_before", 0)],
            ["kept_tu", totals.get("kept_tu", 0)],
            ["removed_tu", totals.get("removed_tu", 0)],
            ["output_total_tu", totals.get("output_total_tu", 0)],
            ["output_importable_tu", totals.get("output_importable_tu", 0)],
            ["output_problem_tu", totals.get("output_problem_tu", 0)],
            ["output_issues", totals.get("output_issues", 0)],
            ["created_files", totals.get("created_files", 0)],
            ["removed_duplicates", totals.get("removed_duplicates", 0)],
            ["noisy_warnings", totals.get("noisy_warnings", 0)],
            ["removed_noisy", totals.get("removed_noisy", 0)],
            ["removed_one_char_punctuation", totals.get("removed_one_char_punctuation", 0)],
            ["inline_tag_warnings", totals.get("inline_tag_warnings", 0)],
            ["changed_tu", totals.get("changed_tu", 0)],
        ]
        write_xlsx(report_path, [("Batch summary", summary), ("Files", rows)])
        self.last_report_path = report_path
        self.log(f"Batch summary XLSX report: {report_path}")
        self.set_result_summary_text(
            f"Batch {mode}: files {len(batch_rows)} | "
            f"Before importable {totals.get('importable_before', 0)} | Before problems {totals.get('problem_tu_before', 0)} | "
            f"After importable {totals.get('output_importable_tu', 0)} | After problems {totals.get('output_problem_tu', 0)} | "
            f"Removed {totals.get('removed_tu', 0)} | Changed {totals.get('changed_tu', 0)}"
        )

    def split_file(self, path, output_dir, max_mb, part_tu_count, split_mode, prefix):
        max_bytes = int(max_mb * 1024 * 1024)
        input_size = os.path.getsize(path)
        base = sanitize_filename(os.path.splitext(os.path.basename(path))[0])
        header = []
        in_tu = False
        block = []
        part_no = 0
        current_size = 0
        current_tu_count = 0
        writer = None
        total_tu = 0
        created_files = []
        current_out_path = None
        last_update = time.time()

        def header_size():
            return sum(len(h) for h in header)

        def open_part():
            nonlocal part_no, current_size, current_tu_count, writer, current_out_path
            part_no += 1
            out_name = f"{prefix}{part_no:02d}_{base}.tmx"
            current_out_path = os.path.join(output_dir, out_name)
            created_files.append(current_out_path)
            writer = open(current_out_path, "wb")
            for h in header:
                writer.write(h)
            current_size = header_size()
            current_tu_count = 0
            self.log(f"Writing part {part_no}: {out_name}")

        def should_open_next_part(tu_len):
            if writer is None:
                return False
            if current_tu_count <= 0:
                return False
            if split_mode == "tu":
                return current_tu_count >= part_tu_count
            return current_size + tu_len + 32 > max_bytes and current_size > header_size()

        def write_tu(tu):
            nonlocal writer, current_size, current_tu_count, total_tu
            if writer is None:
                open_part()
            if should_open_next_part(len(tu)):
                write_closing(writer)
                writer.close()
                open_part()
            writer.write(tu)
            current_size += len(tu)
            current_tu_count += 1
            total_tu += 1

        mode_label = f"TU count: {part_tu_count}" if split_mode == "tu" else f"file size: {max_mb:g} MB"
        self.log(f"Splitting TMX by {mode_label}...")
        bytes_read = 0
        try:
            with open(path, "rb") as f:
                while True:
                    line = f.readline()
                    if not line:
                        break
                    bytes_read += len(line)
                    if not in_tu:
                        if TU_START_RE.search(line):
                            in_tu = True
                            block = [line]
                            if TU_END_RE.search(line):
                                write_tu(b"".join(block))
                                in_tu = False
                                block = []
                        else:
                            if writer is None:
                                header.append(line)
                    else:
                        block.append(line)
                        if TU_END_RE.search(line):
                            write_tu(b"".join(block))
                            in_tu = False
                            block = []

                    now = time.time()
                    if now - last_update > 0.5:
                        pct = 0 if input_size == 0 else min(100, bytes_read * 100 / input_size)
                        self.queue.put(("progress", pct))
                        self.log(f"Split: {pct:.1f}% - part {part_no} - TU {total_tu}")
                        last_update = now

                    if self.cancel_event.is_set():
                        break
        finally:
            if writer is not None:
                write_closing(writer)
                writer.close()

        if self.cancel_event.is_set():
            self.log("Canceled during split.")
        else:
            self.log(f"Split finished: {total_tu} TU, {part_no} parts")
        return created_files


# Additional localization fixes added in v4.8.6 for optimization result viewer messages.
UI_TRANSLATIONS_RU.update({
    "No removed TUs are available. Run Optimize TMX first.": "Удаленные TU недоступны. Сначала запустите оптимизацию TMX.",
    "No removed duplicate TUs are available. Run Optimize TMX with duplicate removal enabled.": "Удаленные дубли TU недоступны. Запустите оптимизацию TMX с включенным удалением дублей.",
    "No noisy segment warnings are available. Run Optimize TMX first.": "Предупреждения о мусорных сегментах недоступны. Сначала запустите оптимизацию TMX.",
    "No inline-tag warnings are available. Run Optimize TMX first.": "Предупреждения по inline-тегам недоступны. Сначала запустите оптимизацию TMX.",
    "No changed TUs are available. Run Optimize TMX with language normalization or inline-tag stripping enabled.": "Измененные TU недоступны. Запустите оптимизацию TMX с включенной нормализацией языковых кодов или удалением inline-тегов.",
    "No rows are available yet.": "Строки пока недоступны.",
    "Removed TUs": "Удаленные TU",
    "Removed duplicate TUs": "Удаленные дубли TU",
    "Changed TUs": "Измененные TU",
    "Select a row to view details below.": "Выберите строку, чтобы посмотреть детали ниже.",
    "Details / raw XML": "Детали / raw XML",
})

def main():
    root = tk.Tk()
    apply_window_icon(root)
    app = TmxSplitterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

