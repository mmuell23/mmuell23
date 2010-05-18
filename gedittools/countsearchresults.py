from gettext import gettext as _

import gtk
import gedit
import re
import string

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

class SearchResultCounter():
	def __init__(self, window):
		self._window = window
		self._counter = 0
		self._message_id = None #id of message in status bar
		
	def count_selection(self, doc):
		if not doc:	
			return
		
		selection = self.get_selected_text(doc)

		if len(selection) < 1:
			return
			
		text = doc.get_text(doc.get_start_iter(), doc.get_end_iter())
		text = unicode(text)
		
		
		counter = 0
		pos = string.find(text, selection)
		while(pos > 0):
			counter = counter + 1
			offset = pos + len(selection)
			text = text[offset:]
			pos = string.find(text, selection)

		statusbar = self._window.get_statusbar()
		context_id = statusbar.get_context_id("Searchcounter")
		statusbar.pop(context_id)
		message_id = statusbar.push(context_id, "Counted Elements: " + str(counter))
		
	def get_selected_text(self, doc):
		selection = doc.get_selection_bounds()
		current_pos_mark = doc.get_insert()
		
		if len(selection):
			start, end = selection
			return start.get_slice(end)
		return ''
	        
