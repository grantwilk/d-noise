"""
Copyright (C) 2018 Grant Wilk

This file is part of D-NOISE: AI-Acclerated Denoiser.

D-NOISE: AI-Acclerated Denoiser is free software: you can redistribute
it and/or modify it under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

D-NOISE: AI-Acclerated Denoiser is distributed in the hope that it will
be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along
with D-NOISE: AI-Acclerated Denoiser.  If not, see <https://www.gnu.org/licenses/>.
"""


import bpy
import os
import zipfile
import shutil

#
# EXTERNAL FILE MANAGEMENT
#


def save(directory, filename, image):
    """Saves a Blender image file to an external directory"""
    if image.name == 'Render Result':
        original_format = bpy.context.scene.render.image_settings.file_format
        bpy.context.scene.render.image_settings.file_format = 'OPEN_EXR'
        bpy.context.scene.render.image_settings.color_depth = '32'
        image.save_render(filepath=os.path.join(directory, filename))
        bpy.context.scene.render.image_settings.file_format = original_format
    else:
        shutil.copyfile(image.filepath, os.path.join(directory, filename))


def load(directory, filename, imagekey):
    """Loads an external image into a Blender image file called 'D-NOISE Export'"""
    if 'D-NOISE Export' in bpy.data.images:
        bpy.data.images.remove(bpy.data.images['D-NOISE Export'])

    bpy.data.images.load(filepath=os.path.join(directory, filename))
    bpy.data.images[filename].name = imagekey
    bpy.data.images[imagekey].pack()

    fileformat = os.path.splitext(filename)[1]
    setcolorspace(imagekey, fileformat)


def clean(directory, fileformat):
    """Deletes all files of a given format from a directory"""
    os.chdir(directory)
    for file in os.listdir(directory):
        if fileformat in file:
            os.remove(file)


def deepclean(directory, format_dict):
    """Deletes all files of a given set of formats from a directory"""
    for key in format_dict:
        clean(directory, format_dict[key])


def getmostrecent(directory):
    """Returns the file name of the most recently edited file"""
    os.chdir(directory)
    render_files = sorted(os.listdir(os.getcwd()), key=os.path.getmtime)
    return render_files[-1]


def unzip(directory, filename):
    file_dir = os.path.join(directory, filename)
    with zipfile.ZipFile(file_dir, 'r') as zip_ref:
        zip_ref.extractall("")

    os.chdir(directory)
    os.remove(filename)


def removeoptixbin(directory):
    os.chdir(directory)
    if os.path.exists("DNOISE_OptiXBinaries.zip"):
        os.remove("DNOISE_OptiXBinaries.zip")
    if os.path.isdir("OptiXDenoiser"):
        shutil.rmtree(os.path.join(directory, "OptiXDenoiser"))


#
# FILE PATH FUNCTIONS
#


def fixfilepath(path):
    """Unifies expandlocal and truncate to convert incompatible file directories to proper ones"""
    path = exapandlocal(path)
    path = truncate(path)
    return path


def truncate(path):
    """Returns a file path with all data removed after the last slash -- e.g. C:\\myfile\\word becomes C:\\myfile\\"""
    if not path[-1] == "\\":
        truncated = path[:path.rfind("\\")]
    else:
        truncated = path
    return truncated


def exapandlocal(path):
    """Replaces the // at the beginning of a local file path with the full file path"""
    if path[:2] == "//":
        expanded = bpy.path.abspath(path)
    else:
        expanded = path
    return expanded


def filetruncate(filename):
    """Returns a filename with all data removed after the last period -- e.g. myimage.png => myimage"""
    if not filename[-1] == ".":
        truncated = filename[:filename.rfind(".")]
    else:
        truncated = filename
    return truncated


#
# INTERNAL IMAGE MANAGEMENT
#

def setactiveimage(imagekey, space=None):
    """Decides whether to run setactiveimage_context or setactiveimage_nocontext based on space data"""
    if space is not None:
        setactiveimage_context(imagekey, space)
    else:
        setactiveimage_nocontext(imagekey)


def setactiveimage_context(imagekey, space):
    """Sets the given image as the active image of the specified image editor space"""
    if imageexists(imagekey):
        space.image = bpy.data.images[imagekey]


def setactiveimage_nocontext(imagekey):
    """Sets the given image as the active image of any image editor displaying the render result"""
    for area in bpy.data.window_managers['WinMan'].windows[0].screen.areas:
        if area.type == 'IMAGE_EDITOR' and (area.spaces[0].image is None or area.spaces[0].image.name == 'Render Result'):
            area.spaces[0].image = bpy.data.images[imagekey]


def setcolorspace(imagekey, fileformat):
    """Sets the colorspace settings of the specified Blender image"""
    if imageexists(imagekey):
        if fileformat == 'OPEN_EXR' or fileformat == 'OPEN_EXR_MULTILAYER' or fileformat == 'HDR':
            bpy.data.images[imagekey].use_view_as_render = True
            # try-except to prevent custom OCIOs from throwing errors
            try:
                bpy.data.images[imagekey].colorspace_settings.name = 'Linear'
            except:
                pass
        else:
            try:
                bpy.data.images[imagekey].colorspace_settings.name = 'sRGB'
            except:
                pass


def imageexists(imagekey):
    """Returns true if the given image key exists in Blender"""
    if imagekey not in bpy.data.images:
        print(">> D-NOISE ERROR: image {} does not exist in bpy.data.images".format(imagekey))

    return imagekey in bpy.data.images


def getextension(file_format, extension_dict):
    """Checks to make sure the given file format is in the specified extension dictionary, if not, default to PNG"""
    if file_format in extension_dict:
        file_extension = extension_dict[file_format]
    else:
        print(">> D-NOISE ERROR: File output format {0} is not supported by D-NOISE. Defaulting to 'PNG'.".format(file_format))
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        file_extension = extension_dict['PNG']

    return file_extension

#
# RENDER LAYER FUNCTIONS
#


def enablepasses(renderlayer):
    """Enables the passes required by D-NOISE for extra pass denoising"""
    bpy.context.scene.render.layers[renderlayer].use_pass_diffuse_color = True
    bpy.context.scene.render.layers[renderlayer].use_pass_subsurface_color = True
    bpy.context.scene.render.layers[renderlayer].use_pass_emit = True
    bpy.context.scene.render.layers[renderlayer].use_pass_normal = True


def disablepasses(renderlayer):
    """Disables the passes required by D-NOISE for extra pass denoising"""
    bpy.context.scene.render.layers[renderlayer].use_pass_diffuse_color = False
    bpy.context.scene.render.layers[renderlayer].use_pass_subsurface_color = False
    bpy.context.scene.render.layers[renderlayer].use_pass_emit = False
    bpy.context.scene.render.layers[renderlayer].use_pass_normal = False

#
# Force Update Function
#

def forceUIUpdate(area_type):
    for window in bpy.data.window_managers['WinMan'].windows:
        for area in window.screen.areas:
            if area.type == area_type:
                area.tag_redraw()