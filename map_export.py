from qgis.core import *
from qgis.PyQt.QtWidgets import QApplication
import os
import processing
import traceback
import re
from osgeo import gdal
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
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    temp_folder = os.path.join(plugin_dir, "temp")
    os.makedirs(temp_folder, exist_ok=True)

    # === SETUP ===
    project = QgsProject.instance()
    layout = project.layoutManager().layoutByName(layout_name)

    if layout is None:
        raise Exception("Layout not found. Check the layout name.")

    atlas = layout.atlas()
    exporter = QgsLayoutExporter(layout)
    map_item = layout.referenceMap()

    # Ensure output folders exist
    os.makedirs(img_output_folder, exist_ok=True)
    os.makedirs(elv_output_folder, exist_ok=True)

    grid_layer = atlas.coverageLayer()
    if grid_layer is None or not grid_layer.isValid():
        raise Exception("Coverage grid layer (atlas coverage) not found or invalid.")

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
            with open(log_path, "a") as log:
                log.write(f"{success}\n")

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

        # --- Reproject extent from layout CRS to DEM CRS ---

        grid_layer.removeSelection()
        grid_layer.select(fid)

        # Read the saved visual GeoTIFF to get exact extent and pixel size
        ds_visual = gdal.Open(visual_path)

        try:
            width = ds_visual.RasterXSize
            height = ds_visual.RasterYSize
            gt = ds_visual.GetGeoTransform()
            xmin = gt[0]
            px = gt[1]
            rot_x = gt[2]
            ymax = gt[3]
            rot_y = gt[4]
            py = gt[5]  # typically negative
            xmax = xmin + px * width
            ymin = ymax + py * height

            mask_path = os.path.join(temp_folder, f"map_{fid}_mask.tif")

            with open(log_path, "a") as log:
                log.write(f"\nMask Path: {mask_path}\nVisual Width: {width}\nVisual Height: {height}\nVisual Geo Transform: {gt}\nVisual xmin: {xmin}\nVisual xmax: {xmax}\nVisual ymax: {ymax}\nVisual ymin: {ymin}\nVisuals rot_x: {rot_x}\nVisuals rot_y: {rot_y}\nVisuals px: {px}\nVisuals py: {py}\n")

            # Build a raster mask with identical extent + pixel dimensions to the visual
            processing.run("gdal:rasterize", {
                'INPUT': grid_layer,
                'FIELD': None,
                'BURN': 1,
                'USE_Z': False,
                'UNITS': 0,
                'WIDTH': width,
                'HEIGHT': height,
                'EXTENT': f"{xmin},{xmax},{ymax},{ymin}",
                'NODATA': 0,
                'DATA_TYPE': 0,
                'INVERT': False,
                'OUTPUT': mask_path
            })

        except Exception as e:
            with open(log_path, "a") as log:
                log.write(f"\nRasterizing failed: {e}\n")

        # --- Log extent and paths ---
        with open(log_path, "a") as log:
            log.write(f"\nTile {fid} Visual: {visual_path}\n")
            log.write(f"\nOriginal Extent: {extent.toString()}\n")

        atlas.next()

    atlas.endRender()

    for name in sorted(os.listdir(temp_folder)):
        if not name.endswith("_mask.tif"):
            with open(log_path, "a") as log:
                log.write(f"\nNo file with {name} found in folder: {temp_folder}\n")
            continue

        m = re.search(r"map_(\d+)\_mask.tif", name)
        if not m:
            with open(log_path, "a") as log:
                log.write(f"\nSkipping non-mask file: {name}\n")
            continue

        fid = int(m.group(1))
        mask_path = os.path.join(temp_folder, name)

        ds_mask = gdal.Open(mask_path)
        if ds_mask is None:
            with open(log_path, "a") as log:
                log.write(f"\nMask unreadable: {mask_path}\n")
            continue

        width = ds_mask.RasterXSize
        height = ds_mask.RasterYSize
        gt = ds_mask.GetGeoTransform()
        xmin, px, _, ymax, _, py = gt
        xmax = xmin + px * width
        ymin = ymax + py * height

        elv_resampled = os.path.join(temp_folder, f"dem_resampled_{fid}.tif")
        elv_path = os.path.join(elv_output_folder, f"map_{fid}_elevation.tif")

        with open(log_path, "a") as log:
            log.write(f"\nElevation Path: {elv_path}\nElevation Resampled: {elv_resampled}\n")
        try:
            processing.run("gdal:warpreproject", {
                'INPUT': dem_layer,
                'SOURCE_CRS': dem_layer.crs(),
                'TARGET_CRS': map_item.crs(),
                'RESAMPLING': 0,
                'NODATA': -9999,
                'TARGET_RESOLUTION': abs(px),
                'TARGET_EXTENT': f"{xmin},{xmax},{ymax},{ymin}",
                'DATA_TYPE': 0,
                'OPTIONS': '',
                'OUTPUT': elv_resampled
            })
        except Exception as e:
            with open(log_path, "a") as log:
                log.write(f"\n{e}\n")

        try:
            # Apply mask
            processing.run("gdal:rastercalculator", {
                'INPUT_A': elv_resampled, 'BAND_A': 1,
                'INPUT_B': mask_path, 'BAND_B': 1,
                'FORMULA': "A*(B>=1) + (-9999)*(B<1)",
                'NO_DATA': -9999,
                'DATA_TYPE': 0,
                'OPTIONS': '',
                'EXTRA': '',
                'OUTPUT': elv_path
            })

        except Exception as e:
            with open(log_path, "a") as log:
                log.write(f"\nElevation Data Failed: {e}\n")
        print(f"[EXPORT] DEM tile written: {elv_path}")

    return