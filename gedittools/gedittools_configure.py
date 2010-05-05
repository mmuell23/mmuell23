import gtk, gtk.glade, os
from ConfigParser import ConfigParser

class GeditToolsConfiguration():
	def create_configuration_window(self):
		self._snapopen_glade = gtk.glade.XML( os.path.dirname( __file__ ) + "/gedittools.glade" )
		self._snapopen_window = self._snapopen_glade.get_widget( "GeditToolsWindow" )
		self._snapopen_window.set_title("Configure gedittools")

		#read properties
		properties = os.path.dirname( __file__ ) + "/gedittools.properties"
		self.cfg = ConfigParser()
		self.cfg.read(properties)

		container = self._snapopen_glade.get_widget("buttonbox")

		#display properties
		self.options = []
		for option in self.cfg.options("HighlightingOptions"):
			check_button = gtk.CheckButton(option, self.cfg.get("HighlightingOptions", option))
			if self.cfg.get("HighlightingOptions", option) == "true":
				check_button.set_active(True)
			self.options.append(check_button)
			container.pack_start(check_button, True, True, 0)

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
		self._snapopen_window.hide()		
