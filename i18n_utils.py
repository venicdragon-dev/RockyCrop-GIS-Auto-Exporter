from PyQt5.QtCore import QSettings, QLocale, QTranslator, QCoreApplication
import os
import json

SETTINGS_KEY = "rockycrop/locale"

def save_locale_choice(locale_code):
    settings = QSettings()
    settings.setValue(SETTINGS_KEY, locale_code)

def load_saved_locale():
    settings = QSettings()
    v = settings.value(SETTINGS_KEY, "")
    return v or ""

def _load_json(plugin_dir, code):
    i18n_dir = os.path.join(plugin_dir, "i18n")
    if not os.path.isdir(i18n_dir):
        return {}
    cand_files = []
    if code:
        cand_files.append(f"{code}.json")
        if "_" in code:
            cand_files.append(code.split("_")[0] + ".json")
    cand_files.append("en.json")
    for fname in cand_files:
        path = os.path.join(i18n_dir, fname)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception:
                continue
    return {}

def load_json_locale(code, plugin_dir=None):
    if not plugin_dir:
        plugin_dir = os.path.dirname(__file__)
    return _load_json(plugin_dir, code)