#  mscore/__init__.py
#
#  Copyright 2025 Leon Dionne <ldionne@dridesign.sh.cn>
#  Modified 2025 Diego Denolf <graffesmusic@gmail.com>
#  to allow frame copy
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
"""
A python library for opening/inspecting/modifying MuseScore3 files.
"""
import os, sys, logging, configparser, glob, io
from os.path import join, basename, splitext, exists
from appdirs import user_config_dir, user_data_dir
import xml.etree.ElementTree as et
try:
	from functools import cache
except ImportError:
	from functools import lru_cache as cache
from functools import reduce
from operator import or_
from zipfile import ZipFile
from copy import deepcopy
from sf2utils.sf2parse import Sf2File
from console_quiet import ConsoleQuiet
from node_soso import SmartNode, SmartTree

__version__ = "1.16.3"

CHANNEL_NAMES = ['normal', 'open', 'mute', 'arco', 'tremolo', 'crescendo',
				 'marcato', 'staccato', 'flageoletti', 'slap', 'pop', 'pizzicato']

CC_VOLUME       = 7
CC_BALANCE      = 8
CC_PAN          = 10
CC_BANK_MSB     = 0
CC_BANK_LSB     = 32

CC_NAMES = {
	CC_VOLUME   : 'CC_VOLUME',
	CC_BALANCE  : 'CC_BALANCE',
	CC_PAN      : 'CC_PAN',
	CC_BANK_MSB : 'CC_BANK_MSB',
	CC_BANK_LSB : 'CC_BANK_LSB'
}
DEFAULT_VOICE   = 'normal'


class VoiceName:
	"""
	Simply holds a pair of properties:
		"instrument_name", "voice"
	...and provides a string representation.

	Comparison may be made with "==", i.e.
		if voicename1 == voicename2:
	"""

	def __init__(self, instrument_name, voice):
		self.instrument_name = instrument_name
		self.voice = voice

	def __str__(self):
		return f'{self.instrument_name} ({self.voice or DEFAULT_VOICE})'

	def __eq__(self, other):
		return self.instrument_name == other.instrument_name \
			and self.voice == other.voice

def is_score(filename):
	return splitext(filename)[-1] in ['.mscx', '.mscz']

def ini_file():
	"""
	Returns a ConfigParser object, which may be used like this:

	cp = ini_file()
	for section in cp.sections():
		print(f'Section "{section}"')
		for option in cp.options(section):
			print(f'  Option "{option}"')

	The ConfigParser may be used to modify the .ini file, but that is outside of
	the (current) scope of this project. USE AT YOUR OWN RISK!
	"""
	filename = join(user_config_dir('MuseScore'), 'MuseScore3.ini')
	config = configparser.ConfigParser()
	config.read(filename)
	return config

def instruments_file():
	"""
	Returns (str) path to "instruments.xml"
	"""
	for key in ['paths\\instrumentlist1', 'paths\\instrumentlist2']:
		filename = ini_file().get('application', key)
		if exists(filename):
			return filename

@cache
def default_sound_fonts():
	filename = join(user_data_dir('MuseScore'), 'MuseScore3', 'synthesizer.xml')
	return [ node.text for node in et.parse(filename).findall('.//Fluid/val') ]

@cache
def user_soundfont_dirs():
	return ini_file()['application']['paths\\mySoundfonts'].strip('"').split(';')

@cache
def system_soundfont_dirs():
	return ['/usr/share/sounds/sf2']

@cache
def user_soundfonts():
	return list(_iter_sf_paths(user_soundfont_dirs()))

@cache
def system_soundfonts():
	return list(_iter_sf_paths(system_soundfont_dirs()))

@cache
def _user_sfpaths():
	return { basename(path):path for path in user_soundfonts() }

@cache
def _system_sfpaths():
	return { basename(path):path for path in system_soundfonts() }

@cache
def sf2(sf_name):
	if sf_name in _user_sfpaths():
		logging.debug('Inspecting user soundfont "%s"', sf_name)
		return _get_parsed_sf2(_user_sfpaths()[sf_name])
	if sf_name in _system_sfpaths():
		logging.debug('Inspecting user system "%s"', sf_name)
		return _get_parsed_sf2(_system_sfpaths()[sf_name])
	raise Exception(f'SoundFont "{sf_name}" not found')

