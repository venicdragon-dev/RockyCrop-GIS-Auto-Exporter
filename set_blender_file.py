import shutil
import subprocess
import os
import platform

plugin_dir = os.path.dirname(__file__)

def open_folder(path):
    if platform.system() == "Windows":
        subprocess.run(["explorer", os.path.normpath(path)])
    elif platform.system() == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])

def sanitize_path(path):
    return os.path.normpath(path).replace("\\", "/")

def copy_blender_script(src_path, dest_path):
    shutil.copyfile(src_path, dest_path)
    print(f"Copied Blender script to: {dest_path}")

def patch_blender_script(file_path, new_visual_path, new_elevation_path, crs):
    visual_path = sanitize_path(new_visual_path)
    elevation_path = sanitize_path(new_elevation_path)

    with open(file_path, "r") as f:
        lines = f.readlines()

    with open(file_path, "w") as f:
        for line in lines:
            if line.strip().startswith("mapfolder ="):
                f.write(f"mapfolder = r'{visual_path}'\n")
            elif line.strip().startswith("elvfolder ="):
                f.write(f"elvfolder = r'{elevation_path}'\n")
            elif line.strip().startswith("crs ="):
                f.write(f"crs = r'{crs}'\n")
            else:
                f.write(line)
    print("Blender script patched successfully.")

def prepare_blender_script(plugin_dir, visual_path, elevation_path, grid_crs):
    src = sanitize_path(os.path.join(plugin_dir, "blender_import_template.py"))
    dest = sanitize_path(os.path.join(plugin_dir, "blender_import.py"))
    copy_blender_script(src, dest)
    crs = grid_crs
    print(f"CRS passed to patch_blender_script: '{grid_crs}'")
    patch_blender_script(dest, visual_path, elevation_path, crs)
    open_folder(os.path.dirname(dest))