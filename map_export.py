from qgis.core import *
from qgis.PyQt.QtWidgets import QApplication
import os
import processing
import traceback
from .plugin_dialog import *
from qgis.PyQt.QtCore import QEventLoop, QTimer
        
def delay(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec_()

def run_export(layout_name, img_output_folder, elv_output_folder, dem_layer_name, log_path):

    # === CONFIGURATION ===
    layout_name = layout_name
    img_output_folder = img_output_folder
    elv_output_folder = elv_output_folder
    log_path = log_path
    dem_layer_name = dem_layer_name

    # === SETUP ===
    project = QgsProject.instance()
    layout = project.layoutManager().layoutByName(layout_name)

    if layout is None:
        raise Exception("Layout not found. Check the layout name.")

    atlas = layout.atlas()
    exporter = QgsLayoutExporter(layout)
    coverage_layer = atlas.coverageLayer()
    map_item = layout.referenceMap()

    # Ensure output folders exist
    os.makedirs(img_output_folder, exist_ok=True)
    os.makedirs(elv_output_folder, exist_ok=True)

    # Find DEM layer - more flexible approach
    dem_layer = None
    for layer in QgsProject.instance().mapLayers().values():
        if isinstance(layer, QgsRasterLayer) and dem_layer_name in layer.name():
            dem_layer = layer
            break

    if not dem_layer:
        raise Exception(f"No suitable DEM layer found (looking for name containing '{dem_layer_name}').")

    # Start log
    with open(log_path, "a") as log:
        log.write("=== Starting export session ===\n")
        log.write(f"DEM layer found: {dem_layer.name()}\n")
    
    QApplication.processEvents()
    
    # === MAIN LOOP ===
    delay(200)
    atlas.beginRender()
    atlas.seekTo(-1)
    QApplication.processEvents()
    layout.refresh()
    
    retry_count = 0
    max_retries = 5
    
    for feature_number in range(atlas.count()):
        delay(200)
        print(feature_number)
        atlas.seekTo(feature_number)
        QApplication.processEvents()
        layout.refresh()
        
        # Get current feature - more robust approach
        coverage_layer = atlas.coverageLayer()
        feature = coverage_layer.getFeature(atlas.currentFeatureNumber())            
        fid = feature.id()
        
        if fid == -9223372036854775808:
            fid = feature_number
        
        if not feature.isValid():
            error_msg = f"Failed to export visual for tile {fid}"
            print(f"Feature {feature_number} invalid. Retrying... ({retry_count + 1}/{max_retries})")
            retry_count += 1
            delay(500)  # Give it more time to settle
            with open(log_path, "a") as log:
                log.write(f"{error_msg}\n")
        else:
            success = True

        # --- Export visual map ---
        visual_path = os.path.join(img_output_folder, f"map_{fid}_visual.tif")
        settings = QgsLayoutExporter.ImageExportSettings()
        settings.dpi = 300
        settings.exportGeoTIFF = True
        result = exporter.exportToImage(visual_path, settings)
        
        if result != QgsLayoutExporter.Success:
            
            print(f"{error_msg}")
            with open(log_path, "a") as log:
                log.write(f"{error_msg}\n")
            continue

        # --- Get extent of current tile ---
        extent = map_item.extent()
        dem_output_path = os.path.join(elv_output_folder, f"map_{fid}_elevation.tif")

        # --- Reproject extent from layout CRS to DEM CRS ---
        layout_crs = map_item.crs()
        dem_crs = dem_layer.crs()
        transform_context = QgsProject.instance().transformContext()
        xform = QgsCoordinateTransform(layout_crs, dem_crs, transform_context)
        
        try:
            reprojected_extent = xform.transformBoundingBox(extent)
            
            # Add small buffer to ensure we capture all elevation data
            buffered_extent = reprojected_extent.buffered(0.0002)  # ~20 meters at equator
            
            # --- Clip DEM to tile extent ---
            processing_params = {
                'INPUT': dem_layer,
                'PROJWIN': [
                    buffered_extent.xMinimum(),
                    buffered_extent.xMaximum(),
                    buffered_extent.yMinimum(),
                    buffered_extent.yMaximum()
                ],
                'NODATA': -9999,
                'OUTPUT': dem_output_path
            }
            
            # Try GDAL clip first, fall back to native QGIS clip if needed
            try:
                processing.run("gdal:cliprasterbyextent", processing_params)
            except Exception as gdal_err:
                print(f"GDAL clip failed, trying native clip: {gdal_err}")
                processing.run("gdal:warpreproject", {
                    'INPUT': dem_layer,
                    'SOURCE_CRS': dem_crs,
                    'TARGET_CRS': dem_crs,
                    'RESAMPLING': 0,
                    'NODATA': -9999,
                    'TARGET_RESOLUTION': dem_layer.rasterUnitsPerPixelX(),
                    'TARGET_EXTENT': buffered_extent,
                    'DATA_TYPE': 0,
                    'OUTPUT': dem_output_path
                })
            
            print(f"Tile {fid} exported: visual + elevation")
            with open(log_path, "a") as log:
                log.write(f"Tile {fid} exported: visual + elevation\n")
        
        except Exception as err:
            error_msg = f"Failed to process elevation for tile {fid}: {str(err)}\n{traceback.format_exc()}"
            print(f"{error_msg}")
            with open(log_path, "a") as log:
                log.write(f"{error_msg}\n")

        # --- Log extent and paths ---
        with open(log_path, "a") as log:
            log.write(f"Tile {fid} Visual: {visual_path}, Elevation: {dem_output_path}\n")
            log.write(f"Original Extent: {extent.toString()}\n")
            log.write(f"Reprojected Extent: {reprojected_extent.toString() if 'reprojected_extent' in locals() else 'N/A'}\n")
            log.write(f"Buffered Extent: {buffered_extent.toString() if 'buffered_extent' in locals() else 'N/A'}\n\n")

        atlas.next()
        
    atlas.endRender()
    return