def _iter_sf_paths(dirs):
	for d in dirs:
		yield from glob.glob(f'{d}/*.sf2')

def _get_parsed_sf2(filename):
	with open(filename, 'rb') as file:
		with ConsoleQuiet():
			return Sf2File(file)


# ----------------------------
# MuseScore classes

class Score(SmartTree):

	__default_sfnames = None
	__user_sfpaths = None
	__sys_sfpaths = None
	__sf2s = {}

	__zip_entries = None
	__zip_mscx_index = None

	USER_SF2 = 0
	SYSTEM_SF2 = 1
	MISSING_SF2 = 3

	def __init__(self, filename):
		self.filename = filename
		self.basename = basename(filename)
		self.ext = splitext(filename)[-1]
		if self.ext == '.mscx':
			self.tree = et.parse(filename)
		elif self.ext == '.mscz':
			with ZipFile(self.filename, 'r') as zipfile:
				self.__zip_entries = [
					{
						'info'  :info,
						'data'  :zipfile.read(info.filename)
					} for info in zipfile.infolist()
				]
			for idx, entry in enumerate(self.__zip_entries):
				if splitext(entry['info'].filename)[-1] == '.mscx':
					self.__zip_mscx_index = idx
					break
			if self.__zip_mscx_index is None:
				raise RuntimeError("No mscx entries found in zip file")
			with io.BytesIO(self.__zip_entries[self.__zip_mscx_index]['data']) as bob:
				self.tree = et.parse(bob)
		else:
			raise ValueError('Unsupported file extension: "{self.ext}"')
		self.element = self.tree.getroot() # Necessary member of SmartTree
		self._score_node = self.element.find('./Score')
		self._parts = { part.name:part \
			for part in Part.from_elements(self.findall('./Part'), self) }

	def find(self, path):
		return self._score_node.find(path)

	def findall(self, path):
		return self._score_node.findall(path)

	def save_as(self, filename):
		ext = splitext(filename)[-1]
		if ext == '.mscz' and self.ext == '.mscx':
			raise RuntimeError('Cannot save score imported from .mscx to .mscz format')
		self.filename = filename
		self.ext = ext
		self.save()

	def save(self):
		if self.ext == '.mscx':
			self.tree.write(self.filename, xml_declaration=True, encoding='utf-8')
		elif self.ext == '.mscz':
			with io.BytesIO() as bob:
				self.tree.write(bob)
				self.__zip_entries[self.__zip_mscx_index]['data'] = bob.getvalue()
			with ZipFile(self.filename, 'w') as zipfile:
				for entry in self.__zip_entries:
					zipfile.writestr(entry['info'], entry['data'])

	def parts(self):
		return self._parts.values()

	def instruments(self):
		return [ part.instrument() for part in self.parts() ]

	def channels(self):
		return [ channel \
			for instrument in self.instruments() \
			for channel in instrument.channels() ]

	def staffs(self):
		return [ staff \
			for part in self.parts() \
			for staff in part.staffs() ]

	@property
	def length(self):
		return list(self._parts.values())[0].staffs()[0].length

	def part(self, name):
		return self._parts[name]

	def part_names(self):
		return [ part.name for part in self.parts() ]

	def duplicate_part_names(self):
		a = self.part_names()
		return [ name for name in set(a) if a.count(name) > 1]

	def has_duplicate_part_names(self):
		return len(self.duplicate_part_names()) > 0

	def instrument_names(self):
		return [ p.instrument().name for p in self.parts() ]
        
	def find_duplicate_eids(self, source_score):
		"""Find measure eids that exist in both this score and the source score"""
		target_measure_eids = set()
		source_measure_eids = set()
		
		# Collect eids from target score (from <eid> elements)
		for eid_elem in self.tree.getroot().findall(".//eid"):
			eid = eid_elem.text
			if eid:
				target_measure_eids.add(eid)
		
		# Collect eids from source score (from <eid> elements)  
		for eid_elem in source_score.tree.getroot().findall(".//eid"):
			eid = eid_elem.text
			if eid:
				source_measure_eids.add(eid)
		
		return target_measure_eids.intersection(source_measure_eids)

	def rename_duplicate_eids(self, source_score, duplicate_eids):
		"""Rename duplicate measure eids in the source score and update system lock references"""
		import os
		import base64
		
		def generate_new_eid():
			"""Generate a new unique eid in MuseScore's exact two-part format"""
			# Generate 16 random bytes (two 64-bit values) like MuseScore's std::mt19937_64
			random_bytes = os.urandom(16)
			
			# Split into two 64-bit integers (little-endian)
			int1 = int.from_bytes(random_bytes[:8], byteorder='little')
			int2 = int.from_bytes(random_bytes[8:], byteorder='little')
			
			# Standard base64 characters (same as MuseScore)
			chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
			
			def to_base64(n):
				"""Convert uint64_t to base64 string like MuseScore's toBase64Chars"""
				if n == 0:
					return chars[0]
				result = ""
				while n > 0:
					result = chars[n % 64] + result  # Most significant first
					n = n // 64
				return result
			
			part1 = to_base64(int1)
			part2 = to_base64(int2)
			
			return f"{part1}_{part2}"
		
		# Create mapping from old to new eids
		eid_mapping = {}
		for old_eid in duplicate_eids:
			eid_mapping[old_eid] = generate_new_eid()
		
		# Update eids in source score (update <eid> element text)
		for eid_elem in source_score.tree.getroot().findall(".//eid"):
			old_eid = eid_elem.text
			if old_eid in eid_mapping:
				eid_elem.text = eid_mapping[old_eid]
		
		# Update system lock references in the source score
		src_score = source_score.tree.getroot().find(".//Score")
		if src_score is not None:
			system_locks = src_score.find("SystemLocks")
			if system_locks is not None:
				for system_lock in system_locks:
					start_measure = system_lock.find("startMeasure")
					end_measure = system_lock.find("endMeasure")
					
					# Update startMeasure reference if it points to a renamed eid
					if start_measure is not None and start_measure.text in eid_mapping:
						start_measure.text = eid_mapping[start_measure.text]
					
					# Update endMeasure reference if it points to a renamed eid  
					if end_measure is not None and end_measure.text in eid_mapping:
						end_measure.text = eid_mapping[end_measure.text]

	def copy_pictures_to_target(self, source_score, target_score_path):
		"""
		Copy embedded pictures from source score to target score file
		This should be called AFTER target.save() when the file exists
		"""
		import zipfile
		import os
		
		try:
			# Check if source has pictures
			source_zip = zipfile.ZipFile(source_score.filename, 'r')  # FIXED: ZipFile not ZFile
			picture_files = [f for f in source_zip.namelist() if f.startswith('Pictures/') and not f.endswith('/')]
			
			if not picture_files:
				source_zip.close()
				return 0
				
			# Check if target file exists
			if not os.path.exists(target_score_path):
				print(f"Warning: Target file {target_score_path} does not exist yet")
				source_zip.close()
				return 0
			
			# Open target zip file for appending
			target_zip = zipfile.ZipFile(target_score_path, 'a')
			
			# Copy each picture
			pictures_copied = 0
			for picture_path in picture_files:
				# Check if picture already exists in target
				if picture_path not in target_zip.namelist():
					# Read picture data from source
					picture_data = source_zip.read(picture_path)
					# Write to target
					target_zip.writestr(picture_path, picture_data)
					pictures_copied += 1
					#print(f"DEBUG: Copied picture: {picture_path}")
			
			target_zip.close()
			source_zip.close()
			
			return pictures_copied
				
		except Exception as e:
			print(f"Warning: Could not copy pictures from {source_score.basename}: {e}")
			return 0
                
	def concatenate_score(self, source_score, copy_frames=True, copy_title_frames=True, copy_system_locks=True, copy_pictures=False, target_path=None):
		"""
		Unified method to concatenate another Score into this one.
		"""
		from copy import deepcopy
		FRAME_TAGS = ("VBox", "HBox", "TBox", "FBox")

		# Get the actual Score elements
		tgt_score = self.tree.getroot().find(".//Score")
		src_score = source_score.tree.getroot().find(".//Score")

		if tgt_score is None or src_score is None:
			return False

		# Check for eid conflicts before processing
		duplicate_eids = self.find_duplicate_eids(source_score)
		had_duplicates = bool(duplicate_eids)
		
		# Rename duplicate eids to ensure target file has unique eids
		if duplicate_eids:
			self.rename_duplicate_eids(source_score, duplicate_eids)

		# Get all staffs from both scores
		tgt_staffs = tgt_score.findall(".//Staff")
		src_staffs = src_score.findall(".//Staff")
		
		if len(tgt_staffs) != len(src_staffs):
			return had_duplicates
		
		# Process each staff individually
		for tgt_staff, src_staff in zip(tgt_staffs, src_staffs):
			tgt_id = tgt_staff.get('id')
			src_id = src_staff.get('id')
			
			if tgt_id != src_id:
				continue
			
			# Get all elements from source staff
			src_elements = list(src_staff)
			
			# Copy elements based on options
			first_frame = True
			
			for elem in src_elements:
				if elem.tag == "Measure":
					# Always copy measures
					elem_copy = deepcopy(elem)
					tgt_staff.append(elem_copy)
					
				elif copy_frames and elem.tag in FRAME_TAGS:
					# Handle frame copying based on title frame option
					if first_frame and not copy_title_frames and elem.tag in ("VBox", "TBox"):
						texts = elem.findall(".//Text")
						looks_like_title = any(
							(t.findtext("style") or "").strip().lower() == "title" for t in texts
						)
						if looks_like_title:
							first_frame = False
							continue
					
					first_frame = False
					elem_copy = deepcopy(elem)
					tgt_staff.append(elem_copy)
		
		# Copy SystemLocks
		if copy_system_locks:
			src_system_locks = src_score.find("SystemLocks")
			if src_system_locks is not None:
				tgt_system_locks = tgt_score.find("SystemLocks")
				if tgt_system_locks is None:
					tgt_system_locks = deepcopy(src_system_locks)
					tgt_score.append(tgt_system_locks)
				else:
					for system_lock in src_system_locks:
						system_lock_copy = deepcopy(system_lock)
						tgt_system_locks.append(system_lock_copy)
		
		# Copy pictures if requested and target path is provided
		#if copy_pictures and target_path:
		#	self.copy_pictures(source_score, target_path)
		
		return had_duplicates

	def concatenate_measures(self, source_score):
		"""Original method - copy only measures"""
		self.concatenate_score(source_score, copy_frames=False, copy_title_frames=False)

	def concatenate_with_frames(self, source_score, skip_title=True):
		"""Copy frames and measures, with title frame control"""
		self.concatenate_score(source_score, copy_frames=True, copy_title_frames=not skip_title)
			
	def meta_tags(self):
		"""
		Returns a list of MetaTag objects.
		"""
		return MetaTag.from_elements(self.findall('./metaTag'))

	def meta_tag(self, name):
		"""
		Returns a list of MetaTag objects.
		"""
		node = self.find(f'./metaTag[@name="{name}"]')
		return None if node is None else MetaTag(node)

	def sound_fonts(self):
		return list(set( el.text for el in self.findall('.//Synthesizer/Fluid/val') ))

	def __str__(self):
		return f'<Score "{self.filename}">'

