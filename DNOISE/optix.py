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
from mathutils import Vector
from . import fmutils

#
# Denoise Functions
#


def denoise(directory, source_name):
    """Runs full denoise or beauty denoise depending on available information"""
    if bpy.context.scene.EnableExtraPasses:
        normal_name = getnormal(directory)
        albedo_name = getalbedo(directory)
        fulldenoise(directory, source_name,  normal_name, albedo_name, gethdr(), getblend())
    else:
        beautydenoise(directory, source_name, gethdr(),getblend())


def beautydenoise(directory, source_name, hdr, blend):
    """Runs OptiX standalone denoiser with information for a beauty pass"""
    os.chdir(directory)
    os.system('.\OptiXDenoiser\Denoiser.exe -i "{0}" -o "{0}" -hdr {1} -b {2}'.format(source_name, hdr, blend))


def fulldenoise(directory, source_name,  normal_name, albedo_name, hdr, blend):
    """Runs OptiX standalone denoiser with information for a full denoising pass"""
    os.chdir(directory)
    convertnormals(directory, normal_name)
    os.system('.\OptiXDenoiser\Denoiser.exe  -i "{0}" -o "{0}" -n "{1}" -a "{2}" -hdr {3} -b {4}'.format(source_name, normal_name, albedo_name, hdr, blend))

#
# Node Functions
#


def addnodes(output_dir):
    """Adds the D-NOISE extra pass node set to the compositor node tree"""
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree

    # create new render layer node
    render_layer = tree.nodes.new(type='CompositorNodeRLayers')
    render_layer.layer = 'View Layer'
    render_layer.label = '[D-NOISE] Render Layers'
    render_layer.location = 0, 0

    # create first mix RGB node
    mix_emit_diffcol = tree.nodes.new('CompositorNodeMixRGB')
    mix_emit_diffcol.blend_type = 'ADD'
    mix_emit_diffcol.label = '[D-NOISE] Add'
    mix_emit_diffcol.location = 180, -120
    mix_emit_diffcol.hide = True

    # create first mix RGB node
    mix_last_subcol = tree.nodes.new('CompositorNodeMixRGB')
    mix_last_subcol.blend_type = 'ADD'
    mix_last_subcol.label = '[D-NOISE] Add'
    mix_last_subcol.location = 300, -120
    mix_last_subcol.hide = True

    # create file output node
    file_output = tree.nodes.new('CompositorNodeOutputFile')
    file_output.base_path = output_dir
    file_output.file_slots.clear()
    file_output.file_slots.new('Normal')
    file_output.file_slots.new('Albedo')
    file_output.show_options = False
    file_output.format.file_format = 'OPEN_EXR'
    file_output.format.color_depth = '32'
    file_output.label = '[D-NOISE] File Output'
    file_output.location = 420, -100
    file_output.hide = True

    # link nodes
    links = tree.links
    links.new(render_layer.outputs['Normal'], file_output.inputs['Normal'])
    links.new(render_layer.outputs['Emit'], mix_emit_diffcol.inputs[1])
    links.new(render_layer.outputs['DiffCol'], mix_emit_diffcol.inputs[2])
    links.new(mix_emit_diffcol.outputs['Image'], mix_last_subcol.inputs[1])
    links.new(render_layer.outputs['SubsurfaceCol'], mix_last_subcol.inputs[2])
    links.new(mix_last_subcol.outputs['Image'], file_output.inputs['Albedo'])


def cleannodes():
    """Returns true if the D-NOISE extra pass nodes already exist in the compositor"""
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    for node in bpy.context.scene.node_tree.nodes:
        if "D-NOISE" in node.label:
            tree.nodes.remove(node)


#
# Util Functions
#


def getnormal(directory):
    """Returns the file name of the last file with the string 'Normal' in a given directory"""
    os.chdir(directory)
    files = os.listdir(directory)
    normal_filename = None

    for file in files:
        if "Normal" in file:
            normal_filename = file

    return normal_filename


def getalbedo(directory):
    """Returns the file name of the last file with the string 'Albedo' in a given directory"""
    os.chdir(directory)
    files = os.listdir(directory)
    albedo_filename = None

    for file in files:
        if "Albedo" in file:
            albedo_filename = file

    return albedo_filename


def gethdr():
    """Returns whether or not HDR training data is enabled"""
    return 1 if bpy.context.scene.EnableHDRData else 0


def getblend():
    """Returns the float presented by the D-NOISE blend property"""
    return bpy.context.scene.DNOISEBlend

#
# NORMAL FUNCTIONS
#


def convertnormals(directory, filename):
    """Carries out the process of converting a world space normal image to a screen space normal image"""
    fmutils.load(directory, filename, 'Normal')
    print("[D-NOISE] Converting normals...")
    bpy.data.images['Normal'].pixels = toscreenspace(bpy.data.images['Normal'])
    bpy.data.images['Normal'].save()
    bpy.data.images.remove(bpy.data.images['Normal'])
    print("[D-NOISE] Normals successfully converted.")


def toscreenspace(image):
    """Converts the pixel data of a world space normal image to screen space normal pixels"""
    pixels = list(image.pixels)
    camera = bpy.context.scene.camera
    camera_rotation = camera.rotation_euler.to_quaternion()
    camera_rotation.invert()

    for i in range(0, len(pixels), 4):
        normal = Vector((pixels[i + 0], pixels[i + 1], pixels[i + 2]))
        screen_space_normal = camera_rotation @ normal
        pixels[i + 0] = screen_space_normal[0]
        pixels[i + 1] = screen_space_normal[1]
        pixels[i + 2] = screen_space_normal[2]

    return pixels