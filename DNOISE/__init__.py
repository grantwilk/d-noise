bl_info = {
    "name": "D-NOISE: AI-Accelerated Denoiser",
    "author": "Grant Wilk",
    "blender": (2, 7),
    "version": (1, 0, 0),
    "location": "UV/Image Editor",
    "category": "Render",
    "description": """An AI-accelerated denoiser for Cycles and Blender."""
}

if "bpy" in locals():
    import importlib
    if 'optix' in locals():
        importlib.reload(locals()['optix'])
    if 'fm_utils' in locals():
        importlib.reload(locals()['fm_utils'])

import bpy
import os
import shutil
import bpy.utils.previews
from . import optix, fmutils

# directory of the script files
SCRIPT_DIR = os.path.dirname(__file__)

# compositor nodes added by D-NOISE
DNOISE_NODES = []

# custom icons dictionary
CUSTOM_ICONS = None

# source image of the denoised image
DENOISE_SOURCE = None

# file extensions for the various Cycles' image output formats
FORMAT_EXTENSIONS = {'BMP': 'bmp',
                     'PNG': 'png',
                     'JPEG': 'jpg',
                     'TARGA': 'tga',
                     'TARGA_RAW': 'tga',
                     'OPEN_EXR_MULTILAYER': 'exr',
                     'OPEN_EXR': 'exr',
                     'HDR': 'hdr',
                     'TIFF': 'tif'}

#
# Denoiser Functions
#


def runpostdenoiser():
    """Run the OptiX beauty denoiser from the UV/Image editor"""
    global DENOISE_SOURCE, SCRIPT_DIR, FORMAT_EXTENSIONS
    DENOISE_SOURCE = bpy.context.space_data.image

    if DENOISE_SOURCE is not None:
        file_format = DENOISE_SOURCE.file_format
        file_format = fmutils.checkformat(file_format, FORMAT_EXTENSIONS)
        source_name = 'source.{0}'.format(file_format)
        fmutils.save(SCRIPT_DIR, source_name, DENOISE_SOURCE)

    optix.beautydenoise(SCRIPT_DIR, optix.gethdr(), source_name)
    fmutils.load(SCRIPT_DIR, source_name, 'D-NOISE Export')
    fmutils.setactiveimage('D-NOISE Export', bpy.context.space_data)
    fmutils.setcolorspace('D-NOISE Export', file_format)
    fmutils.deepclean(SCRIPT_DIR, FORMAT_EXTENSIONS)


def runrenderdenoiser(placeholder=None):
    """Run the OptiX denoiser after a render completes"""
    global DENOISE_SOURCE, SCRIPT_DIR, FORMAT_EXTENSIONS
    DENOISE_SOURCE = bpy.data.images['Render Result']

    file_format = bpy.context.scene.render.image_settings.file_format
    file_format = fmutils.checkformat(file_format, FORMAT_EXTENSIONS)
    source_name = 'source.{0}'.format(file_format)

    fmutils.save(SCRIPT_DIR, source_name, DENOISE_SOURCE)
    optix.denoise(SCRIPT_DIR, source_name)
    fmutils.load(SCRIPT_DIR, source_name, 'D-NOISE Export')
    fmutils.setactiveimage('D-NOISE Export')
    fmutils.setcolorspace('D-NOISE Export', file_format)
    fmutils.deepclean(SCRIPT_DIR, FORMAT_EXTENSIONS)


def runanimdenoiser(placeholder=None):
    """Run the OptiX denoiser while rendering an animation"""
    global DENOISE_SOURCE, SCRIPT_DIR, FORMAT_EXTENSIONS
    DENOISE_SOURCE = bpy.data.images['Render Result']

    output_dir = fmutils.fixfilepath(bpy.context.scene.render.filepath)
    source_name = fmutils.getmostrecent(output_dir)
    shutil.copyfile(os.path.join(output_dir, source_name), os.path.join(SCRIPT_DIR, source_name))
    optix.denoise(SCRIPT_DIR, source_name)
    shutil.copyfile(os.path.join(SCRIPT_DIR, source_name), os.path.join(output_dir, source_name))
    fmutils.deepclean(SCRIPT_DIR, FORMAT_EXTENSIONS)


def swaptorender(placeholder=None):
    """Switches any image editors with the D-NOISE Export back to the Render Result before rendering"""
    for area in bpy.data.window_managers['WinMan'].windows[0].screen.areas:
        if area.type == 'IMAGE_EDITOR' and area.spaces[0].image.name == 'D-NOISE Export':
            area.spaces[0].image = bpy.data.images['Render Result']


def togglednoise(self=None, context=None):
    """Toggles the D-NOISE denosier for rendering single frames and animations"""
    if not bpy.context.scene.EnableDNOISE:
        bpy.app.handlers.render_complete.remove(runrenderdenoiser)
        bpy.app.handlers.render_write.remove(runanimdenoiser)
    else:
        bpy.app.handlers.render_complete.append(runrenderdenoiser)
        bpy.app.handlers.render_write.append(runanimdenoiser)


