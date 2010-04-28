from gettext import gettext as _

import gtk, gtk.glade
import gedit
import re
import os

ui_str = """<ui>
<menubar name="MenuBar">
<menu name="SearchMenu" action="Search">
<placeholder name="SearchOps_2">
<menuitem name="MeldLauncherAction" action="MeldLauncherAction"/>
</placeholder>
</menu>
</menubar>
<toolbar name="ToolBar">
<placeholder name="Tool_Opt4"><toolitem name="MeldLauncherAction" action="MeldLauncherAction"/></placeholder>
</toolbar>
</ui>
"""


#plugin
class MeldLauncherWindowHelper:
	def __init__(self, plugin, window):
		self._window = window
		self._plugin = plugin
		

		self._insert_menu()
	def deactivate(self):
		self._remove_menu()
	
		self._window = None

		self._plugin = None
		self._action_group = None
	def _insert_menu(self):
		manager = self._window.get_ui_manager()

		self._action_group = gtk.ActionGroup("MeldLauncherGroup")
		self._action_group.add_actions([("MeldLauncherAction", gtk.STOCK_COPY, _("Compare current file"), '<Control><Shift>c', _("Compare current file"), self.on_compare_file)])
		manager.insert_action_group(self._action_group, -1)
		
		self._ui_id = manager.add_ui_from_string(ui_str)

	def _remove_menu(self):
		manager = self._window.get_ui_manager()
		manager.remove_ui(self._ui_id)
		manager.remove_action_group(self._action_group)
		manager.ensure_update()

	def update_ui(self):
		self._action_group.set_sensitive(self._window.get_active_document() != None)

	def on_compare_file(self, action):

		current_doc = self._window.get_active_document()
		app = gedit.app_get_default() 

		#kein oder nur 1 Dokument? return
		if current_doc == None or len(app.get_documents()) == 1:
			return
		
		#nur 2 dokumente? fang gleich an und spar dir den fensterkram...
		if (len(app.get_documents()) == 2):
			self._path_1 = app.get_documents()[0].get_uri_for_display()
			self._path_2 = app.get_documents()[1].get_short_name_for_display()
			self.start_comparing()
			return

		self._path_1 = current_doc.get_uri_for_display()

		#fenster zur auswahl bauen
		self._snapopen_glade = gtk.glade.XML( os.path.dirname( __file__ ) + "/meldlauncher.glade" )
		self._snapopen_window = self._snapopen_glade.get_widget( "MeldLauncherWindow" )	

		#fill in current filename
		labelbox = self._snapopen_glade.get_widget("labelbox")
		label = gtk.Label()
		label.set_use_markup(True)
		label.set_markup("Compare <b>" + current_doc.get_short_name_for_display() + "</b> to:")
		label.set_justify(gtk.JUSTIFY_LEFT)
		label.set_padding(15,15)
		
		labelbox.pack_start(label, True, True, 0)

		#build filenames in listbox
		self._snapopen_window.set_title("Select file to compare with")
		self._snapopen_window.set_transient_for(self._window)

		#iterate all opened files
		filelist_group = self._snapopen_glade.get_widget("buttonbox")
		for doc in gedit.app_get_default().get_documents():
			if current_doc.get_short_name_for_display() != doc.get_short_name_for_display():
				button = gtk.Button(doc.get_short_name_for_display())
				button.connect("clicked", self.button_callback)
				
				filelist_group.pack_start(button, True, True, 0)

				if doc != gedit.app_get_default().get_documents()[-1]:
					filelist_group.pack_start(gtk.HSeparator(), True, True, 0)

		self._snapopen_window.show_all()
		
		
	def start_comparing(self):
		path = None
		for doc in gedit.app_get_default().get_documents():
			if doc.get_short_name_for_display() == self._path_2:
				path = doc.get_uri_for_display()
				
		os.system("/usr/bin/meld " + self._path_1 + " " + path)


	def button_callback(self, button):
		self._path_2 = button.get_label()
		self.start_comparing()

	def message_dialog(self, par, typ, msg):
	        d = gtk.MessageDialog(par, gtk.DIALOG_MODAL, typ, gtk.BUTTONS_OK, msg)
	        d.set_property('use-markup', True)
	
	        d.run()
	        d.destroy()

	def close_window(self, window):
		window.hide()

class MeldLauncher(gedit.Plugin):

	def __init__(self):
		gedit.Plugin.__init__(self)
		self._instances = {}

	def activate(self, window):
		self._instances[window] = MeldLauncherWindowHelper(self, window)
	
	def deactivate(self, window):
		self._instances[window].deactivate()
		del self._instances[window]

	def update_ui(self, window):
		self._instances[window].update_ui()
