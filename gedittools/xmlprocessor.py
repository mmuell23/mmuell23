#import gtk, gtk.glade
from gi.repository import GObject, Gedit
#import gedit
import re
import os

class XslProcessor:
	def __init__(self, window, caller):
		self._window = window
		self._caller = caller
		
	def transform_xml(self):
		pass
