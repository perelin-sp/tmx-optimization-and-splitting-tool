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
from tkinter import filedialog, messagebox, ttk
from xml.etree import ElementTree as ET

APP_TITLE = "TMX Optimization and Splitting Tool v4.0.1"
APP_SHORT_NAME = "TOST"
DEFAULT_MAX_MB = "250"
DEFAULT_PART_TU_COUNT = "50000"
DEFAULT_PREFIX = "part"
DEFAULT_SOURCE_LANGS = "en,en-us,en-gb"
DEFAULT_TARGET_LANGS = "ru,ru-ru"
DEFAULT_NORMALIZE_SOURCE_LANG = "en-US"
DEFAULT_NORMALIZE_TARGET_LANG = "ru-RU"


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
    icon_path = resource_path("tmx_splitter.ico")
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


def xlsx_cell(value, row, col):
    ref = f"{xlsx_col_name(col)}{row}"
    if value is None:
        value = ""
    if isinstance(value, bool):
        return f'<c r="{ref}" t="b"><v>{1 if value else 0}</v></c>'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}"><v>{value}</v></c>'
    text = escape(str(value), {'"': '&quot;'})
    return f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>'


def make_sheet_xml(rows):
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
    out.append('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">')
    out.append('<sheetData>')
    for r_idx, row in enumerate(rows, 1):
        out.append(f'<row r="{r_idx}">')
        for c_idx, value in enumerate(row, 1):
            out.append(xlsx_cell(value, r_idx, c_idx))
        out.append('</row>')
    out.append('</sheetData></worksheet>')
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
    workbook.append('</sheets></workbook>')
    rels.append('</Relationships>')

    root_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>\n</Relationships>'

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", ''.join(content_types))
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("xl/workbook.xml", ''.join(workbook))
        zf.writestr("xl/_rels/workbook.xml.rels", ''.join(rels))
        for idx, (_title, rows) in enumerate(safe_sheets, 1):
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", make_sheet_xml(rows))


