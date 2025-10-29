def classFactory(iface):
    from .i18n_utils import load_saved_locale, load_json_locale
    import os
    saved_code = load_saved_locale() or ""
    json_map = load_json_locale(saved_code, plugin_dir=os.path.dirname(__file__)) or {}
    from .main import RunGeneration
    return RunGeneration(json_i18n=json_map)
