from gettext import gettext as _

import gtk, gtk.glade
import gedit
import re
import os

ui_str = """<ui>
<menubar name="MenuBar">
<menu name="SearchMenu" action="Search">
<placeholder name="SearchOps_2">
<menuitem name="SortDocumentAction" action="SortDocumentAction"/>
</placeholder>
</menu>
</menubar>
<toolbar name="ToolBar">
<placeholder name="Tool_Opt4"><toolitem name="SortDocumentAction" action="SortDocumentAction"/></placeholder>
</toolbar>
</ui>
"""


#plugin
class SortDocumentWindowHelper:
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

		self._action_group = gtk.ActionGroup("SortDocumentGroup")
		self._action_group.add_actions([("SortDocumentAction", gtk.STOCK_SORT_DESCENDING, _("Sort document alphabetically"), '<Control><Shift>o', _("Sort document alphabetically"), self.on_compare_file)])
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


		lines = current_doc.get_text(current_doc.get_start_iter(), current_doc.get_end_iter()).split("\n")
		lines = self.qsort(lines)

		current_doc.set_text("".join(["%s\n" % (k) for k in lines]))
		
	def qsort(self, lst):
		if len(lst) <= 1:
			return lst
		pivot = lst.pop(0)
		greater_eq = self.qsort([i for i in lst if i >= pivot])
		lesser = self.qsort([i for i in lst if i < pivot])
		return lesser + [pivot] + greater_eq


	def message_dialog(self, par, typ, msg):
	        d = gtk.MessageDialog(par, gtk.DIALOG_MODAL, typ, gtk.BUTTONS_OK, msg)
	        d.set_property('use-markup', True)
	
	        d.run()
	        d.destroy()

	def close_window(self, window):
		window.hide()

	def get_filename(self, path):
		return path.split("/")[-1]
		
class SortDocument(gedit.Plugin):

	def __init__(self):
		gedit.Plugin.__init__(self)
		self._instances = {}

	def activate(self, window):
		self._instances[window] = SortDocumentWindowHelper(self, window)
	
	def deactivate(self, window):
		self._instances[window].deactivate()
		del self._instances[window]

	def update_ui(self, window):
		self._instances[window].update_ui()
