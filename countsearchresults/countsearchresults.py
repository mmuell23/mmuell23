from gettext import gettext as _

import gtk
import gedit
import re

ui_str = """<ui>
<menubar name="MenuBar">
<menu name="SearchMenu" action="Search">
<placeholder name="SearchOps_2">
<menuitem name="SearchResultAction" action="SearchResultAction"/>
</placeholder>
</menu>
</menubar>
<toolbar name="ToolBar">
<placeholder name="Tool_Opt3"><toolitem name="SearchResultAction" action="SearchResultAction"/></placeholder>
</toolbar>
</ui>
"""

class CountSearchResultsPluginWindowHelper:
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

		self._action_group = gtk.ActionGroup("CountSearchResultGroup")
		self._action_group.add_actions([("SearchResultAction", gtk.STOCK_ADD, _("Count occurances of selection"), '<Control><Shift>f', _("Count occurances of selection"), self.on_count_selection)])
		manager.insert_action_group(self._action_group, -1)

		self._ui_id = manager.add_ui_from_string(ui_str)

	def _remove_menu(self):
		manager = self._window.get_ui_manager()
		manager.remove_ui(self._ui_id)
		manager.remove_action_group(self._action_group)
		manager.ensure_update()

	def update_ui(self):
		self._action_group.set_sensitive(self._window.get_active_document() != None)

	def on_count_selection(self, action):
		doc = self._window.get_active_document()
		if not doc:	
			return
			
		selection = self.get_selected_text(doc)

		if len(selection) < 1:
			return
			
		text = doc.get_text(doc.get_start_iter(), doc.get_end_iter())
		count = re.findall(selection, text)

		self.message_dialog(None, 0, "Occurances of " + selection + ": " + str(len(count)))

	def get_selected_text(self, doc):
		selection = doc.get_selection_bounds()
		current_pos_mark = doc.get_insert()
		
		if len(selection):
			start, end = selection
			return start.get_slice(end)
		return ''

	def message_dialog(self, par, typ, msg):
	        d = gtk.MessageDialog(par, gtk.DIALOG_MODAL, typ, gtk.BUTTONS_OK, msg)
	        d.set_property('use-markup', True)
	
	        d.run()
	        d.destroy()


class CountSearchResultsPlugin(gedit.Plugin):

	def __init__(self):
		gedit.Plugin.__init__(self)
		self._instances = {}

	def activate(self, window):
		self._instances[window] = CountSearchResultsPluginWindowHelper(self, window)
	
	def deactivate(self, window):
		self._instances[window].deactivate()
		del self._instances[window]

	def update_ui(self, window):
		self._instances[window].update_ui()
