from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsRectangle,
    QgsFields,
    QgsField,
    QgsProject,
    QgsSimpleFillSymbolLayer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsPointXY
)
from PyQt5.QtCore import QVariant, Qt
from qgis.PyQt.QtGui import QColor
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QMessageBox
from .plugin_dialog import *

def convert_to_meters(value, unit):
    conversions = {
        "meters": 1,
        "kilometers": 1000,
        "feet": 0.3048,
        "yards": 0.9144,
        "miles": 1609.34
    }
    if unit == "degrees":
        # We don't convert degrees — it's CRS-dependent and risky.
        raise ValueError("Grid spacing cannot be specified in degrees.")
    return value * conversions.get(unit, 1)

def meters_to_degrees(anchor_point, spacing_m, direction="horizontal", source_crs_code="EPSG:3857"):
    source_crs = QgsCoordinateReferenceSystem(source_crs_code)
    target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
    transformer = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())

    if direction == "horizontal":
        shifted = QgsPointXY(anchor_point.x() + spacing_m, anchor_point.y())
    else:
        shifted = QgsPointXY(anchor_point.x(), anchor_point.y() + spacing_m)

    pt1_deg = transformer.transform(anchor_point)
    pt2_deg = transformer.transform(shifted)

    return abs(pt2_deg.x() - pt1_deg.x()) if direction == "horizontal" else abs(pt2_deg.y() - pt1_deg.y())

def run_grid_generation(horizontal_spacing, vertical_spacing, horizontal_unit, vertical_unit, crs, extent):
    xmin, ymin, xmax, ymax = extent

    is_projected = not crs.startswith("EPSG:4326")

    try:
        h_spacing = convert_to_meters(horizontal_spacing, horizontal_unit)
        v_spacing = convert_to_meters(vertical_spacing, vertical_unit)
        print(f"Converted spacing: h={h_spacing} m × v={v_spacing} m")
    except ValueError as e:
        print("Unit conversion error:", e)
        return None

    if not is_projected:
        # Reject non-degree units in geographic CRS
        anchor = QgsPointXY((xmin + xmax) / 2, (ymin + ymax) / 2)

        if horizontal_unit != "degrees":
            h_spacing = meters_to_degrees(anchor, h_spacing, direction="horizontal")
        if vertical_unit != "degrees":
            v_spacing = meters_to_degrees(anchor, v_spacing, direction="vertical")

        print("Converted meters to degrees spacing: h={:.6f}°, v={:.6f}°".format(h_spacing, v_spacing))

    cols = int((xmax - xmin) / h_spacing)
    rows = int((ymax - ymin) / v_spacing)
    print(f"Grid dimensions: {cols} columns × {rows} rows")

    layer_uri = "Polygon?crs=" + crs.strip()
    print("Layer URI:", layer_uri)

    layer = QgsVectorLayer(layer_uri, "Grid", "memory")
    if not layer.isValid():
        print("Layer is invalid! Check CRS or URI formatting.")
        return None
    
    max_features = 100000
    estimated_features = cols * rows

    if estimated_features > max_features:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Grid Size Warning")
        msg.setText(f"The grid will generate approximately {estimated_features:,} tiles.")
        msg.setInformativeText("This may severely impact performance or crash QGIS on low-memory machines.\n\nDo you want to continue anyway?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        response = msg.exec_()

        if response == QMessageBox.No:
            return None
    
    provider = layer.dataProvider()
    fields = QgsFields()
    fields.append(QgsField("id", QVariant.Int))
    provider.addAttributes(fields)
    layer.updateFields()

    features = []
    fid = 0

    for col in range(cols):
        for row in range(rows):
            x1 = xmin + col * h_spacing
            x2 = x1 + h_spacing
            y1 = ymin + row * v_spacing
            y2 = y1 + v_spacing

            rect = QgsRectangle(x1, y1, x2, y2)
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromRect(rect))
            feat.setFields(fields)
            feat.setAttribute("id", fid)
            feat.setId(fid)
            fid += 1
            features.append(feat)

    provider.addFeatures(features)
    layer.updateExtents()
    print("Created features:", len(features))

    try:
        symbol = layer.renderer().symbol()
        symbol_layer = symbol.symbolLayer(0)
        if isinstance(symbol_layer, QgsSimpleFillSymbolLayer):
            symbol_layer.setStrokeColor(QColor(255, 0, 0))
            symbol_layer.setStrokeWidth(0.2)
            symbol_layer.setBrushStyle(Qt.NoBrush)
    except Exception as e:
        print("Styling error:", e)

    QgsProject.instance().addMapLayer(layer)
    print("Grid layer added to map.")
    return layer