class Part(SmartNode):

	def __init__(self, element, parent):
		super().__init__(element, parent)
		self._instrument = Instrument.from_element(self.find('./Instrument'), self)

	def instrument(self):
		return self._instrument

	def replace_instrument(self, instrument):
		if not isinstance(instrument, Instrument):
			raise ValueError('Can only copy Instrument')
		new_instrument_node = deepcopy(instrument.element)
		old_instrument_node = self.find('Instrument')
		self.element.remove(old_instrument_node)
		self.element.append(new_instrument_node)

	def copy_clef(self, source_part):
		"""
		Copy the staff definition from the given source_part to this Part.
		"""
		for source_staff, target_staff in zip(source_part.staffs(), self.staffs()):
			for node_name in ['defaultClef', 'defaultConcertClef', 'defaultTransposingClef']:
				source_node = source_staff.child(node_name, False)
				if not source_node is None:
					target_node = target_staff.child(node_name, True)
					target_node.text = source_node.text

	def staffs(self):
		return Staff.from_elements(self.findall('Staff'), self)

	def staff(self, id):
		for staff in self.staffs():
			if staff.id == id:
				return staff
		raise IndexError

	def channel_switches_used(self):
		"""
		Returns a set of (str) StaffText/channelSwitch values
		"""
		sets = [ staff.channel_switches_used() for staff in self.staffs() ]
		return reduce(or_, sets, set())

	@property
	def name(self):
		return self.element_text('trackName')

	def __str__(self):
		return f'<Part "{self.name}">'


