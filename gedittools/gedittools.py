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

		if self._current_doc and not self._tag_lib.has_key(self._current_doc):
			self._tag_lib[self._current_doc] = []
			self._tag_lib[self._current_doc].append(self._current_doc.create_tag('active_0', foreground="#000000", background="#CCDDFF"))
			self._tag_lib[self._current_doc].append(self._current_doc.create_tag('active_1', foreground="#000000", background="#FFDDCC"))
			self._tag_lib[self._current_doc].append(self._current_doc.create_tag('active_2', foreground="#000000", background="#CCFFDD"))
			self._tag_lib[self._current_doc].append(self._current_doc.create_tag('active_3', foreground="#000000", background="#DDFFCC"))
			self._tag_lib[self._current_doc].append(self._current_doc.create_tag('active_4', foreground="#000000", background="#DDCCFF"))

		if not self._tag_list.has_key(self._current_doc):
			self._tag_list[self._current_doc] = {}

		#initialize list for highlighted tags
		if not self._highlighted_pairs.has_key(self._current_doc):
			self._highlighted_pairs[self._current_doc] = []

		#create tags
		if self._current_doc:
			self._tag_folded = self._current_doc.get_tag_table().lookup('folded')
			if self._tag_folded == None:
				self._tag_folded = self._current_doc.create_tag('folded', foreground="#000000", background="#FBEC5D")		
				
		self.timer = glib.timeout_add(500, self.general_timer)

	def alert(self, message):
		self.message_dialog(None, 0, message)
		
	#helper to show a message dialog
	def message_dialog(self, par, typ, msg):
		d = gtk.MessageDialog(par, gtk.DIALOG_MODAL, typ, gtk.BUTTONS_OK, msg)
		d.set_property('use-markup', False)
		d.run()
		d.destroy()

	def close_window(self, window):
		window.hide()

	#general timer. runs always
	def general_timer(self):
		xml_highlighted = False
		if self._current_doc:
			xml_highlighted = self.start_highlighting()

		if not xml_highlighted:
			self.highlight_selection()

	def start_highlighting(self):
		selection = self._current_doc.get_selection_bounds()
		was_xml = False
		if selection:
			#first of all: remove all other tags
			for triple in self._highlighted_pairs[self._current_doc]:
				self._current_doc.remove_tag(triple[0], triple[1], triple[2])

			self._highlighted_pairs[self._current_doc] = []		
			self.highlight_xml(selection[0], selection[1], 0)
			
			#now, show all tags
			self._highlighted_pairs[self._current_doc].reverse()
			
			for triple in self._highlighted_pairs[self._current_doc]:
				#self.alert("Highlighte Text:" + self._current_doc.get_text(triple[1], triple[2]))
				for remove_tag in self._tag_lib[self._current_doc]:
					self._current_doc.remove_tag(remove_tag, triple[1], triple[2])
				self._current_doc.apply_tag(triple[0], triple[1], triple[2])				
				was_xml = True
		return was_xml
				
	def highlight_xml(self, s, e, level):
		#self.alert(self._current_doc.get_text(s,e))
		is_xml = self.is_xml_tag(s,e)

		if is_xml:
			selected_text = self._current_doc.get_text(s, e)
			selected_text = self.format_starttag(selected_text)
			#s.set_line_offset(s.get_line_offset() + len(selected_text))
			closing_tag_iter = self.move_to_end_tag(s.copy(), selected_text, level)

			if closing_tag_iter:
				#self.alert(selected_text + " auf Level " + str(level))
				self._highlighted_pairs[self._current_doc].append([self._tag_lib[self._current_doc][level % len(self._tag_lib[self._current_doc])], s, closing_tag_iter])

	def move_to_end_tag(self, start_iter, start_tag, level):
		end_tag = "</" + start_tag[1:] + ">"
		self._tag_list[self._current_doc][start_tag] = 0
		self._tag_list[self._current_doc][end_tag] = 0

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

			#move to end of line
			e.forward_to_line_end()

			if e.get_line() > s.get_line():
				s.set_line(e.get_line())
				s.set_line_offset(0)
			
			line_content = s.get_text(e)
			line_content = self._current_doc.get_text(s,e)
			scan_current_line = True
			reg_ex = "<[a-zA-Z0-9_]+"
			#self.alert(reg_ex)

			found_tags = re.findall(reg_ex, line_content)
			another_tag = None
			for found_tag in found_tags:
				if found_tag != start_tag:
					another_tag = found_tag
					break
			
			#another_tag = re.search(reg_ex, line_content)
			if another_tag: #hier noch beruecksichtigen, wenn gleiche tags verschachtelt sind. sollte ueber die anzahl gefundener tags gehen
				pos_another_tag = string.find(line_content, another_tag) 
				s1 = s.copy()
				e1 = s1.copy()
				s1.set_offset(s1.get_offset() + pos_another_tag)
				e1.set_offset(s1.get_offset() + len(another_tag))
				self.highlight_xml(s1, e1, level + 1)
				
			while scan_current_line:
				#special case: inline tags like <example test="blahblah"/>
				pos_closed_tag = string.find(line_content, "/>")
				#found "/>" and no other "<" in between? Then this is an inline command
				if pos_closed_tag > 0 and string.find(line_content[1:pos_closed_tag], "<") == -1 and string.find(line_content[0:pos_closed_tag], start_tag) >= 0:
					#nothing else found so far? begins with inline command. so, presume, this is the one we want to mark.
					if self._tag_list[self._current_doc][start_tag] == 0:
						s1 = s.copy() #position to conintue scanning from; also position behind "/>"
						s1.set_offset(s.get_offset() + pos_closed_tag + 2)
						self._highlighted_pairs[self._current_doc].append([self._tag_lib[self._current_doc][level % len(self._tag_lib[self._current_doc])], s, s1])
						return s1
					else:
						s.set_offset(s.get_offset() + pos_closed_tag + 2)
						line_content = self._current_doc.get_text(s,e)
			
				#oeffnet sich noch mal der starttag?
				#wenn ja, passiert das vor dem endtag, wenn einer da ist?
				pos_start_tag = string.find(line_content, start_tag)
				pos_end_tag   = string.find(line_content, end_tag)

				found_start_tag = (pos_start_tag >= 0)
				found_end_tag = (pos_end_tag >= 0)

				#starttag, kein endtag oder starttag und endtag, aber starttag vor endtag
				if (found_start_tag and not found_end_tag) or (found_start_tag and found_end_tag and pos_start_tag < pos_end_tag):
					self._tag_list[self._current_doc][start_tag] = self._tag_list[self._current_doc][start_tag] + 1
					s.set_offset(s.get_offset() + pos_start_tag + len(start_tag))
					line_content = self._current_doc.get_text(s,e)
				elif (found_end_tag and not found_start_tag) or (found_start_tag and found_end_tag and pos_end_tag < pos_start_tag):
					self._tag_list[self._current_doc][end_tag] = self._tag_list[self._current_doc][end_tag] + 1
					s.set_offset(s.get_offset() + pos_end_tag + len(end_tag))
					if self._tag_list[self._current_doc][end_tag] == self._tag_list[self._current_doc][start_tag]:
						scan_current_line = False
					line_content = self._current_doc.get_text(s,e)
				else:
					scan_current_line = False
				
				if self._tag_list[self._current_doc][end_tag] == self._tag_list[self._current_doc][start_tag]:
					return s

			has_next_line = start_iter.forward_line()
		return None

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
			return True	

		#only tag keyword selected	
		if s.get_line_index() > 0:
			s.set_line_index(s.get_line_index() - 1)
		selected_text = self._current_doc.get_text(s, e)
		return (selected_text.strip()[0] == "<")

	def get_end_tag(self, start_tag):
		return "</" + start_tag[1:] + ">"
		
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
