from qgis.PyQt.QtWidgets import QAction
from qgis.utils import iface
from qgis.PyQt.QtGui import QIcon
from .plugin_dialog import *
from . import resources
from .map_export import run_export
from .i18n_utils import load_saved_locale, load_json_locale


class RunGeneration:
    def __init__(self, json_i18n=None):
        self.iface = iface
        self._json_i18n = json_i18n or {}
        self.grid_size = None
        self.selected_crs = None
        self.grid_extent = None
        self.layout_name = None
        self.page_width_mm = 50.0
        self.page_height_mm = 50.0
        self.map_scale = None
        self.atlas_enabled = True

        saved_code = load_saved_locale() or ""
        self._json_i18n = load_json_locale(saved_code, plugin_dir=os.path.dirname(__file__)) or {}

    def initGui(self):
        self.action = QAction(QIcon(":/icons/LogoIcon.png"), "Start RockyCrop", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        iface.addToolBarIcon(self.action)
        iface.addPluginToMenu("&RockyCrop", self.action)

    def unload(self):
        iface.removeToolBarIcon(self.action)
        iface.removePluginMenu("&RockyCrop", self.action)

    def run(self):
        dialog = PluginDialog(parent=iface.mainWindow(), json_i18n=self._json_i18n)
        if dialog.exec_():
            inputs = dialog.get_inputs()

            # Assign plugin-level attributes
            self.grid_horizontal = inputs["horizontal_spacing"]
            self.grid_vertical = inputs["vertical_spacing"]
            self.grid_hor_unit = inputs["horizontal_unit"]
            self.grid_ver_unit = inputs["vertical_unit"]
            self.selected_crs = inputs["crs"]
            self.grid_extent = None
            self.layout_name = inputs["layout_name"]
            self.page_width_mm = inputs["page_width_mm"]
            self.page_height_mm = inputs["page_height_mm"]
            self.atlas_enabled = True

            # OSM Export Settings
            self.osm_export_folder = inputs["osm_export_folder"]
            self.osm_enabled = inputs["osm_enabled"]
            self.osm_object_types = inputs.get("osm_object_types", {})
            self.osm_filters = inputs.get("osm_filters", {})

            print(f"Captured Inputs:", inputs)