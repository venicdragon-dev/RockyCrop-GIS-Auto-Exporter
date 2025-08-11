from qgis.core import (
    QgsProject,
    QgsLayoutManager,
    QgsPrintLayout,
    QgsLayoutSize,
    QgsLayoutPoint,
    QgsUnitTypes,
    QgsLayoutItemMap,
    QgsLayoutAtlas,
    QgsLayoutExporter,
    QgsVectorLayer,
    QgsCoordinateTransform,
)
from qgis.PyQt.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer

def create_print_layout(project, coverage_layer, layout_name, page_width_mm, page_height_mm):
    atlas_enabled = True
    manager = project.layoutManager()

    # Remove any existing layout with same name
    existing = manager.layoutByName(layout_name)
    if existing:
        manager.removeLayout(existing)

    # Initialize new layout
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(layout_name)
    manager.addLayout(layout)

    # Set custom page size
    page = layout.pageCollection().pages()[0]
    page.setPageSize(QgsLayoutSize(page_width_mm, page_height_mm, QgsUnitTypes.LayoutMillimeters))

    # Create and configure map item to match user-defined page size
    map_item = QgsLayoutItemMap(layout)
    layout.addLayoutItem(map_item)

    map_item.attemptMove(QgsLayoutPoint(0, 0, QgsUnitTypes.LayoutMillimeters))
    map_item.attemptResize(QgsLayoutSize(page_width_mm, page_height_mm, QgsUnitTypes.LayoutMillimeters))
    map_item.setFrameEnabled(False)

    # Lock coverage layer to ensure rendering
    map_item.setLayers([coverage_layer])
    map_item.setKeepLayerStyles(False)

    if atlas_enabled:
        # Set up Atlas
        atlas = layout.atlas()
        atlas.setEnabled(True)
        atlas.setCoverageLayer(coverage_layer)
        atlas.setPageNameExpression('"id"')
        map_item.setAtlasDriven(True)
        map_item.setAtlasScalingMode(QgsLayoutItemMap.Fixed)
        map_item.setAtlasMargin(0.0)
        

        # Safe zoom to first feature's extent
        features = list(coverage_layer.getFeatures())
        if features:
            first_geom = features[0].geometry()
            if not first_geom or first_geom.isNull():
                QMessageBox.warning(None, "Geometry Error", "First feature geometry is null.")
                return

            # Transform bounding box to project CRS if needed
            if coverage_layer.crs() != QgsProject.instance().crs():
                transformer = QgsCoordinateTransform(
                    coverage_layer.crs(), QgsProject.instance().crs(), QgsProject.instance())
                bbox = transformer.transformBoundingBox(first_geom.boundingBox())
            else:
                bbox = first_geom.boundingBox()

            print("Zooming to bbox:", bbox.toString())
            map_item.zoomToExtent(bbox)
        else:
            QMessageBox.warning(None, "Atlas Error", "No features found in coverage layer.")
            return
    
    def lock(map_item):
        # Lock the actual layer set
        map_item.setLayers(map_item.layers())
        map_item.setKeepLayerStyles(False)

        def unlock():
            map_item.setLayers([])  # Clear lock
            map_item.refresh()
            layout.atlas().beginRender()
            layout.refresh()

        QTimer.singleShot(1000, unlock)

    lock(map_item)

    print(f"Layout '{layout_name}' created at {page_width_mm}mm × {page_height_mm}mm. Atlas: {'enabled' if atlas_enabled else 'disabled'}")