#!/usr/bin/env python3
import sys
import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp, GObject, Gio

def create_hello_world_image():
    """Core image creation logic."""
    image = Gimp.Image.new(600, 400, Gimp.ImageBaseType.RGB)
    bg = Gimp.Layer.new(image, "BG", 600, 400, Gimp.ImageType.RGB_IMAGE, 100, Gimp.LayerMode.NORMAL)
    image.insert_layer(bg, None, 0)

    # Grab the active system font automatically
    active_font = Gimp.context_get_font()
    # Create the text layer safely
    text = Gimp.TextLayer.new(image, "Hello GIMP 3.2!", active_font, 40, Gimp.Unit.pixel())

    image.insert_layer(text, None, 0)
    Gimp.Display.new(image)

class HelloWorldPlugin(Gimp.PlugIn):
    def do_query_procedures(self):
        return ["python-fu-hello-world"]

    def do_create_procedure(self, name):
        proc = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run, None)
        proc.set_menu_label("Hello World 3.2")
        proc.add_menu_path("<Image>/Filters/Development")
        return proc

    def run(self, procedure, run_mode, image, drawables, config, data):
        create_hello_world_image()
        return procedure.new_return_values(Gimp.PdbStatusType.SUCCESS, None)

Gimp.main(HelloWorldPlugin.__gtype__, sys.argv)
