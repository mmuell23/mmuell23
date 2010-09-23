from gettext import gettext as _

import gtk, gtk.glade
from gedittools_configure import GeditToolsConfiguration
import gedit
import re
import os
import glib
import string
from ConfigParser import ConfigParser
from countsearchresults import SearchResultCounter
from meldlauncher import MeldLauncher

class Tag():
	def __init__(self, tag, start):
		self._tag = tag
		self._start = start
		self._end = None
		self._complete_tag = None
		
	def set_end(self, end):
		self._end = end
		
	def set_start(self, start):
		self._start = start

	def start(self):
		return self._start
	
	def end(self):
		return self._end
	
	def has_end(self):
		return (self._end != None)
	
	def tag(self):
		return self._tag
	
	def is_identical_to(self, tag):
		return tag == self._tag
	
	def tostring(self):
		return self._tag + ": " + str(self._start) + " / " + str(self._end)
	
	def set_complete_tag(self, complete_tag):
		self._complete_tag = complete_tag
		
	def complete_tag(self):
		return self._complete_tag

class XmlHighlighter():
	def __init__(self, window, opener):
		self._window = window
		self._highlighted_pairs = {} #pairs of highlighted iters
		self._tag_list = {} #all applied tags by document 
		self._tag_lib = {} #all tags to be assigned
		self._opener = opener
				
	def update(self, doc):
		self._current_doc = doc
	
		#initialize tags	
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
		
	def start_highlighting(self):
		#first of all: remove all other tags
		i = 0
		l = len(self._tag_lib[self._current_doc])
		
		for tag in self._highlighted_pairs[self._current_doc]:
			if tag.start() != None and tag.end() != None:
				iter_start = self._current_doc.get_iter_at_offset(tag.start())
				iter_end = self._current_doc.get_iter_at_offset(tag.end())		
				self._current_doc.remove_tag(self._tag_lib[self._current_doc][i%l], iter_start, iter_end)
				i = i + 1

		self._highlighted_pairs[self._current_doc] = []	
		
		#read text
		text = self._current_doc.get_text(self._current_doc.get_start_iter(), self._current_doc.get_end_iter())
		text = unicode(text)
		
		#get tags
		self._highlighted_pairs[self._current_doc] = self.get_tags_to_highlight(text)
		
		#now, show all tags
		i = 0
		for tag in self._highlighted_pairs[self._current_doc]:
			if tag.start() != None and tag.end() != None:# and i < 13:
				iter_start = self._current_doc.get_iter_at_offset(tag.start())
				iter_end = self._current_doc.get_iter_at_offset(tag.end())
				for remove_tag in self._tag_lib[self._current_doc]:
					self._current_doc.remove_tag(remove_tag, iter_start, iter_end)
				self._current_doc.apply_tag(self._tag_lib[self._current_doc][i%l], iter_start, iter_end)	
				i = i + 1
			
		return True			
		
	#highlight single words instead of xml trees
	def highlight_selection(self):
		selection = self._current_doc.get_selection_bounds()

		if selection:
			self._current_doc.set_enable_search_highlighting(True)
			s,e = selection
			selected_text = self._current_doc.get_text(s, e)
			self._current_doc.set_search_text(selected_text, 1)		
		
	#get a list of all tags in the document
	def get_tags_to_highlight(self, text):
	
		#search all opening and closing tags
		it = re.finditer(r"<(/)?([a-zA-Z0-9_\-:]+)((\s)*[A-Za-z:0-9]+\=\"[_\-a-zA-Z0-9\s:\.]*\")*(/)?>", text, re.I)
		tags = [] 
		
		#iterate over tags and decide what to do
		for m in it: 

			complete_tag = m.group(0)
			tag_word = complete_tag[0:string.find(complete_tag, " ")]
			is_end_tag = False
			is_inline_tag = False
			
			#closing tag
			if tag_word[0:2] == "</":
				is_end_tag = True
				tag_word = complete_tag[2:string.find(complete_tag, " ")]
			#opening tag
			else:
				tag_word = complete_tag[1:string.find(complete_tag, " ")]
		
			#inline tag
			if complete_tag[-2:] == "/>":
				is_inline_tag = True
				
			#in any case: append opening and inline tag to list of tags
			if not is_end_tag:
				tag = Tag(tag_word, m.span()[0])
				tag.set_complete_tag(complete_tag)
				if is_inline_tag:
					tag.set_end(m.span()[1]) 
				tags.append(tag)
			#is closing tag? look for last added corresponding opening tag and update its end position
			else:
				tags.reverse()
				for tag in tags:
					#offener tag passend zum schliessenden? mach ihn zu
					if tag.tag() == tag_word and not tag.has_end():
						tag.set_end(m.span()[1])
					else:
						pass
				tags.reverse()
			
		return tags
			
