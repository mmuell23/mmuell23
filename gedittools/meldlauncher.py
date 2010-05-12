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
class MeldLauncher:

	def __init__(self, window):
		self._window = window

	def compare(self, current_doc):
		if not current_doc:
			return
			
		app = gedit.app_get_default() 

		#only one document in gedit? stop this
		if current_doc == None or len(app.get_documents()) == 1:
			return
		
		#only 2 documents at all? start comparing straight away
		if (len(app.get_documents()) == 2):
			self._path_1 = app.get_documents()[0].get_uri_for_display()
			self._path_2 = app.get_documents()[1].get_short_name_for_display()
			self.start_comparing()
			return

		self._path_1 = current_doc.get_uri_for_display()

		#build selection screen
		self._snapopen_glade = gtk.glade.XML( os.path.dirname( __file__ ) + "/meldlauncher.glade" )
		self._snapopen_window = self._snapopen_glade.get_widget( "MeldLauncherWindow" )	

		#fill in current filename
		labelbox = self._snapopen_glade.get_widget("labelbox")
		label = gtk.Label()
		label.set_use_markup(True)
		label.set_markup("Compare <b>" + current_doc.get_short_name_for_display() + "</b> to ...")
		label.set_justify(gtk.JUSTIFY_LEFT)
		label.set_padding(15,15)
		
		labelbox.pack_start(label, True, True, 0)

		#build filenames in listbox
		self._snapopen_window.set_title("Select file to compare with")
		self._snapopen_window.set_transient_for(self._window)

		#iterate all opened files
		filelist_group = self._snapopen_glade.get_widget("buttonbox")
		for doc in gedit.app_get_default().get_documents():
			button = gtk.Button(self.get_filename(doc.get_uri_for_display()), None, False)
			button.set_tooltip_text(doc.get_uri()[7:])
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

	def get_filename(self, path):
		return path.split("/")[-1]
		
