from gettext import gettext as _

import gtk, gtk.glade
import gedit
import re
import os
import glib
import string

ui_str = """<ui>
<menubar name="MenuBar">
<menu name="SearchMenu" action="Search">
<placeholder name="SearchOps_2">
<menuitem name="GeditToolsAction" action="GeditToolsAction"/>
</placeholder>
</menu>
</menubar>
<toolbar name="ToolBar">
<placeholder name="Tool_Opt4"><toolitem name="GeditToolsAction" action="GeditToolsAction"/></placeholder>
</toolbar>
</ui>
"""


#plugin
class GeditToolsWindowHelper:
	def __init__(self, plugin, window):
		self._window = window
		self._plugin = plugin
		self._insert_menu()
		self._highlighted_pairs = {}
		self._tag_lib = {}
		
	def deactivate(self):
		self._remove_menu()
		self._window = None
		self._plugin = None
		self._action_group = None
		
		
	def _insert_menu(self):
		#manager = self._window.get_ui_manager()
		self._action_group = gtk.ActionGroup("GeditToolsGroup")
		#self._action_group.add_actions([("GeditToolsAction", gtk.STOCK_COPY, _("Compare current file"), '<Control><Shift>h', _("Compare current file"), self.on_compare_file)])
		#manager.insert_action_group(self._action_group, -1)
		#self._ui_id = manager.add_ui_from_string(ui_str)
		return True
		
	def _remove_menu(self):
		manager = self._window.get_ui_manager()
		manager.remove_ui(self._ui_id)
		manager.remove_action_group(self._action_group)
		manager.ensure_update()

	def update_ui(self):
		self._action_group.set_sensitive(self._window.get_active_document() != None)
		self._current_doc = self._window.get_active_document()

		if not self._tag_lib.has_key(self._current_doc):
			self._tag_lib[self._current_doc] = {}
		
		if not self._highlighted_pairs.has_key(self._current_doc):
			self._highlighted_pairs[self._current_doc] = []

		
		if self._current_doc:
			self._tag_active = self._current_doc.get_tag_table().lookup('active')
			self._tag_folded = self._current_doc.get_tag_table().lookup('folded')

			if self._tag_active == None:
				self._tag_active = self._current_doc.create_tag('active', foreground="#000000", background="#CCDDFF")
			if self._tag_folded == None:
				self._tag_folded = self._current_doc.create_tag('folded', foreground="#000000", background="#FBEC5D")		

		self.timer = glib.timeout_add(500, self.general_timer)

	def message_dialog(self, par, typ, msg):
	        d = gtk.MessageDialog(par, gtk.DIALOG_MODAL, typ, gtk.BUTTONS_OK, msg)
	        d.set_property('use-markup', False)
	        d.run()
	        d.destroy()

	def close_window(self, window):
		window.hide()

	def general_timer(self):
		if self._current_doc:
			self.highlight_xml()
			#self.highlight_selection()

	def highlight_xml(self):
		#if selection is a tag, try to find the end tag and highlight everything in between
		selection = self._current_doc.get_selection_bounds()
		if selection:

			#first of all: remove all other tags
			for triple in self._highlighted_pairs[self._current_doc]:
				#self.message_dialog(None, 0, "Ausblenden")
				self._current_doc.remove_tag(triple[0], triple[1], triple[2])
			self._highlighted_pairs[self._current_doc] = []

			#get selection, search for end-tag and highlight everything in between
			s,e = selection
			is_xml = self.is_xml_tag(s,e)

			if is_xml:
				selected_text = self._current_doc.get_text(s, e)
				selected_text = self.format_starttag(selected_text)
				#s.set_line_offset(s.get_line_offset() + len(selected_text))
				closing_tag_iter = self.move_to_end_tag(s.copy(), selected_text)
				if closing_tag_iter:
					#self.message_dialog(None,0,selected_text)
					#self.message_dialog(None, 0, str(closing_tag_iter.get_line()))
					self._current_doc.apply_tag(self._tag_active, s, closing_tag_iter)
					self._highlighted_pairs[self._current_doc].append([self._tag_active, s, closing_tag_iter])

	#format the starttag: to ignore all attributes, kick out the ">" if present
	def format_starttag(self, tag):
		if tag[-1:] == ">":
			#self.message_dialog(None, 0, "removed <:" + tag + " to " + tag[0:-1])
			return tag[0:-1]
		else:
			return tag
			
	#place s and e to the beginning and end of the tag
	def is_xml_tag(self, s, e):
		#complete tag selected
		selected_text = self._current_doc.get_text(s, e)
		is_xml = (selected_text.strip()[0] == "<")
		if is_xml:
			self._end_tag = "</" + selected_text[1:-1] + ">"
			#self.message_dialog(None, 0, self._end_tag)
			return True	

		#only tag keyword selected	
		s.set_line_index(s.get_line_index() - 1)
		selected_text = self._current_doc.get_text(s, e)
		self._end_tag = "</" + selected_text.strip()[1:] + ">"
		return (selected_text.strip()[0] == "<")
					
	def move_to_end_tag(self, start_iter, start_tag):
		self._tag_lib[self._current_doc][start_tag] = 0
		self._tag_lib[self._current_doc][self._end_tag] = 0

		has_next_line = True
		is_first_line = True

		
		while(has_next_line):
			s = start_iter
			e = start_iter.copy()
			if not is_first_line:
				s.set_line_offset(0)
			is_first_line = False
			
			e.forward_to_line_end()

			if e.get_line() > s.get_line():
				s.set_line(e.get_line())
				s.set_line_offset(0)
			
			line_content = s.get_text(e)
			line_content = self._current_doc.get_text(s,e)
			scan_current_line = True

			while scan_current_line:
				#oeffnet sich noch mal der starttag?
				#wenn ja, passiert das vor dem endtag, wenn einer da ist?
				pos_start_tag = string.find(line_content, start_tag)
				pos_end_tag   = string.find(line_content, self._end_tag)
				#self.message_dialog(None, 0, line_content + " at:" + str(s.get_line_index()) + "/" + str(e.get_line_index()) + "found at:" + str(pos_start_tag) + "/" + str(pos_end_tag))

				found_start_tag = (pos_start_tag >= 0)
				found_end_tag = (pos_end_tag >= 0)

				#self.message_dialog(None, 0, "Zeile " + str(s.get_line()) + ": " + line_content)

				if (found_start_tag and not found_end_tag) or (found_start_tag and found_end_tag and pos_start_tag < pos_end_tag):
					#self.message_dialog(None, 0, "Found Starttag(" + start_tag + ") before Endtag(" + self._end_tag + "): Starttag: " + str(pos_start_tag) + " / Endtag: " +str(pos_end_tag) + " / Line: " + str(s.get_line()))
					self._tag_lib[self._current_doc][start_tag] = self._tag_lib[self._current_doc][start_tag] + 1
					s.set_line_offset(s.get_line_offset() + pos_start_tag + len(start_tag))
					line_content = self._current_doc.get_text(s,e)
				elif (found_end_tag and not found_start_tag) or (found_start_tag and found_end_tag and pos_end_tag < pos_start_tag):
					#self.message_dialog(None, 0, "Found End(" + self.end_tag + ") before Starttag(" + start_tag + "): Starttag: " + str(pos_start_tag) + " / Endtag: " +str(pos_end_tag) + " / Line: " + str(s.get_line()))
					self._tag_lib[self._current_doc][self._end_tag] = self._tag_lib[self._current_doc][self._end_tag] + 1
					s.set_line_offset(s.get_line_offset() + pos_end_tag + len(self._end_tag))
					if self._tag_lib[self._current_doc][self._end_tag] == self._tag_lib[self._current_doc][start_tag]:
						scan_current_line = False
					line_content = self._current_doc.get_text(s,e)
				else:
					scan_current_line = False
				
				if self._tag_lib[self._current_doc][self._end_tag] == self._tag_lib[self._current_doc][start_tag]:
					#self.message_dialog(None, 0, "gleiche anzahl end wie start")
					return s

			has_next_line = start_iter.forward_line()
		return None
		
	def highlight_selection(self):
		selection = self._current_doc.get_selection_bounds()

		if selection:
			self._current_doc.set_enable_search_highlighting(True)
			s,e = selection
			selected_text = self._current_doc.get_text(s, e)
			self._current_doc.set_search_text(selected_text, 1)
			#self._current_doc.search_forward(self._current_doc.get_start_iter(), self._current_doc.get_end_iter(), s, e)
			return
			self._current_doc.apply_tag(self._tag_active, s, e)
			#i = 0
			#error = False

			#aktuellen noch merken

			#while (not error):
			#	if(not self._current_doc.goto_line(i)):
			#		error = true;
			#	if not error:
			#	i = i+1 <test>

	

				
class GeditTools(gedit.Plugin):

	def __init__(self):
		gedit.Plugin.__init__(self)
		self._instances = {}
		#</test>

	def activate(self, window):
		self._instances[window] = GeditToolsWindowHelper(self, window)
	
	def deactivate(self, window):
		self._instances[window].deactivate()
		del self._instances[window]

	def update_ui(self, window):
		self._instances[window].update_ui()
