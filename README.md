# RockyCrop-GIS-Auto-Exporter
A plugin for QGIS that will automate creation of a grid and print layout to automatically export TIF files for later use in Blender or other programs. Blender code included for easier importing of the exported files.

Other plugins you will need (These were used for the exporting side):
QuickMapServices
SRTMDownloader

More indepth explanation of what this plugin does:

1: It will create a grid on the map for you as a red line square / rectangle for easier viewing in the export and in your map extent, using the measurements provided in the UI.

2: After creating the grid, a print layout will be created with a page size given by you in the UI. (Note: The page size will determine the resolution of the exports, the larger your page size, the higher resolution you will get. This will also increase the files size considerably if you go for a large page size. So make sure you have enough space for the exports as it can take up a lot of space. Eg, exporting a map for a game we are developing at a 1km by 1km page size, we would've needed over a petabyte of space for all the map tiles (Given, it was a HUGE area we were exporting).)

3: Once those two items have been created, the exporting will commence into the two folders provided by you and it will also provide you with a python file that you can use in Blender to import those TIF files automatically with out having to do anything coding yourself (Will get into how to work with that later)

4: After all that, you will have a visual folder full of what you normally see on the map you chose and an elevation folder full of elevation data for making the visual have the correct elevations in Blender.

What you will need to do from your side:

1: Make sure you have set up SRTM downloader and QuickMapServices.
2: Download a map from QuickMapServices (A Google map is prefered).
3: If your map is a full map of the world, zoom into the area you want to export.
4: Use SRTMDownloader to download the Elevation Data for that area.
5: Right click the SRTM layer and rename it, so you can copy paste the name.
6: Click the RockyCrop icon on your tool bar.
7: Set up everything in the UI (Paste the copied SRTM layer name into the SRTM input at the bottom).
8: Everything set to your preference? Awesome, now we start the process and watch the Visual folder and Elevation Folder fill with those exports.

Break down of the UI:

1: Grid Settings: This is where you'll set up your grid measurements and set the CRS you want to use.
2: Manual Extent Coordinates: You welcome to set your own extents if you know how to do those. You can also just use the current map extent (What you are currently viewing in the main view port) or you can draw on the map to select a section of the area you are viewing.
3: Print Layout Settings: This is where you'll give the needed name of the print layout and the "resolution" you want the exports to be.
4: Export Settings: Set your SRTM layer name. Make sure to have the visual and export files in seperate locations, which you will need to provide.
5: Start Process: Begin the journey of exporting your map for what ever project you are working on. Be it a video game. Art project. Architectural planning. They are yours to play with now.

When the process begins, the location of the plugin files will open for you so you can copy the blender_import.py file which you can open in Blender to import the exported files (Best to copy and paste or move the file into a location that is easier to access)

You should be all set!