class Instrument(SmartNode):

	def __init__(self, element, parent):
		super().__init__(element, parent)
		self._init_channels()

	def _init_channels(self):
		self._channels = { chan.name:chan \
			for chan in Channel.from_elements(self.findall('./Channel'), self) }

	def channels(self):
		"""
		Returns list of Channel objects.
		"""
		return self._channels.values()

	def channel(self, name):
		"""
		Returns list of Channel objects.
		"""
		return self._channels[name]

	def channel_names(self):
		"""
		Returns all channels' name, including duplicates, if any.
		"""
		return [ channel.name for channel in self.channels() ]

	def duplicate_channel_names(self):
		a = self.channel_names()
		return [ name for name in set(a) if a.count(name) > 1]

	def has_duplicate_channel_names(self):
		return len(self.duplicate_channel_names()) > 0

	def dedupe_channels(self):
		unique_channel_names = set(self.channel_names())
		channels = self.channels()
		for channel in channels:
			if channel.name in unique_channel_names:
				unique_channel_names.remove(channel.name)
			else:
				self.element.remove(channel.element)
		self._init_channels()

	@property
	def name(self):
		return self.long_name or self.track_name

	@property
	def long_name(self):
		return self.element_text('longName')

	@property
	def track_name(self):
		return self.element_text('trackName')

	@property
	def short_name(self):
		return self.element_text('shortName')

	@property
	def musicxml_id(self):
		return self.element_text('instrumentId')

	def clear_synth(self):
		for channel in self.findall('Channel'):
			for node in channel.findall('controller'):
				channel.remove(node)
			for node in channel.findall('program'):
				channel.remove(node)
			for node in channel.findall('synti'):
				channel.remove(node)

	def remove_channel(self, name):
		node = self.find(f'Channel[@name="{name}"]')
		if node:
			self.element.remove(node)
		self._init_channels()

	def add_channel(self, name):
		"""
		Returns Channel
		"""
		if self.find(f'Channel[@name="{name}"]'):
			raise RuntimeError(f'Channel "{name}" already exists')
		new_channel_node = et.SubElement(self.element, 'Channel')
		new_channel_node.set('name', name)
		self._init_channels()
		return self.channel(name)

	def __str__(self):
		return f'<Instrument "{self.name}">'