class TmxSplitterApp:
    def __init__(self, root):
        self.root = root
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
        self.result_summary = tk.StringVar(value="Result summary: no analysis or optimization has been run yet.")

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
        self.profile_descriptions = {
            "General CAT-safe": "Safe default profile. Removes missing, empty and tag-only TU; reports noisy pairs and inline-tag mismatch. Does not remove duplicates, normalize language codes or strip inline tags.",
            "Strict import": "Stricter cleanup profile. Removes missing, empty, tag-only and malformed TU, removes exact duplicate source-target pairs, and reports noisy pairs and inline-tag mismatch. Does not normalize language codes by default.",
            "Smartcat-oriented": "CAT import-oriented profile using Smartcat as a practical reference. Keeps only the selected source-target pair, normalizes language codes to the user-defined values, removes missing/empty/tag-only TU, exact duplicates, configured noisy pairs and one-character/punctuation-only pairs, and reports inline-tag mismatch.",
            "Custom": "Manual profile. Keeps the current checkbox settings unchanged so you can tune cleanup rules yourself.",
        }

        self.load_settings()
        self.build_ui()
        self.root.after(100, self.process_queue)

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
        ttk.Button(buttons, text="Settings / About", command=self.show_settings_about).pack(side=tk.RIGHT)

        self.file_list = tk.Listbox(file_frame, height=3, selectmode=tk.EXTENDED)
        self.file_list.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        self.notebook = ttk.Notebook(main, height=430)
        self.notebook.pack(fill=tk.X, expand=False, pady=(3, 2))

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

        split_tab.columnconfigure(1, weight=1)

        # ------------------------------------------------------------------
        # Tab 2: Optimize TMX
        # ------------------------------------------------------------------
        optimize_tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(optimize_tab, text="Optimize TMX")

        opt_lang_box = ttk.LabelFrame(optimize_tab, text="Profile and language pair", padding=3)
        opt_lang_box.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 2))
        ttk.Label(opt_lang_box, text="Optimization profile:").grid(row=0, column=0, sticky="w")
        profile_button = ttk.Menubutton(opt_lang_box, textvariable=self.opt_profile, width=24)
        profile_button.grid(row=0, column=1, sticky="w", padx=6)
        profile_menu = tk.Menu(profile_button, tearoff=False)
        self.profile_values = ("General CAT-safe", "Strict import", "Smartcat-oriented", "Custom")
        for profile_name in self.profile_values:
            profile_menu.add_radiobutton(
                label=profile_name,
                variable=self.opt_profile,
                value=profile_name,
                command=self.hide_profile_menu_tooltip,
            )
        profile_button["menu"] = profile_menu
        self.profile_button = profile_button
        self.profile_menu = profile_menu
        self.profile_menu_tooltip = MenuItemToolTip(
            profile_menu,
            text_func=self.get_profile_description,
            delay_ms=2000,
        )
        ttk.Button(opt_lang_box, text="Apply profile", command=self.apply_optimization_profile).grid(row=0, column=2, sticky="w")
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

        optimize_tab.columnconfigure(0, weight=1)
        optimize_tab.columnconfigure(1, weight=1)

        # ------------------------------------------------------------------
        # Shared progress and log area
        # ------------------------------------------------------------------
        status_frame = ttk.Frame(main)
        status_frame.pack(fill=tk.X, pady=0)
        self.overall_label = ttk.Label(status_frame, text="Overall: idle")
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

    def show_settings_about(self):
        win = tk.Toplevel(self.root)
        win.title("Settings / About")
        win.geometry("720x560")
        win.transient(self.root)
        apply_window_icon(win)

        container = ttk.Frame(win, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        settings_box = ttk.LabelFrame(container, text="Default settings", padding=8)
        settings_box.pack(fill=tk.X)

        ttk.Label(settings_box, text="Default output folder:").grid(row=0, column=0, sticky="w")
        ttk.Entry(settings_box, textvariable=self.output_dir).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(settings_box, text="Browse...", command=self.choose_output).grid(row=0, column=2)

        ttk.Label(settings_box, text="Default part size, MB:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(settings_box, textvariable=self.max_mb, width=12).grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(settings_box, text="Default part TU count:").grid(row=2, column=0, sticky="w")
        ttk.Entry(settings_box, textvariable=self.part_tu_count, width=12).grid(row=2, column=1, sticky="w", padx=6)

        ttk.Label(settings_box, text="Default split mode:").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Radiobutton(settings_box, text="By MB", variable=self.split_mode, value="mb").grid(row=3, column=1, sticky="w", padx=6, pady=4)
        ttk.Radiobutton(settings_box, text="By TU count", variable=self.split_mode, value="tu").grid(row=3, column=1, sticky="w", padx=(90, 6), pady=4)

        ttk.Label(settings_box, text="Default prefix:").grid(row=4, column=0, sticky="w")
        ttk.Entry(settings_box, textvariable=self.prefix, width=12).grid(row=4, column=1, sticky="w", padx=6)

        ttk.Label(settings_box, text="Default source langs:").grid(row=5, column=0, sticky="w", pady=4)
        ttk.Entry(settings_box, textvariable=self.source_langs).grid(row=5, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(settings_box, text="Default target langs:").grid(row=6, column=0, sticky="w")
        ttk.Entry(settings_box, textvariable=self.target_langs).grid(row=6, column=1, sticky="ew", padx=6)

        ttk.Checkbutton(
            settings_box,
            text="Analyze TMX before splitting by default",
            variable=self.analyze_before_split,
        ).grid(row=7, column=1, sticky="w", padx=6, pady=(6, 0))
        ttk.Checkbutton(
            settings_box,
            text="Post-check created files after splitting by default",
            variable=self.post_check_after_split,
        ).grid(row=8, column=1, sticky="w", padx=6, pady=(1, 0))

        settings_actions = ttk.Frame(settings_box)
        settings_actions.grid(row=9, column=0, columnspan=3, sticky="w", pady=(10, 0))
        self.save_settings_btn = ttk.Button(settings_actions, text="Save settings", command=self.save_settings)
        self.save_settings_btn.pack(side=tk.LEFT)
        ttk.Button(settings_actions, text="Reset settings", command=self.reset_settings).pack(side=tk.LEFT, padx=6)
        ttk.Button(settings_actions, text="Open settings folder", command=self.open_settings_folder).pack(side=tk.LEFT)
        ttk.Button(settings_actions, text="Close", command=win.destroy).pack(side=tk.LEFT, padx=6)

        settings_box.columnconfigure(1, weight=1)

        about_box = ttk.LabelFrame(container, text="About", padding=8)
        about_box.pack(fill=tk.BOTH, expand=True, pady=10)
        ttk.Label(
            about_box,
            text=(
                f"{APP_TITLE}\n"
                "A safe TMX preparation utility for CAT import workflows.\n"
                "Current principle: preserve original TU content as much as possible and split only on <tu> boundaries.\n"
                "Original TMX files are read-only input and are never modified.\n\n"
                "Current tabs:\n"
                "• Split / Analyze - check TMX files and safely split them into smaller parts.\n"
                "• Optimize TMX - create cleaned TMX copies for safer CAT import.\n\n"
                "Smartcat is used as one strict import reference point, but the optimization workflow is intended to be CAT-system neutral."
            ),
            wraplength=650,
            justify=tk.LEFT,
        ).pack(anchor="w")

    def load_settings(self):
        path = get_settings_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
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
                self.opt_report_inline_tag_mismatch.set(bool(data.get("opt_report_inline_tag_mismatch", self.opt_report_inline_tag_mismatch.get())))
                self.opt_strip_mismatched_inline_tags.set(bool(data.get("opt_strip_mismatched_inline_tags", self.opt_strip_mismatched_inline_tags.get())))
                self.opt_strip_all_inline_tags.set(bool(data.get("opt_strip_all_inline_tags", self.opt_strip_all_inline_tags.get())))
                self.opt_keep_selected_pair.set(bool(data.get("opt_keep_selected_pair", self.opt_keep_selected_pair.get())))
                self.opt_normalize_source_lang.set(bool(data.get("opt_normalize_source_lang", self.opt_normalize_source_lang.get())))
                self.opt_normalize_target_lang.set(bool(data.get("opt_normalize_target_lang", self.opt_normalize_target_lang.get())))
                self.opt_normalize_source_code.set(data.get("opt_normalize_source_code", self.opt_normalize_source_code.get()) or DEFAULT_NORMALIZE_SOURCE_LANG)
                self.opt_normalize_target_code.set(data.get("opt_normalize_target_code", self.opt_normalize_target_code.get()) or DEFAULT_NORMALIZE_TARGET_LANG)
                self.opt_dry_run.set(bool(data.get("opt_dry_run", self.opt_dry_run.get())))
                profile = data.get("opt_profile", self.opt_profile.get())
                if profile in ("General CAT-safe", "Strict import", "Smartcat-oriented", "Custom"):
                    self.opt_profile.set(profile)
        except Exception:
            pass

    def save_settings(self):
        data = {
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
        }
        path = get_settings_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo(APP_TITLE, f"Settings saved:\n{path}")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Could not save settings:\n{exc}")

    def reset_settings(self):
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
        self.opt_report_inline_tag_mismatch.set(True)
        self.opt_strip_mismatched_inline_tags.set(False)
        self.opt_strip_all_inline_tags.set(False)
        self.opt_keep_selected_pair.set(False)
        self.opt_normalize_source_lang.set(False)
        self.opt_normalize_target_lang.set(False)
        self.opt_normalize_source_code.set(DEFAULT_NORMALIZE_SOURCE_LANG)
        self.opt_normalize_target_code.set(DEFAULT_NORMALIZE_TARGET_LANG)
        self.opt_profile.set("General CAT-safe")
        self.opt_dry_run.set(False)
        messagebox.showinfo(APP_TITLE, "Settings reset to defaults. Click Save settings to persist them.")

    def get_profile_description(self, profile):
        return self.profile_descriptions.get(profile, "")

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
            messagebox.showerror(APP_TITLE, f"Could not open output folder:\n{exc}")

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
            messagebox.showerror(APP_TITLE, f"Could not open settings folder:\n{exc}")

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
        self.cancel_btn.config(state=tk.NORMAL if running else tk.DISABLED)
        if hasattr(self, "save_settings_btn") and self.save_settings_btn.winfo_exists():
            self.save_settings_btn.config(state=state)

    def log(self, text):
        self.queue.put(("log", text))

    def set_result_summary_text(self, text):
        self.queue.put(("result_summary", text))

    def open_path(self, path, label="file"):
        if not path or not os.path.exists(path):
            messagebox.showinfo(APP_TITLE, f"No {label} has been created yet.")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Could not open {label}:\n{exc}")

    def open_last_report(self):
        self.open_path(self.last_report_path, "report")

    def open_optimized_tmx(self):
        self.open_path(self.last_optimized_tmx_path, "optimized TMX")

    def view_problem_tus(self):
        if not self.last_problem_tus:
            messagebox.showinfo(APP_TITLE, "No problem TUs are available. Run Analyze first.")
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
            messagebox.showinfo(APP_TITLE, message_if_empty)
            return

        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("1120x660")
        win.transient(self.root)
        apply_window_icon(win)

        container = ttk.Frame(win, padding=8)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text=f"{title}. Select a row to view details below.").pack(anchor="w", pady=(0, 6))

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

        detail_box = ttk.LabelFrame(container, text="Details / raw XML", padding=4)
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
            messagebox.showerror(APP_TITLE, "Output folder cannot be empty.")
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
            messagebox.showerror(APP_TITLE, f"Output folder is not writable:\n{output_dir}\n\n{exc}")
            return False

    def collect_optimize_warnings(self):
        warnings = []
        if getattr(self, "opt_dry_run", None) is not None and self.opt_dry_run.get():
            warnings.append("Dry run is enabled: TOST will create an XLSX report only and will not leave an optimized TMX file.")
        if self.opt_remove_duplicates.get():
            warnings.append("Remove exact duplicates keeps only the first source-target pair and removes later duplicates.")
        if self.opt_remove_noisy.get():
            warnings.append("Remove pairs matching the noisy segment list may delete valid short UI strings if the list is too broad.")
        if self.opt_remove_one_char_punct.get():
            warnings.append("Remove one-character or punctuation-only pairs can delete legitimate UI labels such as symbols or numbered options.")
        if self.opt_strip_mismatched_inline_tags.get():
            warnings.append("Strip inline tags only from mismatched TUs changes segment content in affected TU blocks.")
        if self.opt_strip_all_inline_tags.get():
            warnings.append("Strip inline tags from all kept TUs changes segment content across the optimized TMX.")
        if self.opt_normalize_source_lang.get() or self.opt_normalize_target_lang.get():
            warnings.append("Language normalization rewrites xml:lang values in the optimized TMX.")
        if self.opt_keep_selected_pair.get():
            warnings.append("Keep only selected source-target language pair removes other languages from multilingual TU blocks.")
        if self.opt_remove_xml_errors.get():
            warnings.append("Remove XML parse errors / malformed TU is aggressive; malformed blocks will be excluded from the optimized TMX.")
        return warnings

    def confirm_optimize_warnings(self):
        warnings = self.collect_optimize_warnings()
        if not warnings:
            return True
        text = "The selected optimization settings may change or remove TMX content:\n\n"
        text += "\n".join(f"- {w}" for w in warnings)
        text += "\n\nOriginal TMX files are never modified. Continue?"
        return messagebox.askyesno(APP_TITLE, text)

    def start_worker(self, mode):
        if not self.files:
            messagebox.showwarning(APP_TITLE, "Please add at least one TMX file.")
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
                    messagebox.showerror(APP_TITLE, "Part size must be a positive number.")
                    return
            else:
                try:
                    part_tu_count = int(self.part_tu_count.get().strip())
                    if part_tu_count <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror(APP_TITLE, "Part TU count must be a positive integer.")
                    return

        source_langs = parse_lang_set(self.source_langs.get())
        target_langs = parse_lang_set(self.target_langs.get())
        if not source_langs or not target_langs:
            messagebox.showerror(APP_TITLE, "Source langs and target langs cannot be empty.")
            return
        if source_langs & target_langs:
            overlap = ", ".join(sorted(source_langs & target_langs))
            if not messagebox.askyesno(APP_TITLE, f"Source and target language lists overlap: {overlap}\n\nContinue anyway?"):
                return

        if mode == "optimize":
            if self.opt_remove_noisy.get() and not parse_noisy_set(self.opt_noisy_segments.get()):
                messagebox.showerror(APP_TITLE, "Noisy segment list is empty, but noisy segment removal is enabled.")
                return
            if self.opt_normalize_source_lang.get():
                code = self.opt_normalize_source_code.get().strip()
                if code and not self.is_valid_language_code(code):
                    messagebox.showerror(APP_TITLE, f"Invalid source language code for normalization: {code}")
                    return
            if self.opt_normalize_target_lang.get():
                code = self.opt_normalize_target_code.get().strip()
                if code and not self.is_valid_language_code(code):
                    messagebox.showerror(APP_TITLE, f"Invalid target language code for normalization: {code}")
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
                    self.overall_label.config(text="Overall: done")
                    messagebox.showinfo(APP_TITLE, payload)
                elif kind == "error":
                    self.set_running(False)
                    self.overall_label.config(text="Overall: error")
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
                self.queue.put(("overall", f"Overall: {index} / {len(files)}"))
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
            noisy_pair = bool(source_text and target_text and is_noisy_segment(source_text, noisy_set) and is_noisy_segment(target_text, noisy_set))
            one_char_pair = bool(source_text and target_text and is_one_char_or_punctuation(source_text) and is_one_char_or_punctuation(target_text))
            if warn_noisy and (noisy_pair or one_char_pair):
                noisy_warnings += 1
                reason = []
                if noisy_pair:
                    reason.append("noisy_segment_list_match")
                if one_char_pair:
                    reason.append("one_character_or_punctuation_pair")
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


def main():
    root = tk.Tk()
    apply_window_icon(root)
    app = TmxSplitterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
