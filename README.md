# RockyCrop GIS Auto Exporter

RockyCrop is a QGIS plugin that automates grid creation, print layout setup, and terrain export for seamless integration with Blender or other 3D tools. It includes a Blender Python script for easy import of exported `.tif` files.

---

## Requirements

Before using RockyCrop, install these plugins via QGIS Plugin Manager:

- **QuickMapServices** – for basemap imagery
- **SRTMDownloader** – for elevation data

---

## What RockyCrop Does

1. **Grid Generation**  
   Creates a red-line grid overlay based on your specified spacing and CRS.

2. **Print Layout Creation**  
   Automatically builds a print layout with your chosen page size. Larger page sizes yield higher resolution exports but require more disk space.

3. **Export Automation**  
   Exports visual and elevation `.tif` files into separate folders. Also generates a Blender import script for easy terrain reconstruction.

4. **Blender Integration**  
   Use the included `blender_import.py` to load your exported tiles directly into Blender with correct elevation.

---

## How to Use

1. Install QuickMapServices and SRTMDownloader.
2. Load a map (Google Maps recommended).
3. Zoom to your target area.
4. Use SRTMDownloader to download elevation data.
5. Rename the SRTM layer for easy reference.
6. Launch RockyCrop from the toolbar.
7. Fill in the UI fields:
   - Grid spacing and CRS
   - Manual extent or use current map view
   - Layout name and page size
   - SRTM layer name
   - Visual and elevation folder paths
8. Click **Start Process** and watch your folders fill with exports!

---

## UI Breakdown

- **Grid Settings**: Define spacing and CRS.
- **Extent Selection**: Use manual coordinates, current map extent, or draw on map.
- **Print Layout Settings**: Set layout name and page dimensions.
- **Export Settings**: Provide SRTM layer name and folder paths.
- **Start Process**: Begin export and generate Blender script.

---

## Blender Import Script

After export, the plugin folder will open automatically. Copy `blender_import.py` to a convenient location and run it in Blender to import your terrain tiles.

---

## Notes

- Ensure visual and elevation folders are **not the same**.
- Large exports can consume significant disk space — plan accordingly.
- Works great for game development, architectural visualization, and terrain modeling.

---

## Support

For questions, feedback, or bug reports, visit [RockyCrop: GIS Auto Exporter](https://github.com/venicdragon-dev/RockyCrop-GIS-Auto-Exporter)].

---

## License

RockyCrop is licensed under [GPL v3](https://www.gnu.org/licenses/gpl-3.0.en.html).