class Channel(SmartNode):

	def program(self):
		el = self.find('program')
		return None if el is None else int(el.attrib['value'])

	def bank_msb(self):
		return self.controller_value(CC_BANK_MSB, int)

	def bank_lsb(self):
		return self.controller_value(CC_BANK_LSB, int)

	def controller_value(self, ccid, type_ = None):
		el = self.find(f'controller[@ctrl="{ccid}"]')
		return None if el is None \
			else el.attrib['value'] if type_ is None \
			else type_(el.attrib['value'])

	def set_controller_value(self, ccid, value):
		if not 0 <= int(value) <= 127:
			raise ValueError('Invalid CC value')
		el = self.find(f'controller[@ctrl="{ccid}"]')
		if el is None:
			el = et.SubElement(self.element, 'controller')
			el.set('ctrl', str(ccid))
		el.set('value', value)

	def idstring(self):
		return '%02d:%02d:%02d' % (
			self.bank_msb() or -1,
			self.bank_lsb() or -1,
			self.program() or -1
		)

	@property
	def name(self):
		return self.attribute_value('name', 'normal')

	@property
	def instrument_name(self):
		return self.parent.name

	@property
	def voice_name(self):
		return VoiceName(self.instrument_name, self.name)

	@property
	def midi_port(self):
		"""
		Always returns the public (1-based) channel number.
		"""
		text = self.element_text('midiPort')
		return None if text is None else int(text) + 1

	@midi_port.setter
	def midi_port(self, value):
		"""
		"value" must be the public (1-based) channel number.
		The actual node value is set to one less.
		"""
		value = int(value)
		if value < 1:
			raise ValueError('Channel midi_port must be greater than 0')
		node = self.find('midiPort')
		if node is None:
			node = et.SubElement(self.element, 'midiPort')
		node.text = str(value - 1)

	@property
	def midi_channel(self):
		"""
		Always returns the public (1-based) channel number.
		"""
		text = self.element_text('midiChannel')
		return None if text is None else int(text) + 1

	@midi_channel.setter
	def midi_channel(self, value):
		"""
		"value" must be the public (1-based) channel number.
		The actual node value is set to one less.
		"""
		value = int(value)
		if not 1 <= value <= 16:
			raise ValueError('Channel midi_channel must be betwen 1 and 16, inclusive')
		node = self.find('midiChannel')
		if node is None:
			node = et.SubElement(self.element, 'midiChannel')
		node.text = str(value - 1)

	@property
	def volume(self):
		return self.controller_value(CC_VOLUME, int)

	@volume.setter
	def volume(self, value):
		self.set_controller_value(CC_VOLUME, str(value))

	@property
	def balance(self):
		return self.controller_value(CC_BALANCE, int)

	@balance.setter
	def balance(self, value):
		self.set_controller_value(CC_BALANCE, str(value))

	@property
	def pan(self):
		return self.controller_value(CC_PAN, int)

	@pan.setter
	def pan(self, value):
		self.set_controller_value(CC_PAN, str(value))

	def __str__(self):
		return f'<Channel "{self.voice_name}">'


