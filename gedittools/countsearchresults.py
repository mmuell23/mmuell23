from gettext import gettext as _
from gi.repository import GObject, Gedit, Gtk
import re
import string
import glib
import sys

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

class SearchResultCounterPlugin():
    __gtype_name__ = "SearchResultCounterPlugin"

    def __init__(self, w):
        self._counter = 0
        self._active = False
        self._message_id = None #id of message in status bar
        self.window = w
        
    def do_activate(self):
        pass
        
    def do_deactivate(self):
        pass
        
    def do_update_state(self):
        self._current_doc = self.window.get_active_document()
        self.count_selection(self._current_doc)
        self.highlight_selection()
        
    #highlight single words instead of xml trees
    def highlight_selection(self):
        selection = self._current_doc.get_selection_bounds()

        if selection:
            self._current_doc.set_enable_search_highlighting(True)
            s,e = selection
            selected_text = self._current_doc.get_text(s, e, True)
            self._current_doc.set_search_text(selected_text, 1)            
        
    def count_selection(self, doc):
        if not doc:    
            return
        
        selection = self.get_selected_text(doc)

        if len(selection) < 1:
            return
            
        text = doc.get_text(doc.get_start_iter(), doc.get_end_iter(), True)
        text = unicode(text)
        
        counter = 0
        pos = string.find(text, selection)
        while(pos > 0):
            counter = counter + 1
            offset = pos + len(selection)
            text = text[offset:]
            pos = string.find(text, selection)

        statusbar = self.window.get_statusbar()
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
            
