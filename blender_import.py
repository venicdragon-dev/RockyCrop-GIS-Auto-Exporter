import bpy
import bpy.utils
import bgl
from bpy import context
from mathutils import *
import time
import os
import re
import bmesh

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator

# Config
mapfolder = r'D:/Work/QGIS Auto Exporter/Map Images/Map Visuals'
elvfolder = r'D:/Work/QGIS Auto Exporter/Map Images/Map Elevations'
crs = r'EPSG:3857'

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Process matching pairs
for mapfile in os.listdir(mapfolder):
    if mapfile.endswith('_visual.tif'):
        # Get corresponding elevation file
        fid = mapfile.split('_')[1]
        elvfile = f"map_{fid}_elevation.tif"
        elvpath = os.path.join(elvfolder, elvfile)
       
        if not os.path.exists(elvpath):
            print(f"Missing elevation file for {mapfile}")
            continue
           
        # === 1. IMPORT ELEVATION (AS MESH) ===
        bpy.ops.importgis.georaster(
            filepath=elvpath,
            rastCRS=crs,
            importMode="DEM"
        )
        terrain = bpy.context.object
        terrain.name = f"Terrain_{fid}"
        
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        # Apply each modifier in reverse order to avoid indexing issues
        for mod in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
                print(f"Applied '{mod.name}' on '{obj.name}'")
            except Exception as e:
                print(f"Failed to apply '{mod.name}' on '{obj.name}': {e}")

            # Deselect object after processing
            obj.select_set(False)
               
        # === 2. APPLY VISUAL AS TEXTURE ===
        mappath = os.path.join(mapfolder, mapfile)
       
        # Create material
        mat = bpy.data.materials.new(name=f"TerrainMat_{fid}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
       
        # Add image texture
        tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_node.image = bpy.data.images.load(mappath)
       
        # Connect to material
        mat.node_tree.links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
        terrain.data.materials.append(mat)
       
        # === 3. FIX VISIBILITY & SCALE ===
        terrain.scale = (1, 1, 1)
        bpy.ops.object.transform_apply(scale=True)
       
        # Ensure object is visible
        terrain.hide_set(False)
        terrain.hide_viewport = False
        terrain.hide_render = False

# Fix viewport clipping
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.clip_start = 0.1
                space.clip_end = 100000
                
print("=== IMPORT COMPLETE ===")