class Staff(SmartNode):

	def measures(self):
		score = self.parent.parent
		return Measure.from_elements(score.findall(f'./Staff[@id="{self.id}"]/Measure'))

	def is_empty(self):
		return all(measure.is_empty() for measure in self.measures())

	@property
	def length(self):
		return len(self.measures())

	def empty(self):
		"""
		Removes all but the first measure, and removes all chords and rests within it.
		"""
		score = self.parent.parent
		staff_node = score.find(f'./Staff[@id="{self.id}"]')
		measure_nodes = staff_node.findall(f'./Measure')
		for node in measure_nodes[1:]:
			staff_node.remove(node)
		for node in measure_nodes[0].getchildren():
			measure_nodes[0].remove(node)
		voice_node = et.SubElement(measure_nodes[0], 'voice')
		rest_node = et.SubElement(voice_node, 'Rest')
		node = et.SubElement(rest_node, 'durationType')
		node.text = 'measure'
		node = et.SubElement(rest_node, 'duration')
		node.text = '4/4'

	def channel_switches_used(self):
		"""
		Returns a set of (str) StaffText/channelSwitch values
		"""
		sets = [ measure.channel_switches() for measure in self.measures() ]
		return reduce(or_, sets, set())

	def part(self):
		return self.parent

	@property
	def color(self):
		"""
		Returns a dictionary of RBG values.
		"""
		node = self.child('color', False)
		return None if node is None else {
			'r' : node.attrib['r'],
			'g' : node.attrib['g'],
			'b' : node.attrib['b'],
			'a' : node.attrib['a']
		}

	@color.setter
	def color(self, rgba_dict):
		"""
		Set the color of this Staff.
		rgba_dict must be a dict containing "r", "g", "b" and "a" keys, having integer
		values in the range 0 - 255.
		"""
		node = self.child('color')
		node.set('r', str(rgba_dict['r']))
		node.set('g', str(rgba_dict['g']))
		node.set('b', str(rgba_dict['b']))
		node.set('a', str(rgba_dict['a']))

	@property
	def id(self):
		return self.attribute_value('id')

	@property
	def type(self):
		type_node = self.find('./StaffType')
		try:
			return f'{type_node.attrib["group"]} {self.element_text("./StaffType/name")}'
		except Exception:
			return ''

	@property
	def clef(self):
		return self.element_text('./defaultClef', self.element_text('./defaultConcertClef', 'G'))

	def __str__(self):
		return f'<Staff "{self.id}">'


class Measure(SmartNode):

	def is_empty(self):
		return len(self.find_all('.//Note')) == 0

	def channel_switches(self):
		"""
		Returns a set of (str) StaffText/channelSwitch values
		"""
		nodes = self.findall('./voice/StaffText/channelSwitch')
		return set() if nodes is None else { node.attrib['name'] for node in nodes }

class MetaTag(SmartNode):

	@property
	def name(self):
		return self.attribute_value('name')

	@property
	def value(self):
		return self.element.text

	@value.setter
	def value(self, value):
		self.element.text = str(value)

	def __str__(self):
		return f'{self.name}: {self.value}'


#  end mscore/__init__.py