def togglenodes(self=None, context=None):
    """Toggles the D-NOISE nodes in the compositor"""
    global DNOISE_NODES, SCRIPT_DIR
    active_layer = bpy.context.scene.render.layers.active.name

    if bpy.context.scene.EnableExtraPasses:
        fmutils.enablepasses(active_layer)
        optix.cleannodes()
        DNOISE_NODES = optix.addnodes(SCRIPT_DIR, DNOISE_NODES)
    else:
        fmutils.disablepasses(active_layer)
        DNOISE_NODES = optix.removenodes(DNOISE_NODES)
        optix.cleannodes()


#
# Operators
#


class QuickDenoise(bpy.types.Operator):
    bl_idname = "dnoise.quick_denoise"
    bl_label = "D-NOISE"

    def execute(self, context):
        runpostdenoiser()
        return {'FINISHED'}


class ToggleDnoiseExport(bpy.types.Operator):
    bl_idname = "dnoise.toggle_export"
    bl_label = "Toggle D-NOISE Export in 3D Viewport"

    global DENOISE_SOURCE

    def execute(self, context):
        current_image = bpy.context.space_data.image

        if DENOISE_SOURCE is not None:
            if (current_image == bpy.data.images['D-NOISE Export']) and (DENOISE_SOURCE.name in bpy.data.images):
                bpy.context.space_data.image = DENOISE_SOURCE

            elif (current_image != bpy.data.images['D-NOISE Export']) and ('D-NOISE Export' in bpy.data.images):
                bpy.context.space_data.image = bpy.data.images['D-NOISE Export']

        return {'FINISHED'}


class DNOISEPanel(bpy.types.Panel):
    bl_label = "D-NOISE: AI Denoiser"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render_layer"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        layout.prop(bpy.context.scene, 'EnableDNOISE', text="")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(bpy.context.scene, "EnableHDRData", text="Use HDR Training")
        row.prop(bpy.context.scene, "EnableExtraPasses", text="Use Extra Passes")


#
# UI Implementations
#


def appendto_image_ht_header(self, context):
    """UI code to append to the IMAGE_HT_HEADER space"""
    global CUSTOM_ICONS
    layout = self.layout
    layout.separator()
    row = layout.row(align=True)
    row.operator(
        "dnoise.quick_denoise",
        text="Quick D-NOISE",
        icon_value=CUSTOM_ICONS['dnoise_icon'].icon_id)
    if bpy.context.space_data.image.name == 'D-NOISE Export':
        row.operator("dnoise.toggle_export", text="", icon="RESTRICT_VIEW_OFF")
    else:
        row.operator("dnoise.toggle_export", text="", icon="RESTRICT_VIEW_ON")


#
# Registration / Unregistration
#


def register():
    # register classes
    bpy.utils.register_class(QuickDenoise)
    bpy.utils.register_class(ToggleDnoiseExport)
    bpy.utils.register_class(DNOISEPanel)

    # register properties
    bpy.types.Scene.EnableDNOISE = bpy.props.BoolProperty(update=togglednoise, description="Denoise the rendered image using D-NOISE.")
    bpy.types.Scene.EnableHDRData = bpy.props.BoolProperty(description="Enabling HDR training data will produce a more accurate denoise for renders with high dynamic range.")
    bpy.types.Scene.EnableExtraPasses = bpy.props.BoolProperty(update=togglenodes, description="Enabling extra passes will help maintain fine detail in texures, but may cause artifacts.")

    # register variables
    global CUSTOM_ICONS
    CUSTOM_ICONS = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icon")
    CUSTOM_ICONS.load("dnoise_icon", os.path.join(icons_dir, "dnoise_icon.png"), 'IMAGE')

    # register UI implementations
    bpy.types.IMAGE_HT_header.append(appendto_image_ht_header)

    # clean out any past files from the script directory
    global SCRIPT_DIR, FORMAT_EXTENSIONS
    fmutils.deepclean(SCRIPT_DIR, FORMAT_EXTENSIONS)


def unregister():
    # unregister classes
    bpy.utils.unregister_class(QuickDenoise)
    bpy.utils.unregister_class(ToggleDnoiseExport)
    bpy.utils.unregister_class(DNOISEPanel)

    # clean out any past files from the script directory
    global SCRIPT_DIR, FORMAT_EXTENSIONS
    fmutils.deepclean(SCRIPT_DIR, FORMAT_EXTENSIONS)

    # remove nodes
    if bpy.context.scene.EnableExtraPasses:
        togglenodes()

    # unregister properties
    del bpy.types.Scene.EnableDNOISE
    del bpy.types.Scene.EnableHDRData

    # unregister variables
    global CUSTOM_ICONS
    bpy.utils.previews.remove(CUSTOM_ICONS)

    # unregister UI integrations
    bpy.types.IMAGE_HT_header.remove(appendto_image_ht_header)

    # unregister render process integrations
    if runpostdenoiser in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(runpostdenoiser)

    if runrenderdenoiser in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(runrenderdenoiser)

    if runanimdenoiser in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(runanimdenoiser)

