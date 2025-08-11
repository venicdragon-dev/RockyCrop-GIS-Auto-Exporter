from qgis.PyQt import QtWidgets, QtGui
from qgis.PyQt.QtCore import Qt
from qgis.utils import iface
from qgis.core import QgsCoordinateReferenceSystem, QgsProject, QgsRectangle
from PyQt5.QtWidgets import QDialog, QLineEdit, QLabel, QPushButton, QFileDialog
import os
import traceback
from .grid_generation import run_grid_generation
from .draw_on_map import DrawOnMap, StartDrawOnMap
from .print_layout import create_print_layout
from .map_export import run_export
from .set_blender_file import prepare_blender_script

class PluginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RockyCrop Auto Exporter")
        self.setMinimumSize(800, 600)

        # Grid Settings
        self.horizontal_spacing = QtWidgets.QDoubleSpinBox()
        self.horizontal_spacing.setRange(0.01, 10000)
        self.horizontal_spacing.setValue(1000)
        self.horizontal_unit = QtWidgets.QComboBox()
        self.horizontal_unit.addItems(["meters", "kilometers", "feet", "miles", "yards"])
        
        self.vertical_spacing = QtWidgets.QDoubleSpinBox()
        self.vertical_spacing.setRange(0.01, 10000)
        self.vertical_spacing.setValue(1000)
        self.vertical_unit = QtWidgets.QComboBox()
        self.vertical_unit.addItems(["meters", "kilometers", "feet", "miles", "yards"])
        self.horizontal_degrees = QtWidgets.QLabel("Degrees")
        self.vertical_degrees = QtWidgets.QLabel("Degrees")
        
        self.horizontal_degrees.setVisible(False)
        self.vertical_degrees.setVisible(False)
        
        grid_settings = QtWidgets.QGroupBox("Grid Settings")
        grid_settings_layout = QtWidgets.QFormLayout()
        
        hor_inputs = QtWidgets.QHBoxLayout()
        hor_inputs.addWidget(self.horizontal_spacing)
        hor_inputs.addWidget(self.horizontal_unit)
        hor_inputs.addWidget(self.horizontal_degrees)
        
        ver_inputs = QtWidgets.QHBoxLayout()
        ver_inputs.addWidget(self.vertical_spacing)
        ver_inputs.addWidget(self.vertical_unit)
        ver_inputs.addWidget(self.vertical_degrees)
        
        self.crs_options = QtWidgets.QComboBox()
        self.crs_options.addItems(["EPSG:3857 - Pseudo-Mercator", "EPSG:4326 - WGS 84", "EPSG:9008 - IGb00", "ESRI:104664 - Nepal_Nagarkot_3D"])
        
        self.crs_options.currentIndexChanged.connect(self.updateGridUnit)
        
        grid_settings_layout.addRow("Horizontal spacing:", hor_inputs)
        grid_settings_layout.addRow("Vertical spacing:", ver_inputs)
        grid_settings_layout.addRow("CRS (EPSG Code):", self.crs_options)
        
        grid_settings.setLayout(grid_settings_layout)
        
        # Manual Extent Inputs
        self.min_x_input = QtWidgets.QLineEdit()
        self.max_x_input = QtWidgets.QLineEdit()
        self.min_y_input = QtWidgets.QLineEdit()
        self.max_y_input = QtWidgets.QLineEdit()
        
        # Extent Buttons
        self.extent_button = QtWidgets.QPushButton("Use Current Map Extent")
        self.draw_extent_button = QtWidgets.QPushButton("Draw Extent on Map")
        extent_buttons = QtWidgets.QHBoxLayout()
        extent_buttons.addWidget(self.extent_button)
        extent_buttons.addWidget(self.draw_extent_button)
        extent_buttons_wid = QtWidgets.QWidget()
        extent_buttons_wid.setLayout(extent_buttons)

        # Group box to hold manual inputs
        self.manual_extent_group = QtWidgets.QGroupBox("Manual Extent Coordinates")
        manual_layout = QtWidgets.QFormLayout()
        manual_layout.addRow("Min X:", self.min_x_input)
        manual_layout.addRow("Max X:", self.max_x_input)
        manual_layout.addRow("Min Y:", self.min_y_input)
        manual_layout.addRow("Max Y:", self.max_y_input)
        manual_layout.addRow("Choose extent: ", extent_buttons_wid)
        self.manual_extent_group.setLayout(manual_layout)
        
        # Layout Settings
        print_layout_settings = QtWidgets.QGroupBox("Print Layout settings")
        self.layout_name_label = QtWidgets.QLabel("Layout Name:")
        self.layout_name_input = QtWidgets.QLineEdit()

        self.page_width_label = QtWidgets.QLabel("Page Width (mm):")
        self.page_width_input = QtWidgets.QDoubleSpinBox()
        self.page_width_input.setRange(10, 500)
        self.page_width_input.setValue(50)

        self.page_height_label = QtWidgets.QLabel("Page Height (mm):")
        self.page_height_input = QtWidgets.QDoubleSpinBox()
        self.page_height_input.setRange(10, 500)
        self.page_height_input.setValue(50)
        
        print_layout = QtWidgets.QFormLayout()
        print_layout.addRow(self.layout_name_label, self.layout_name_input)
        print_layout.addRow(self.page_width_label, self.page_width_input)
        print_layout.addRow(self.page_height_label, self.page_height_input)
        print_layout_settings.setLayout(print_layout)
        
        # Atlas Settings
        self.atlas_checkbox = QtWidgets.QCheckBox("Enable Atlas")
        self.atlas_checkbox.setChecked(True)

        # Run Controls
        self.run_button = QtWidgets.QPushButton("Start Process")
        self.cancel_button = QtWidgets.QPushButton("Cancel")

        # Layout Management
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(grid_settings)
        form_layout.addRow(self.manual_extent_group)
        
        # Do stuff when extent button clicked
        self.extent_button.clicked.connect(self.populate_manual_extent_from_canvas)
        self.draw_tool = DrawOnMap(iface, self.min_x_input, self.max_x_input, self.min_y_input, self.max_y_input, self)
        self.draw_extent_button.clicked.connect(self.draw_tool.activate_draw_extent)
        
        # Print Layout
        form_layout.addRow(print_layout_settings)

        # Set SRTM layer input
        self.elevation_srtm_label = QtWidgets.QLabel("SRTM Layer name:")
        self.elevation_srtm_input = QtWidgets.QLineEdit()
        
        # Visual TIF Export Folder
        self.visual_folder_label = QtWidgets.QLabel("Visual TIF Folder:")
        self.visual_folder_input = QtWidgets.QLineEdit()
        self.visual_folder_button = QtWidgets.QPushButton("Browse...")
        self.visual_folder_button.clicked.connect(self.select_visual_folder)

        # Elevation TIF Export Folder
        self.elevation_folder_label = QtWidgets.QLabel("Elevation TIF Folder:")
        self.elevation_folder_input = QtWidgets.QLineEdit()
        self.elevation_folder_button = QtWidgets.QPushButton("Browse...")
        self.elevation_folder_button.clicked.connect(self.select_elevation_folder)

        # Setup export settings layout
        export_settings = QtWidgets.QGroupBox("Export Settings:")
        export_settings_layout = QtWidgets.QFormLayout()

        # SRTM layer layout
        srtm_layer = QtWidgets.QHBoxLayout()
        export_settings_layout.addRow(self.elevation_srtm_label, self.elevation_srtm_input)

        # Visual File Export Folder
        visual_layout = QtWidgets.QHBoxLayout()
        visual_layout.addWidget(self.visual_folder_input)
        visual_layout.addWidget(self.visual_folder_button)
        export_settings_layout.addRow(self.visual_folder_label, visual_layout)

        # Elevation File Export Folder
        elevation_layout = QtWidgets.QHBoxLayout()
        elevation_layout.addWidget(self.elevation_folder_input)
        elevation_layout.addWidget(self.elevation_folder_button)
        export_settings_layout.addRow(self.elevation_folder_label, elevation_layout)
        
        export_settings.setLayout(export_settings_layout)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.cancel_button)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(export_settings)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # Connect buttons to functions
        self.cancel_button.clicked.connect(self.reject)
        self.run_button.clicked.connect(self.accept)
        self.run_button.clicked.connect(self.generate_grid)
        
    def updateGridUnit(self):
        selected_crs = self.crs_options.currentText()
        if "EPSG:4326 - WGS 84" in selected_crs or "EPSG:9008 - IGb00" in selected_crs or "ESRI:104664 - Nepal_Nagarkot_3D" in selected_crs:
            self.horizontal_spacing.setRange(0.01, 1.0)
            self.horizontal_spacing.setSingleStep(0.01)
            self.horizontal_spacing.setValue(0.1)
            self.vertical_spacing.setRange(0.01, 1.0)
            self.vertical_spacing.setSingleStep(0.01)
            self.vertical_spacing.setValue(0.1)
            self.horizontal_unit.setVisible(False)
            self.vertical_unit.setVisible(False)
            self.horizontal_degrees.setVisible(True)
            self.vertical_degrees.setVisible(True)
            
        else:
            self.horizontal_spacing.setRange(100, 10000)
            self.horizontal_spacing.setSingleStep(100)
            self.horizontal_spacing.setValue(1000)
            self.vertical_spacing.setRange(100, 10000)
            self.vertical_spacing.setSingleStep(100)
            self.vertical_spacing.setValue(1000)
            self.horizontal_unit.setVisible(True)
            self.vertical_unit.setVisible(True)
            self.horizontal_degrees.setVisible(False)
            self.vertical_degrees.setVisible(False)
            
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
        
        #Run the export code
        try:
            run_export(
                layout_name=self.layout_name_input.text(),
                img_output_folder = self.visual_folder_input.text(),
                elv_output_folder = self.elevation_folder_input.text(),
                dem_layer_name = self.elevation_srtm_input.text(),
                log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export_log.txt")
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
        }
    
    def accept(self):
        inputs = self.get_inputs()
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        super().accept()