#!/usr/bin/env python3
import sys
import gi
# GIMP core elements use 3.0 API bindings
gi.require_version('Gimp', '3.0')

# GEGL components use 0.4 API bindings
gi.require_version('Gegl', '0.4')

from gi.repository import Gimp, Gegl, Gio, GLib

def create_make_background_transparent_image(procedure, run_mode, image, n_drawables, drawables, config, data):
    if n_drawables == 0:
        return procedure.new_return_values(Gimp.PdbStatusType.EXECUTION_ERROR, GLib.Error.new_literal(Gio.io_error_quark(), Gio.IOErrorEnum.INVALID_ARGUMENT, "No drawables provided."))

    drawable = drawables[0]

    # 1. Get the GEGL buffer of the drawable
    buffer = drawable.get_buffer()
    
    # 2. Define the 1x1 target region
    rect = Gegl.Rectangle.new(0, 0, 1, 1)

    # 3. Force GEGL to output standard 8-bit RGBA bytes using Babl formatting
    # "RGBA u8" tells Babl exactly how to fill the byte array
    pixel_data = buffer.get(rect, 1.0, "RGBA u8", Gegl.AbyssPolicy.CLAMP)

    # 4. Safe guard check to ensure data was actually read from the canvas
    if pixel_data and len(pixel_data) >= 3:
        r = pixel_data[0] / 255.0
        g = pixel_data[1] / 255.0
        b = pixel_data[2] / 255.0
    else:
        r = g = b = 1.0  # Default fallback if read failed

    # 5. Correctly initialize the Gegl.Color object using a valid base string string
    color = Gegl.Color.new("black")

    # 6. Explicitly overwrite the RGBA components with your extracted floats
    color.set_rgba(r, g, b, 1.0)

    
    # 7. Perform the Select by Color operation using the modern Gimp Image API
    # Gimp.ChannelOps.REPLACE (value 2) replaces any active selection
    image.select_color(Gimp.ChannelOps.REPLACE, drawable, color)

    Gimp.Selection.grow(image, 1)  # Grow selection by 1 pixel to ensure edges are included

    # 2. Check if an active selection exists on the canvas.
    # If no selection is active, GIMP defaults to applying filters to the whole layer.
    is_empty = Gimp.Selection.is_empty(image)
    if is_empty:
        print("Warning: No active selection found. Filter will apply to the entire layer.")

    # 3. Color to Alpha requires an explicit transparency map.
    # Add an alpha channel if the source layer does not have one (e.g., flat JPEGs)
    if not drawable.has_alpha():
        drawable.add_alpha()

    # 4. Instantiate the modern non-destructive GIMP 3 filter via GEGL
    # Operation ID: "gegl:color-to-alpha"
    c2alpha_filter = Gimp.DrawableFilter.new(drawable, "gegl:color-to-alpha", "Selection Color to Alpha")
    
    # 5. Extract the internal configuration map to inject the color data
    filter_config = c2alpha_filter.get_config()
    
    # 6. Set properties. "color" expects a valid Gegl.Color object
    filter_config.set_property("color", color)
    filter_config.set_property("transparency-threshold", 0.0) # Matches default tool behavior
    filter_config.set_property("opacity-threshold", 1.0)       # Matches default tool behavior
    
    # 7. Execute, commit, and merge the filter data onto the drawable canvas matrix.
    # GIMP automatically restricts this operation to the boundaries of the selection.
    drawable.merge_filter(c2alpha_filter)

    # 8. Clear the selection after applying the filter to avoid leaving an active selection on the canvas
    Gimp.Selection.none(image)
    
    # 9. Flush displays to make the selection visible on canvas
    Gimp.displays_flush()
    
    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

class MakeBackTransPlugin(Gimp.PlugIn):
    # Override this method to tell GIMP 3.2 to stop looking for translation files
    def do_set_i18n(self, procname):
        return (False, None, None)
    
    def do_query_procedures(self):
        return ["python-fu-make-background-transparent"]

    def do_create_procedure(self, name):
        proc = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run, None)
        proc.set_menu_label("Make Background Transparent")
        proc.add_menu_path("<Image>/Filters/Development")
        return proc

    def run(self, procedure, run_mode, image, drawables, config, data):
        create_make_background_transparent_image(procedure, run_mode, image, len(drawables), drawables, config, data)
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)

Gimp.main(MakeBackTransPlugin.__gtype__, sys.argv)
