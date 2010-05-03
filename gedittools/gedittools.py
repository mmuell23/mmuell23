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
		self._tag_list = {} #all applied tags by document 
		self._tag_lib = {} #all tags to be assigned
		self._active_tag_switch = 0
		
	def deactivate(self):
		self._remove_menu()
		self._window = None
		self._plugin = None
		self._action_group = None
		
	def _insert_menu(self):
		self._action_group = gtk.ActionGroup("GeditToolsGroup")
		return True
		
	def _remove_menu(self):
		manager = self._window.get_ui_manager()
		manager.remove_ui(self._ui_id)
		manager.remove_action_group(self._action_group)
		manager.ensure_update()

	def update_ui(self):
		self._action_group.set_sensitive(self._window.get_active_document() != None)
		self._current_doc = self._window.get_active_document()

		if not self._tag_list.has_key(self._current_doc):
			self._tag_list[self._current_doc] = {}
		
		if not self._highlighted_pairs.has_key(self._current_doc):
			self._highlighted_pairs[self._current_doc] = []

		#create tags
		if self._current_doc:

			self._tag_folded = self._current_doc.get_tag_table().lookup('folded')
			if self._tag_folded == None:
				self._tag_folded = self._current_doc.create_tag('folded', foreground="#000000", background="#FBEC5D")		

			self._tag_active_0 = self._current_doc.get_tag_table().lookup('active_0')
			self._tag_active_1 = self._current_doc.get_tag_table().lookup('active_1')
			if self._tag_active_0 == None:
				self._tag_active_0 = self._current_doc.create_tag('active_0', foreground="#000000", background="#CCDDFF")
			if self._tag_active_1 == None:
				self._tag_active_1 = self._current_doc.create_tag('active_1', foreground="#000000", background="#FFDDCC")

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
			self.start_highlighting()
			#self.highlight_selection()

	def start_highlighting(self):
		selection = self._current_doc.get_selection_bounds()
		if selection:
			self.highlight_xml(selection[0], selection[1])
		#iterate all tags and apply them to current document

		#self.message_dialog(None, 0, str(len(self._highlighted_pairs[self._current_doc])))
		self._highlighted_pairs[self._current_doc].reverse()

		#first of all: remove all other tags
		for triple in self._highlighted_pairs[self._current_doc]:
			self._current_doc.remove_tag(triple[0], triple[1], triple[2])

		#iterate all new iters and apply tags	
		for triple in self._highlighted_pairs[self._current_doc]:
			self._current_doc.apply_tag(triple[0], triple[1], triple[2])
			
	def highlight_xml(self, s, e):
		is_xml = self.is_xml_tag(s,e)

		self._highlighted_pairs[self._current_doc] = []

		if is_xml:
			selected_text = self._current_doc.get_text(s, e)
			selected_text = self.format_starttag(selected_text)
			#s.set_line_offset(s.get_line_offset() + len(selected_text))
			self.message_dialog(None, 0, "Tag:" + selected_text)
			closing_tag_iter = self.move_to_end_tag(s.copy(), selected_text)

			#was this an inline command?
			if self._is_inline:
				closing_tag_iter = s.copy()
				closing_tag_iter.forward_to_line_end()
				line = self._current_doc.get_text(s, closing_tag_iter)
				offset = string.find(line, "/>") + s.get_line_offset() +2
				closing_tag_iter.set_line_offset(offset)
			
			if closing_tag_iter:
				if self._active_tag_switch == 1:
					self._active_tag_switch = 0
					self._highlighted_pairs[self._current_doc].append([self._tag_active_1, s, closing_tag_iter])
				else:
					self._highlighted_pairs[self._current_doc].append([self._tag_active_0, s, closing_tag_iter])
					self._active_tag_switch = 1
				self._current_doc.select_range(s,s)
	#format the starttag: to ignore all attributes, kick out the ">" if present
	def format_starttag(self, tag):
		if tag[-1:] == ">":
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
			return True	

		#only tag keyword selected	
		if s.get_line_index() > 0:
			s.set_line_index(s.get_line_index() - 1)
		selected_text = self._current_doc.get_text(s, e)
		self._end_tag = "</" + selected_text.strip()[1:] + ">"
		return (selected_text.strip()[0] == "<")

	def get_end_tag(self, start_tag):
		return "</" + start_tag[1:] + ">"
					
	def move_to_end_tag(self, start_iter, start_tag):
		self._tag_list[self._current_doc][start_tag] = 0
		self._tag_list[self._current_doc][self.get_end_tag(start_tag)] = 0

		has_next_line = True
		is_first_line = True
		self._is_inline = False #Flag for inline commands
		
		while(has_next_line):
			s = start_iter
			e = start_iter.copy()

			#not on first line? set index to beginning
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

			#another xml tag? call that function again
			another_tag = re.search('\<[a-z][a-z]*', line_content)
			self.message_dialog(None, 0, "Start_tag: " + start_tag)
			if another_tag and another_tag.group(0) != start_tag:

				pos_another_tag = string.find(line_content, another_tag.group(0))

				self.message_dialog(None, 0, "Tag: " + another_tag.group(0) + "; Pos: " + str(pos_another_tag))

				s1 = s.copy()
				s1.set_line_offset(s1.get_line_offset() + pos_another_tag + 1)

				e1 = s.copy()
				e1.set_line_offset(e1.get_line_offset() + len(another_tag.group(0)) + 1)

				self.message_dialog(None, 0, "Tag ausgelesen: " + self._current_doc.get_text(s1, e1))
				
				self._tag_list[self._current_doc][another_tag.group(0)] = 0
				self._tag_list[self._current_doc]["</" + another_tag.group(0)[1:] + ">"] = 0
				
				self.highlight_xml(s1, e.copy())
				#self.message_dialog(None, 0, "</" + another_tag.group(0)[1:] + ">")

			while scan_current_line:
				#special case: inline tags like <example test="blahblah"/>
				#detects inline tags in check of FIRST LINE only
				closed_tag = string.find(line_content, "/>")
				#found "/>" and no other "<" in between? Then this is an inline command
				if closed_tag > 0 and string.find(line_content[1:closed_tag], "<") == -1 and string.find(line_content[0:closed_tag], start_tag) >= 0:
					#nothing else found so far? begins with inline command. so, presume, this is the one we want to mark.
					if self._tag_list[self._current_doc][start_tag] == 0:
						self._is_inline = True
						return s
					else:
						s.set_line_offset(closed_tag)
						line_content = self._current_doc.get_text(s,e)
			
				#oeffnet sich noch mal der starttag?
				#wenn ja, passiert das vor dem endtag, wenn einer da ist?
				pos_start_tag = string.find(line_content, start_tag)
				pos_end_tag   = string.find(line_content, self.get_end_tag(start_tag))

				found_start_tag = (pos_start_tag >= 0)
				found_end_tag = (pos_end_tag >= 0)

				if (found_start_tag and not found_end_tag) or (found_start_tag and found_end_tag and pos_start_tag < pos_end_tag):
					self._tag_list[self._current_doc][start_tag] = self._tag_list[self._current_doc][start_tag] + 1
					s.set_line_offset(s.get_line_offset() + pos_start_tag + len(start_tag))
					line_content = self._current_doc.get_text(s,e)
				elif (found_end_tag and not found_start_tag) or (found_start_tag and found_end_tag and pos_end_tag < pos_start_tag):
					self._tag_list[self._current_doc][self.get_end_tag(start_tag)] = self._tag_list[self._current_doc][self.get_end_tag(start_tag)] + 1
					s.set_line_offset(s.get_line_offset() + pos_end_tag + len(self.get_end_tag(start_tag)))
					if self._tag_list[self._current_doc][self.get_end_tag(start_tag)] == self._tag_list[self._current_doc][start_tag]:
						scan_current_line = False
					line_content = self._current_doc.get_text(s,e)
				else:
					scan_current_line = False
				
				if self._tag_list[self._current_doc][self.get_end_tag(start_tag)] == self._tag_list[self._current_doc][start_tag]:
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

				
class GeditTools(gedit.Plugin):

	def __init__(self):
		gedit.Plugin.__init__(self)
		self._instances = {}

	def activate(self, window):
		self._instances[window] = GeditToolsWindowHelper(self, window)
	
	def deactivate(self, window):
		self._instances[window].deactivate()
		del self._instances[window]

	def update_ui(self, window):
		self._instances[window].update_ui()
