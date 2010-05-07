import gtk, gtk.glade, os
from ConfigParser import ConfigParser

class GeditToolsConfiguration():
	def create_configuration_window(self):
		self._snapopen_glade = gtk.glade.XML( os.path.dirname( __file__ ) + "/gedittools.glade" )
		self._snapopen_window = self._snapopen_glade.get_widget( "GeditToolsWindow" )
		self._snapopen_window.set_title("Configure gedittools")
		
		#layout stuff
		container = self._snapopen_glade.get_widget("labelbox")
		label = gtk.Label("Select from available options:")
		container.pack_start(label, True, True, 0)
		
		#read properties
		properties = os.path.dirname( __file__ ) + "/gedittools.properties"
		self.cfg = ConfigParser()
		self.cfg.read(properties)

		container = self._snapopen_glade.get_widget("mainelements")

		#display properties
		self.options = []
		for option in self.cfg.options("HighlightingOptions"):
			option = option[0].swapcase() + option[1:]
			check_button = gtk.CheckButton(option, self.cfg.get("HighlightingOptions", option))
			if self.cfg.get("HighlightingOptions", option) == "true":
				check_button.set_active(True)
			self.options.append(check_button)
			container.pack_start(check_button, True, True, 0)


		#display buttons
		container = self._snapopen_glade.get_widget("buttonbox")

		cancel = gtk.Button("Cancel")
		cancel.connect("clicked", self.close_window)
		container.pack_start(cancel)
		
		button = gtk.Button("Save settings")
		button.connect("clicked", self.save_properties)
		container.pack_start(button)
		
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
