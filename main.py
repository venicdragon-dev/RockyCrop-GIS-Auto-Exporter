from qgis.PyQt.QtWidgets import QAction
from qgis.utils import iface
from qgis.PyQt.QtGui import QIcon
from .plugin_dialog import *
from . import resources
from .map_export import run_export

class RunGeneration:
    def __init__(self, iface):
        self.iface = iface
        self.grid_type = None
        self.grid_size = None
        self.selected_crs = None
        self.grid_extent = None
        self.layout_name = None
        self.page_width_mm = 50.0
        self.page_height_mm = 50.0
        self.map_scale = None
        self.atlas_enabled = True

    def initGui(self):
        self.action = QAction(QIcon(":/icons/LogoIcon.png"), "Start RockyCrop", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        iface.addToolBarIcon(self.action)
        iface.addPluginToMenu("&RockyCrop", self.action)

    def unload(self):
        iface.removeToolBarIcon(self.action)
        iface.removePluginMenu("&RockyCrop", self.action)
    
    import os  # Make sure this is at the top

    def run(self):
        dialog = PluginDialog()
        if dialog.exec_():
            inputs = dialog.get_inputs()

            self.include_osm_data = inputs.get("include_osm_data", False)
            self.osm_features = inputs.get("osm_features", [])
            self.osm_export_folder = inputs.get("osm_export_folder", "")

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

            print("Captured Inputs:", inputs)