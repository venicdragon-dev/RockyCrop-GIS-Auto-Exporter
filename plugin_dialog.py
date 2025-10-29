from qgis.PyQt import QtWidgets, QtGui
from qgis.PyQt.QtCore import Qt
from qgis.utils import iface
from qgis.core import QgsCoordinateReferenceSystem, QgsProject, QgsRectangle, QgsMapLayer, QgsRasterLayer
from PyQt5.QtWidgets import QDialog, QLineEdit, QLabel, QPushButton, QFileDialog, QMessageBox, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QLocale, QCoreApplication
from osgeo import gdal
import os
import traceback
from .grid_generation import run_grid_generation
from .draw_on_map import DrawOnMap, StartDrawOnMap
from .print_layout import create_print_layout
from .map_export import run_export
from .set_blender_file import prepare_blender_script
from .i18n_utils import save_locale_choice, load_saved_locale, load_json_locale

class PluginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, json_i18n=None):
        super().__init__(parent)
        self.setWindowTitle("RockyCrop Auto Exporter")
        self.setMinimumSize(900, 800)
        self._json_i18n = json_i18n or {}

        # == Form Layout Variables == #

        # -- Form Layouts -- #
        grid_size_layout = QtWidgets.QFormLayout()
        extent_layout = QtWidgets.QFormLayout()
        print_layout_layout = QtWidgets.QFormLayout()
        export_settings_layout = QtWidgets.QFormLayout()
        form_layout = QtWidgets.QFormLayout()

        # -- QH Box Layouts -- #
        self.hor_inputs = QtWidgets.QHBoxLayout()
        self.ver_inputs = QtWidgets.QHBoxLayout()
        self.extent_buttons = QtWidgets.QHBoxLayout()
        self.srtm_layer = QtWidgets.QHBoxLayout()
        self.visual_layout = QtWidgets.QHBoxLayout()
        self.elevation_layout = QtWidgets.QHBoxLayout()
        self.button_layout = QtWidgets.QHBoxLayout()
        self.content_layout = QtWidgets.QHBoxLayout()
        self.lang_btn_layout = QtWidgets.QHBoxLayout()
        lang_row = QtWidgets.QHBoxLayout()

        # -- Group Boxes -- #
        grid_settings_box = QtWidgets.QGroupBox("Grid Settings")
        print_layout_settings_box = QtWidgets.QGroupBox("Print Layout settings")
        manual_extent_group_box = QtWidgets.QGroupBox("Manual Extent Coordinates")
        export_settings_box = QtWidgets.QGroupBox("Export Settings")
        self.osm_options_groupbox = QtWidgets.QGroupBox("OSM Export Filters (Premium only)")
        self.lang_group = QtWidgets.QGroupBox("Language")

        # -- QV Box Layouts -- #
        main_layout = QtWidgets.QVBoxLayout()
        lang_group_layout = QtWidgets.QVBoxLayout()

        # === UI Box declaration === #

        # -- Double Spin Boxes -- #
        self.horizontal_spacing = QtWidgets.QDoubleSpinBox()
        self.vertical_spacing = QtWidgets.QDoubleSpinBox()
        self.page_height_input = QtWidgets.QDoubleSpinBox()
        self.page_width_input = QtWidgets.QDoubleSpinBox()

        # -- Combo Boxes -- #
        self.horizontal_unit = QtWidgets.QComboBox()
        self.vertical_unit = QtWidgets.QComboBox()
        self.crs_options = QtWidgets.QComboBox()
        self.lang_combo = QtWidgets.QComboBox()

        # -- Widgets -- #
        self.extent_buttons_wid = QtWidgets.QWidget()

        # === UI input declaration === #

        # -- Labels -- #
        self.grid_horizontal_label = QtWidgets.QLabel("Horizontal spacing:")
        self.grid_vertical_label = QtWidgets.QLabel("Vertical spacing:")
        self.grid_crs_label = QtWidgets.QLabel("CRS (EPSG Code):")
        self.horizontal_spacing_label = QtWidgets.QLabel("Degrees")
        self.vertical_spacing_label = QtWidgets.QLabel("Degrees")
        self.extent_minx_label = QtWidgets.QLabel("Min X:")
        self.extent_maxx_label = QtWidgets.QLabel("Max X:")
        self.extent_miny_label = QtWidgets.QLabel("Min Y:")
        self.extent_maxy_label = QtWidgets.QLabel("Max Y:")
        self.extent_choose_label = QtWidgets.QLabel("Choose extent:")
        self.layout_name_label = QtWidgets.QLabel("Layout Name:")
        self.page_width_label = QtWidgets.QLabel("Page Width (mm):")
        self.page_height_label = QtWidgets.QLabel("Page Height (mm):")
        self.elevation_srtm_label = QtWidgets.QLabel("SRTM Layer name:")
        self.visual_folder_label = QtWidgets.QLabel("Visual TIF Folder:")
        self.elevation_folder_label = QtWidgets.QLabel("Elevation TIF Folder:")
        self.lang_label = QtWidgets.QLabel("Language: ")

        # -- Set Ranges -- #
        self.horizontal_spacing.setRange(0.000001, 999999)
        self.vertical_spacing.setRange(0.000001, 999999)
        self.page_height_input.setRange(10, 1500)
        self.page_width_input.setRange(10, 1500)

        # -- Set Default Values -- #
        self.horizontal_spacing.setValue(200)
        self.vertical_spacing.setValue(200)
        self.page_width_input.setValue(50)
        self.page_height_input.setValue(50)

        # -- Add Items to Combo Boxes -- #
        self.horizontal_unit.addItems(["meters", "kilometers", "feet", "miles", "yards"])
        self.vertical_unit.addItems(["meters", "kilometers", "feet", "miles", "yards"])
        self.crs_options.addItems(["EPSG:3857 - Pseudo-Mercator", "EPSG:4326 - WGS 84", "EPSG:9008 - IGb00", "ESRI:104664 - Nepal_Nagarkot_3D"])

        # -- Line Edit inputs -- #
        self.min_x_input = QtWidgets.QLineEdit()
        self.max_x_input = QtWidgets.QLineEdit()
        self.min_y_input = QtWidgets.QLineEdit()
        self.max_y_input = QtWidgets.QLineEdit()
        self.layout_name_input = QtWidgets.QLineEdit()
        self.elevation_srtm_input = QtWidgets.QLineEdit()
        self.visual_folder_input = QtWidgets.QLineEdit()
        self.elevation_folder_input = QtWidgets.QLineEdit()

        # -- Atlas Checkbox - Do not change or remove -- #
        self.atlas_checkbox = QtWidgets.QCheckBox("Enable Atlas")

        # Extent Buttons
        self.extent_button = QtWidgets.QPushButton("Use Current Map Extent")
        self.draw_extent_button = QtWidgets.QPushButton("Draw Extent on Map")
        self.elevation_folder_button = QtWidgets.QPushButton("Browse...")
        self.visual_folder_button = QtWidgets.QPushButton("Browse...")
        self.run_button = QtWidgets.QPushButton("Start Process")
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.lang_apply_button = QtWidgets.QPushButton("Apply")

        # === Functionality === #

        # -- Set Print Layout Atlas to true -- #
        self.atlas_checkbox.setChecked(True) # Leave as true or your exports won't work

        # -- Set visibility of items -- #
        self.horizontal_spacing_label.setVisible(False)
        self.vertical_spacing_label.setVisible(False)

        # -- Buttons On Click -- #
        self.draw_tool = DrawOnMap(iface, self.min_x_input, self.max_x_input, self.min_y_input, self.max_y_input, self)
        self.extent_button.clicked.connect(self.populate_manual_extent_from_canvas)
        self.draw_extent_button.clicked.connect(self.draw_tool.activate_draw_extent)
        self.cancel_button.clicked.connect(self.reject)
        self.run_button.clicked.connect(self.accept)
        self.run_button.clicked.connect(self.generate_grid)
        self.visual_folder_button.clicked.connect(self.select_visual_folder)
        self.elevation_folder_button.clicked.connect(self.select_elevation_folder)
        self.lang_apply_button.clicked.connect(self.on_lang_change)

        # -- Force Sizes -- #
        self.extent_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.draw_extent_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # -- Change drop down -- #
        self.crs_options.currentIndexChanged.connect(self.updateGridUnit)

        # -- Add locales to Language Dropdown -- #

        # available locales: display text, item data = locale code
        self._available_locales = [
            ("English - en", "en"),
            ("Português (Brazil) - pt_BR", "pt_BR"),
            ("Español - es", "es"),
        ]
        for display, code in self._available_locales:
            self.lang_combo.addItem(display, code)

        # load saved locale and select it
        try:
            saved_code = load_saved_locale() or QLocale.system().name()
            idx = self.lang_combo.findData(saved_code)
            if idx >= 0:
                self.lang_combo.setCurrentIndex(idx)
        except Exception:
            pass

        # === Set Up UI layout === #

        # -- Grid Widgets -- #
        self.hor_inputs.addWidget(self.horizontal_spacing_label)
        self.hor_inputs.addWidget(self.horizontal_unit)
        self.hor_inputs.addWidget(self.horizontal_spacing)
        self.ver_inputs.addWidget(self.vertical_spacing_label)
        self.ver_inputs.addWidget(self.vertical_unit)
        self.ver_inputs.addWidget(self.vertical_spacing)

        # -- Extent Widgets -- #
        self.extent_buttons.addWidget(self.extent_button)
        self.extent_buttons.addWidget(self.draw_extent_button)

        # -- Export Widgets -- #
        self.srtm_layer.addWidget(self.elevation_srtm_input)
        self.visual_layout.addWidget(self.visual_folder_input)
        self.visual_layout.addWidget(self.visual_folder_button)
        self.elevation_layout.addWidget(self.elevation_folder_input)
        self.elevation_layout.addWidget(self.elevation_folder_button)

        # -- Run / Cancel Button Widgets -- #

        self.button_layout.addWidget(self.run_button)
        self.button_layout.addWidget(self.cancel_button)

        # -- Add Language Widgets -- #
        lang_row.addWidget(self.lang_label)
        lang_row.addWidget(self.lang_combo)
        lang_row.addWidget(self.lang_apply_button)
        lang_row.addStretch()

        # -- Add Rows -- #

        # -- Add Language Rows -- #

        lang_group_layout.addLayout(lang_row)
        self.lang_group.setLayout(lang_group_layout)

        # Grid Layout
        grid_size_layout.addRow(self.grid_horizontal_label, self.hor_inputs)
        grid_size_layout.addRow(self.grid_vertical_label, self.ver_inputs)
        grid_size_layout.addRow(self.grid_crs_label, self.crs_options)

        # Extent Layout
        self.extent_buttons_wid.setLayout(self.extent_buttons)
        extent_layout.addRow(self.extent_minx_label, self.min_x_input)
        extent_layout.addRow(self.extent_maxx_label, self.max_x_input)
        extent_layout.addRow(self.extent_miny_label, self.min_y_input)
        extent_layout.addRow(self.extent_maxy_label, self.max_y_input)
        extent_layout.addRow(self.extent_choose_label, self.extent_buttons_wid)

        # Print Layout Layout
        print_layout_layout.addRow(self.layout_name_label, self.layout_name_input)
        print_layout_layout.addRow(self.page_width_label, self.page_width_input)
        print_layout_layout.addRow(self.page_height_label, self.page_height_input)

        export_settings_layout.addRow(self.elevation_srtm_label, self.elevation_srtm_input)
        export_settings_layout.addRow(self.visual_folder_label, self.visual_layout)
        export_settings_layout.addRow(self.elevation_folder_label, self.elevation_layout)

        # -- Setting Layouts -- #

        grid_settings_box.setLayout(grid_size_layout)
        manual_extent_group_box.setLayout(extent_layout)
        print_layout_settings_box.setLayout(print_layout_layout)
        export_settings_box.setLayout(export_settings_layout)

        # Create form layout to hold main sections
        form_layout.addRow(grid_settings_box)
        form_layout.addRow(manual_extent_group_box)
        form_layout.addRow(print_layout_settings_box)
        form_layout.addRow(export_settings_box)
        form_layout.addRow(self.lang_group)

        # Horizontal layout to hold form + OSM sidebar
        self.content_layout.addLayout(form_layout)
        self.content_layout.addWidget(self.osm_options_groupbox)

        # Add bottom buttons
        self.button_layout.addWidget(self.run_button)
        self.button_layout.addWidget(self.cancel_button)

        # Final main layout
        main_layout.addLayout(self.content_layout)
        main_layout.addLayout(self.button_layout)
        self.setLayout(main_layout)

        try:
            self.retranslate_ui()
        except Exception:
            pass

    def on_lang_change(self):
        code = self.lang_combo.currentData()
        if not code:
            return
        save_locale_choice(code)

        json_map = load_json_locale(code, plugin_dir=os.path.dirname(__file__))
        if not json_map:
            QMessageBox.warning(self, "Language not loaded", f"Translation file not found for selected language ({code}).")
            return

        # store JSON map for retranslate_ui and apply immediately
        self._json_i18n = json_map
        try:
            self.retranslate_ui()
            QMessageBox.information(self, "Language changed", "Language applied.")
        except Exception:
            QMessageBox.information(self, "Language changed", "Language saved. Restart the plugin or QGIS to apply fully.")

    def retranslate_ui(self):
        # pick JSON map (cached if earlier stored)
        code = load_saved_locale() or QLocale.system().name()
        json_map = getattr(self, "_json_i18n", None)
        if json_map is None:
            json_map = load_json_locale(code, plugin_dir=os.path.dirname(__file__))
            self._json_i18n = json_map or {}

        def t(s):
            return self._json_i18n.get(s, s)

        # Window title and programmatic labels/buttons
        self.setWindowTitle(t("RockyCrop Auto Exporter"))
        self.grid_horizontal_label.setText(t("Horizontal spacing:"))
        self.grid_vertical_label.setText(t("Vertical spacing:"))
        self.grid_crs_label.setText(t("CRS (EPSG Code):"))
        self.horizontal_spacing_label.setText(t("Degrees"))
        self.vertical_spacing_label.setText(t("Degrees"))
        self.layout_name_label.setText(t("Layout Name:"))
        self.page_width_label.setText(t("Page Width (mm):"))
        self.page_height_label.setText(t("Page Height (mm):"))
        self.visual_folder_label.setText(t("Visual TIF Folder:"))
        self.elevation_folder_label.setText(t("Elevation TIF Folder:"))
        self.osm_export_label.setText(t("OSM Layer Export (Premium Only)"))
        self.lang_label.setText(t("Language:"))
        self.lang_apply_button.setText(t("Apply"))
        self.extent_choose_label.setText(t("Choose extent:"))
        self.extent_button.setText(t("Use Current Map Extent"))
        self.draw_extent_button.setText(t("Draw Extent on Map"))
        self.run_button.setText(t("Start Process"))
        self.cancel_button.setText(t("Cancel"))

        # update combo display texts if you prefer translated names there
        for i in range(self.lang_combo.count()):
            code = self.lang_combo.itemData(i)
            if code == "en":
                self.lang_combo.setItemText(i, t("English - en"))
            elif code == "pt_BR":
                self.lang_combo.setItemText(i, t("Português (Brasil) - pt_BR"))
            elif code == "es":
                self.lang_combo.setItemText(i, t("Español - es"))

    def updateGridUnit(self):
        selected_crs = self.crs_options.currentText()
        if "EPSG:4326 - WGS 84" in selected_crs or "EPSG:9008 - IGb00" in selected_crs or "ESRI:104664 - Nepal_Nagarkot_3D" in selected_crs:
            self.horizontal_spacing.setRange(0.000001, 100.0)
            self.horizontal_spacing.setSingleStep(0.000001)
            self.horizontal_spacing.setValue(0.1)
            self.vertical_spacing.setRange(0.000001, 100.0)
            self.vertical_spacing.setSingleStep(0.000001)
            self.vertical_spacing.setValue(0.1)
            self.horizontal_spacing.setDecimals(6)
            self.vertical_spacing.setDecimals(6)
            self.horizontal_unit.setVisible(False)
            self.vertical_unit.setVisible(False)
            self.horizontal_spacing_label.setVisible(True)
            self.vertical_spacing_label.setVisible(True)

        else:
            self.horizontal_spacing.setRange(100, 10000)
            self.horizontal_spacing.setSingleStep(100)
            self.horizontal_spacing.setValue(1000)
            self.vertical_spacing.setRange(100, 10000)
            self.vertical_spacing.setSingleStep(100)
            self.vertical_spacing.setValue(1000)
            self.horizontal_spacing.setDecimals(0)
            self.vertical_spacing.setDecimals(0)
            self.horizontal_unit.setVisible(True)
            self.vertical_unit.setVisible(True)
            self.horizontal_spacing_label.setVisible(False)
            self.vertical_spacing_label.setVisible(False)

    def select_visual_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Visual TIF Folder")
        if folder:
            self.visual_folder_input.setText(folder)

    def select_elevation_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Elevation TIF Folder")
        if folder:
            self.elevation_folder_input.setText(folder)

    def get_extent(self, method):
        project_crs = QgsProject.instance().crs()
        if method == "manual":
            try:
                min_x = float(self.min_x_input.text())
                min_y = float(self.min_y_input.text())
                max_x = float(self.max_x_input.text())
                max_y = float(self.max_y_input.text())
            except ValueError:
                raise ValueError("Invalid manual extent coordinates.")
            return QgsRectangle(min_x, min_y, max_x, max_y)

        elif method == "drawn":
            drawn_geom = self.get_drawn_geometry()  # Replace with actual method
            if not drawn_geom:
                raise ValueError("No drawn geometry found.")
            return drawn_geom.boundingBox()

        elif method == "canvas":
            return iface.mapCanvas().extent()

        else:
            raise ValueError(f"Unknown extent method: {method}")
            # CRS transformation
            transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())
            transformed_extent = transform.transformBoundingBox(extent)

            return transformed_extent

    def populate_manual_extent_from_canvas(self):
        extent = iface.mapCanvas().extent()
        self.min_x_input.setText(str(extent.xMinimum()))
        self.max_x_input.setText(str(extent.xMaximum()))
        self.min_y_input.setText(str(extent.yMinimum()))
        self.max_y_input.setText(str(extent.yMaximum()))

    def generate_grid(self):
        grid_size_hor = self.horizontal_spacing.value()
        grid_size_ver = self.vertical_spacing.value()
        grid_hor_unit = self.horizontal_unit.currentText()
        grid_ver_unit = self.vertical_unit.currentText()
        crs_text = self.crs_options.currentText()
        epsg_code = crs_text.split(" ")[0]
        grid_crs = QgsCoordinateReferenceSystem(epsg_code)
        crs_str = grid_crs.authid()

        print(f"Selected CRS text: '{self.crs_options.currentText()}'")
        print(f"Extracted CRS authid: '{crs_str}'")

        visual_path = self.visual_folder_input.text()
        elevation_path = self.elevation_folder_input.text()

        # Validate inputs
        if not visual_path or not elevation_path:
            QtWidgets.QMessageBox.warning(self, "Missing Paths", "Please select both Visual and Elevation folders.")
            return

        elif visual_path == elevation_path:
            QtWidgets.QMessageBox.warning(self, "Paths are the same", "Please ensure both the visual folder and elevation folder are different.")
            return

        # Extent handling
        user_extent = self.get_extent("manual")
        extent = [user_extent.xMinimum(), user_extent.yMinimum(), user_extent.xMaximum(), user_extent.yMaximum()]

        # Generate the grid
        grid_layer = run_grid_generation(
            horizontal_spacing = grid_size_hor,
            vertical_spacing = grid_size_ver,
            horizontal_unit = grid_hor_unit,
            vertical_unit = grid_ver_unit,
            crs = crs_str,
            extent = extent
        )

        # Add to map
        QgsProject.instance().addMapLayer(grid_layer)

        create_print_layout(
            project = QgsProject.instance(),
            coverage_layer = grid_layer,
            layout_name = self.layout_name_input.text(),
            page_width_mm = self.page_width_input.value(),
            page_height_mm = self.page_height_input.value()
        )

        # Setting up Blender code for use
        plugin_dir = os.path.dirname(__file__)
        prepare_blender_script(plugin_dir, visual_path, elevation_path, crs_str)
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export_log.txt")

        # --- Pick main map layer: first raster in canvas that's not the DEM ---
        self.main_map_layer = None
        dem_name = self.elevation_srtm_input.text().strip().lower()

        for lyr in iface.mapCanvas().layers():
            # Skip DEM by name (case-insensitive)
            if lyr.name().strip().lower() == dem_name:
                continue
            if lyr.type() == QgsMapLayer.RasterLayer:
                self.main_map_layer = lyr
                with open(log_path, "a") as log:
                    log.write(f"Main Map Layer: {lyr.name()}\n")
                break

        if self.main_map_layer:
            root = QgsProject.instance().layerTreeRoot()

            # Select basemap so new layers don’t nest under DEM
            node = root.findLayer(self.main_map_layer.id())
            if node:
                iface.layerTreeView().setCurrentLayer(self.main_map_layer)

            # Get/repair custom layer order
            order = root.customLayerOrder()

            # Rebuild if empty, missing our layer, or out of sync with the project
            if not order or self.main_map_layer not in order or len(order) != len(root.findLayers()):
                order = [node.layer() for node in root.findLayers()]

            # Move our layer to the front
            try:
                order.remove(self.main_map_layer)
            except ValueError:
                pass
            order.insert(0, self.main_map_layer)

            root.setCustomLayerOrder(order)
            root.setHasCustomLayerOrder(True)

            with open(log_path, "a") as log:
                log.write("main_map_layer moved to top in custom draw order.\n")
        else:
            with open(log_path, "a") as log:
                log.write("main_map_layer not found\n")

        # Run the export code
        try:
            run_export(
                layout_name=self.layout_name_input.text(),
                img_output_folder=self.visual_folder_input.text(),
                elv_output_folder=self.elevation_folder_input.text(),
                dem_layer_name=self.elevation_srtm_input.text(),
                log_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "export_log.txt")
            )
            QtWidgets.QMessageBox.information(self, "Export Complete", "Visual and elevation exports finished successfully.")
        except Exception as e:
            QtWidgets.QMessageBox.information(self, "Export Failed", "Visual and elevation exports have failed.")
            traceback.print_exc()

    def get_inputs(self):
        # Returns all input data as a dictionary for later use
        return {
            "horizontal_spacing": self.horizontal_spacing.value(),
            "horizontal_unit": self.horizontal_unit.currentText(),
            "vertical_spacing": self.vertical_spacing.value(),
            "vertical_unit": self.vertical_unit.currentText(),
            "crs": QgsCoordinateReferenceSystem(self.crs_options.currentText()),
            "layout_name": self.layout_name_input.text(),
            "visual_folder": self.visual_folder_input.text(),
            "elevation_folder": self.elevation_folder_input.text(),
            "page_width_mm": self.page_width_input.value(),
            "page_height_mm": self.page_height_input.value(),
            "atlas_enabled": self.atlas_checkbox.isChecked(),
            "extent_min_x": self.min_x_input.text(),
            "extent_max_x": self.max_x_input.text(),
            "extent_min_y": self.min_y_input.text(),
            "extent_max_y": self.max_y_input.text(),

        }

    def accept(self):
        inputs = self.get_inputs()
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        super().accept()