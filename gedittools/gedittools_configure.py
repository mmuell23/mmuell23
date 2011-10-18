import os
from gi.repository import GObject, Gedit, Gtk
from ConfigParser import ConfigParser

class GeditToolsConfiguration():
    def create_configuration_window(self):
    
        self.builder = Gtk.Builder()
        self.builder.add_from_file( os.path.dirname( __file__ ) + "/gedittools.ui" )
        self._snapopen_window = self.builder.get_object("GeditToolsWindow")    
        self._snapopen_window.set_title("Configure gedittools")
        
        #layout stuff
        container = self.builder.get_object("labelbox")
        label = Gtk.Label("Select from available options:")
        container.pack_start(label, True, True, 0)
        
        #read properties
        properties = os.path.dirname( __file__ ) + "/gedittools.properties"
        self.cfg = ConfigParser()
        self.cfg.read(properties)

        container = self.builder.get_object("mainelements")

        #display properties
        self.options = []
        for option in self.cfg.options("HighlightingOptions"):
            check_button = Gtk.CheckButton(option[0].swapcase() + option[1:])
            if self.cfg.get("HighlightingOptions", option) == "true":
                check_button.set_active(True)
            self.options.append(check_button)
            container.pack_start(check_button, True, True, 0)

        #display buttons
        container = self.builder.get_object("buttonbox")

        cancel = Gtk.Button("Cancel")
        cancel.connect("clicked", self.close_window)
        container.pack_start(cancel, True, True, 0)
        
        button = Gtk.Button("Save settings")
        button.connect("clicked", self.save_properties)
        container.pack_start(button, True, True, 0)
        
        self._snapopen_window.show_all()
        
    def save_properties(self, button):
        cfg_file = open(os.path.dirname( __file__ ) + "/gedittools.properties", "w")
        for option in self.options:
            is_set = "false"
            if option.get_active():
                is_set = "true"
            self.cfg.set("HighlightingOptions", option.get_label(), is_set)
        self.cfg.write(cfg_file)
        self.close_window(button)
                
    def close_window(self, button):
        self._snapopen_window.hide()
