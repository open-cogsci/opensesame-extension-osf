# -*- coding: utf-8 -*-
"""
@author: Daniel Schreij

This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

This module is distributed under the Apache v2.0 License.
You should have received a copy of the Apache v2.0 License
along with this module. If not, see <http://www.apache.org/licenses/>.
"""
# Python3 compatibility
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from qtpy import QtWidgets, QtCore, QtGui, QtNetwork

from libqtopensesame.extensions import base_extension
from libqtopensesame.misc.translate import translation_context
from libopensesame.py3compat import *
import json
import warnings

_ = translation_context(u'OpenScienceFramework', category=u'extension')

__author__ = u"Daniel Schreij"
__license__ = u"Apache2"

from openscienceframework import widgets, events, manager
from openscienceframework import connection as osf
import os
# For md5 and sha comparisons
import hashlib
# For easier python time handling
import arrow
# For human readable file sizes
import humanize
# File copying
import shutil

def hashfile(path, hasher, blocksize=65536):
	""" Creates a hash for the supplied file
	
	Parameters
	----------
	path : str
		Path to the file to hash
	hasher : hashlib.HASH
		Hashing object, such as returned by hashlib.md5() or hashlib.sha256()
	blocksize : int (default: 65536)
		The buffersize to read the file with
	
	Returns:
	str : the hasher.hexdigest() contents
	"""
	with open(os.path.abspath(path), 'rb') as afile:
		buf = afile.read(blocksize)
		while len(buf) > 0:
			hasher.update(buf)
			buf = afile.read(blocksize)
	return hasher.hexdigest()

class Notifier(QtCore.QObject):
	""" Sends on messages to the notifier extension or shows a dialog box if
	it is not available """

	def __init__(self, extension_manager):
		""" Constructor 
		
		Parameters
		----------
		extension_manager : OpenSesame exension manager
			The object that fires internal OpenSesame events.
		"""

		super(Notifier,self).__init__()
		self.extension_manager = extension_manager

	@QtCore.pyqtSlot('QString', 'QString')
	def error(self, title, message):
		""" Show an error message in a red notification ribbon

		Parameters
		----------
		title : str
			The title of the box
		message : str
			The message to display
		"""
		self.extension_manager.fire('notify', message=message, category='danger',
			always_show=True, timeout=None)

	@QtCore.pyqtSlot('QString', 'QString')
	def warning(self, title, message):
		""" Show a warning message in an orange notification ribbon

		Parameters
		----------
		title : str
			The title of the box
		message : str
			The message to display
		"""
		self.extension_manager.fire('notify', message=message, category='warning',
			always_show=True)

	@QtCore.pyqtSlot('QString', 'QString')
	def info(self, title, message):
		""" Show an information message in a blue notification ribbon

		Parameters
		----------
		title : str
			The title of the box
		message : str
			The message to display
		"""
		self.extension_manager.fire('notify', message=message, category='info',
			always_show=True)

	@QtCore.pyqtSlot('QString', 'QString')
	def success(self, title, message):
		""" Show a success message in a green notification ribbon

		Parameters
		----------
		title : str
			The title of the box
		message : str
			The message to display
		"""
		self.extension_manager.fire('notify', message=message, category='success',
			always_show=True)


	@QtCore.pyqtSlot('QString', 'QString')
	def primary(self, title, message):
		""" Show a success message in a 'primary' class notification ribbon

		Parameters
		----------
		title : str
			The title of the box
		message : str
			The message to display
		"""
		self.extension_manager.fire('notify', message=message, category='primary',
			always_show=True)

class VersionChoiceDialog(QtWidgets.QDialog):
	USE_LOCAL = 2
	USE_REMOTE = 3

	def __init__(self, *args, **kwargs):
		try:
			self.local_version_info = kwargs.pop('local_version_info')
		except KeyError:
			raise TypeError(u"Missing local_version_info dicationary argument")

		try:
			self.remote_version_info = kwargs.pop('remote_version_info')
		except KeyError:
			raise TypeError(u"Missing remote_version_info dicationary argument")

		super(VersionChoiceDialog, self).__init__(*args, **kwargs)
		self.__setup_ui()

	def __setup_ui(self):
		self.setLayout(QtWidgets.QVBoxLayout())
		# Message label
		message_layout = QtWidgets.QHBoxLayout()
		message_pixmap = QtWidgets.QLabel()
		message_pixmap.setAlignment(QtCore.Qt.AlignTop)
		message_pixmap.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
			QtWidgets.QSizePolicy.Minimum)
		message_label_icon = QtGui.QIcon.fromTheme('dialog-warning')
		message_pixmap.setPixmap(message_label_icon.pixmap(50,50))

		message_label = QtWidgets.QLabel()
		message_label.setText(
			_(u"This experiment is linked to the Open Science Framework. However, "
				"the version on your computer differs from the one stored at the "
				" Open Science Framework.\nWhich one would you like to use?"))
		message_label.setWordWrap(True)
		message_layout.addWidget(message_pixmap)
		message_layout.addWidget(message_label)

		self.layout().addLayout(message_layout)
		# Side by side view of the files
		side_by_side = QtWidgets.QGridLayout()

		# Get the OpenSesame icon to show for both local and remote versions
		os_image = QtGui.QIcon.fromTheme('opera-widget-manager').pixmap(50, 50)
		# Widget can only be assigned once to layout (so two need to be created
		# even if they are identical by appearance)
		os_local_img = QtWidgets.QLabel()
		os_local_img.setPixmap(os_image)
		os_local_img.setAlignment(QtCore.Qt.AlignCenter)
		os_remote_img = QtWidgets.QLabel()
		os_remote_img.setPixmap(os_image)
		os_remote_img.setAlignment(QtCore.Qt.AlignCenter)

		### Local file data
		local_form_layout = QtWidgets.QFormLayout()
		# Local header
		local_title_label = QtWidgets.QLabel(_(u"<b>On this computer<b/>"))
		local_title_label.setAlignment(QtCore.Qt.AlignCenter)
		# Add some stats about the file
		local_form_layout.addRow(local_title_label)
		local_form_layout.addRow(os_local_img)
		local_form_layout.addRow(_(u"Name:"), 
			QtWidgets.QLabel(self.local_version_info['name'])),
		
		# If filesize is given as int, humanize it to comprehensible notations
		if type(self.local_version_info['filesize']) in [int]: #, long]: (no longer exists?)
			self.local_version_info['filesize'] = humanize.naturalsize(
				self.local_version_info['filesize'])
		local_form_layout.addRow(_(u"Size:"), 
			QtWidgets.QLabel(self.local_version_info['filesize']))
		# Convert to arrow object for easier date/time handling (does nothing
		# if already an arrow object)
		local_last_modified = arrow.get(self.local_version_info['modified'])
		local_form_layout.addRow(_(u"Last modified:"), 
			QtWidgets.QLabel("{} ({})".format(
				local_last_modified.format('YYYY-MM-DD HH:mm'),
				local_last_modified.humanize()
			))
		)

		### Remote file data
		remote_form_layout = QtWidgets.QFormLayout()
		remote_title_label = QtWidgets.QLabel(_(u"<b>On the Open Science Framework</b>"))
		remote_title_label.setAlignment(QtCore.Qt.AlignCenter)
		remote_form_layout.addRow(remote_title_label)
		remote_form_layout.addRow(os_remote_img)
		remote_form_layout.addRow(_(u"Name:"), 
			QtWidgets.QLabel(self.remote_version_info['name']))
		
		# If filesize is given as int, humanize it to comprehensible notations
		if type(self.remote_version_info['filesize']) in [int]: # , long]:
			self.remote_version_info['filesize'] = humanize.naturalsize(
				self.remote_version_info['filesize'])
		remote_form_layout.addRow(_(u"Size:"), 
			QtWidgets.QLabel(self.remote_version_info['filesize']))
		
		# Convert to arrow object for easier date/time handling (does nothing
		# if already an arrow object)
		remote_last_modified = arrow.get(self.remote_version_info['modified'])
		remote_form_layout.addRow(_(u"Last modified:"), 
			QtWidgets.QLabel("{} ({})".format(
				remote_last_modified.format('YYYY-MM-DD HH:mm'),
				remote_last_modified.humanize()
			))
		)

		# Buttons
		self.button_use_local = QtWidgets.QPushButton(_(u"Use version on this computer"))
		self.button_use_local.clicked.connect(lambda: self.done(self.USE_LOCAL))
		self.button_use_remote = QtWidgets.QPushButton(_(u"Use version from the OSF"))
		self.button_use_remote.clicked.connect(lambda: self.done(self.USE_REMOTE))

		# Connect layouts
		local_form_layout.addRow(self.button_use_local)
		remote_form_layout.addRow(self.button_use_remote)
		side_by_side.addLayout(local_form_layout,1,1)
		side_by_side.addLayout(remote_form_layout,1,2)
		self.layout().addLayout(side_by_side)

		# Set fixed size, allow a bit more breathing space in vertical dimension
		minimum_size = self.minimumSizeHint()
		self.setFixedSize(minimum_size.width(),minimum_size.height()+20)

class OpenScienceFramework(base_extension):
	### public functions
	def set_linked_experiment(self, osf_node):
		""" Displays the information of experiment on OSF to which the opened
		experiment is linked and enables the unlink button.

		Parameters
		----------
		osf_node : str or None
			uri to location of experiment on OSF. 
			None resets the displays and unlinks experiment
		"""
		if osf_node is None:
			self.linked_experiment_value.setText(_(u"Not linked"))
			self.button_unlink_experiment.setDisabled(True)
			self.widget_autosave_experiment.setDisabled(True)
			self.checkbox_autosave_experiment.setCheckState(QtCore.Qt.Unchecked)
		else:
			self.linked_experiment_value.setText(osf_node)
			self.button_unlink_experiment.setDisabled(False)
			self.widget_autosave_experiment.setDisabled(False)

	def set_linked_experiment_datanode(self, osf_node):
		""" Displays the information of the folder on OSF to which the data of
		this experiment is to be saved.

		Parameters
		----------
		data : str
			uri to data folder on OSF
			None resets the displays and unlinks datanode
		"""
		if osf_node is None:
			self.linked_data_value.setText(_(u"Not linked"))
			self.button_unlink_data.setDisabled(True)
			self.widget_autosave_data.setDisabled(True)
			self.checkbox_autosave_data.setCheckState(QtCore.Qt.Unchecked)
		else:
			self.linked_data_value.setText(osf_node)
			self.button_unlink_data.setDisabled(False)
			self.widget_autosave_data.setDisabled(False)

	def verify_linked_experiment_status(self):
		""" Check if linked node of the experiment is still valid, and if the always
		upload checkbox should be checked or not, depending on the value of the 
		variable that tracks this in the variable registry """

		if self.experiment.var.has('osf_id') and self.experiment.var.osf_id:
			# Check if the supplied osf_id is a valid one:
			osf_url = osf.api_call('file_info', self.experiment.var.osf_id)

			# Update linked data
			self.set_linked_experiment(osf_url)
			# Check if 'always upload experiment' should (still) be checked
			if self.experiment.var.has('osf_always_upload_experiment') and \
				self.experiment.var.osf_always_upload_experiment == 'yes':
				self.checkbox_autosave_experiment.setCheckState(QtCore.Qt.Checked)
			else:
				self.checkbox_autosave_experiment.setCheckState(QtCore.Qt.Unchecked)

			# If osf_id is nonexistent, the manager.get function will display an
			# error on its own, so just simply pass a lambda function for the
			# callback (we don't need to do anything with that data.)
			self.manager.get(
				osf_url, 
				lambda x: None
			)
		else:
			# If the osf_id variable is gone, they link to OSF is severed. This
			# should be updated in the GUI
			self.set_linked_experiment(None)

	def verify_linked_experiment_data_status(self):
		""" Check if linked node for data upload is still valid, and if the always 
		upload checkbox should be checked or not, depending on the value of the 
		variable that tracks this in the variable registry """

		if self.experiment.var.has('osf_datanode_id') and \
			self.experiment.var.osf_datanode_id:

			node_id = self.experiment.var.osf_datanode_id
			osf_url = self.get_osf_node_url(node_id)

			# Update linked data
			self.set_linked_experiment_datanode(osf_url)
			# Check if 'always upload experiment' should (still) be checked
			if self.experiment.var.has('osf_always_upload_data') and \
				self.experiment.var.osf_always_upload_data == 'yes':
				self.checkbox_autosave_data.setCheckState(QtCore.Qt.Checked)
			else:
				self.checkbox_autosave_data.setCheckState(QtCore.Qt.Unchecked)

			# If osf_id is nonexistent, the manager.get function will display an
			# error on its own, so just simply pass a lambda function for the
			# callback (we don't need to do anything with that data.)
			self.manager.get(
				osf_url, 
				lambda x: None
			)
		else:
			self.set_linked_experiment_datanode(None)

	def get_osf_node_url(self, node_id):
		""" Determine the correct url for a folder node. These differ somewhat
		for a top-level repository url (i.e. the root of the repository) or a
		subfolder of a repository
	
		Parameters
		----------
		node_id : str
			The id of the node. Either is a base64 string for a file or a subfolder 
			in a repository, or a <project_id:repo_name> pair for a top-level (root)
			repository node

		Returns
		-------
		str : The uri to the API endpoint of the node
		"""
		# If there is a colon inside the datanode_id, then we are looking at
		# a reference to a top-level repository node
		if ':' in node_id:
			project_id, repo = node_id.split(':')
			return osf.api_call('repo_files', project_id, repo)
		# If not, it is a normal osf id for a file or folder
		else:
			return osf.api_call('file_info', node_id)

	def compare_versions(self, data):
		""" Check if currently opened experiment and the one linked on the OSF are
		still in sync. Offer use the choice which file to use.
			
		Parameters
		----------
		data : dict or QtNetwork.QNetworkReply
			The data of the remote file. If function is a callback for a HTTP
			request function, this parameter can be a QNetworkReply object, which
			is converted to the corresponding dict
		"""
		# If a QNetworkReply is passed, convert its data to a dict
		if isinstance(data, QtNetwork.QNetworkReply):
			data = json.loads(safe_decode(data.readAll().data()))

		# Check validity of the currently opened file
		local_file = self.main_window.current_path
		if local_file and not os.path.isfile(local_file):
			warnings.warn('No valid file specified')
			return
		
		# Get remote sha256 hash from OSF
		try:
			remote_hash = data['data']['attributes']['extra']['hashes']['sha256']
		except KeyError as e:
			raise osf.OSFInvalidResponse("Unable to retrieve remote hash for "
				" experiment: {}".format(e))

		# Create a sha256 hash for the currently opened experiment
		local_hash = hashfile(local_file, hashlib.sha256())

		# Sync check is being done now, so set this flag to False before the first
		# return is encountered.
		self.sync_check_required = False

		# If hashes are the same, then remote and local versions are the same
		if remote_hash == local_hash:
			self.notifier.info(_(u"In sync"), _(u"Experiment is synchronized with "
				"the Open Science Framework"))
			return
			
		# If not, do some extra digging and provide the user with a choice of which
		# version to keep
		
		# Get remote file information
		try:
			remote_name = data['data']['attributes']['name']
			remote_size = data['data']['attributes']['size']
			remote_modified = data['data']['attributes']['date_modified']
		except KeyError as e:
			raise osf.OSFInvalidResponse("Unable to retrieve remote file info of"
				" experiment: {}".format(e))
		# Create an arrow time object converted to the local timezone
		remote_modified = arrow.get(remote_modified).to('local')

		# Get local file info
		# name
		local_name = os.path.basename(local_file)
		# size
		local_size = os.path.getsize(local_file)
		# last modified time
		local_modified = arrow.get(os.path.getmtime(local_file)).to('local')
		
		local_info = {
			'name': local_name,
			'modified': local_modified,
			'filesize': local_size
		}

		remote_info = {
			'name': remote_name,
			'modified': remote_modified,
			'filesize': remote_size
		}

		# Show a dialog for the choice
		choice_dialog = VersionChoiceDialog(
			self.main_window,
			QtCore.Qt.FramelessWindowHint,
			local_version_info=local_info,
			remote_version_info=remote_info,
		)

		choice = 0
		while not choice:
			choice = choice_dialog.exec_()
		
		# If use closes dialog with close button, 0 will be returned...
		if choice == choice_dialog.USE_LOCAL:
			# If local version should be used, then we're done here
			return
		
		# A weird loop, but the user should not be allowed to choose Yes to the
		# the backup question and not save the file (by pressing cancel for instance)
		while True:
			reply = QtWidgets.QMessageBox.question(
				self.main_window,
				_(u"Create backup of local file"),
				_(u"Do you want to save a backup of the experiment on this computer"
					" using a different filename?"),
				QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
			)
			if reply == QtWidgets.QMessageBox.No:
				break
			if reply == QtWidgets.QMessageBox.Yes:
				destination = QtWidgets.QFileDialog.getSaveFileName(
					self.main_window,
					_("Backup experiment to"),
					self.main_window.current_path,
				)
				# PyQt5 returns a tuple, because it actually performs the function of
				# PyQt4's getSaveFileNameAndFilter() function
				if isinstance(destination, tuple):
					destination = destination[0]
				# Ask user again if he or she wants to make a backup
				if not destination:
					continue
				# Copy the current experiment to the new path
				shutil.copy(self.main_window.current_path, destination)
				break

		# Download the version from the OSF and open it. Show a progress dialog
		# if the file is large and will take a while to download.
		# Some file providers do not report the size. Check for that here
		if data['data']['attributes']['size']:
			# Configure progress dialog
			download_progress_dialog = QtWidgets.QProgressDialog()
			download_progress_dialog.hide()
			download_progress_dialog.setLabelText(_("Downloading") + " " + \
				data['data']['attributes']['name'])
			download_progress_dialog.setMinimum(0)
			download_progress_dialog.setMaximum(data['data']['attributes']['size'])
			progress_cb = self.project_explorer._transfer_progress
		else:
			download_progress_dialog = None
			progress_cb = None
		
		# Download the file to open it later
		self.manager.download_file(
			data['data']['links']['download'],
			self.main_window.current_path,
			downloadProgress=progress_cb,
			progressDialog=download_progress_dialog,
			finishedCallback=self.__experiment_downloaded,
			osf_data=data['data']
		)

	### OpenSesame events
	def event_startup(self):
		""" OpenSesame event on startup of the program. Initialize the extension"""
		self.__initialize()
	
	def activate(self):
		""" Show OSF Explorer. Also check if linked data is still legit. 
		Users have access to it through the variable registry object, so it is 
		possible they have unknowingly tampered with it. """

		self.verify_linked_experiment_status()
		self.verify_linked_experiment_data_status()
		self.__show_explorer_tab()	
	
	def event_save_experiment(self, path):
		""" See if experiment needs to be synced to OSF and do so if necessary"""
		# First check if OSF id has been set
		if not self.experiment.var.has('osf_id') or not self.manager.logged_in_user:
			return

		# If the autosave checkbox is not checked, ask the user for permission
		# to upload the experiment to OSF
		if not self.experiment.var.has('osf_always_upload_experiment') or \
			self.experiment.var.osf_always_upload_experiment != 'yes':
			reply = QtWidgets.QMessageBox.question(
				None,
				_(u"Upload experiment to OSF"),
				_(u"Would you also like to update the version of this experiment"
					" on the Open Science Framework?"),
				QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes
			)
			if reply == QtWidgets.QMessageBox.No:
				return

		osf_id = self.experiment.var.osf_id

		# First we need to retrieve the experiment details to determine the upload
		# link. The real file uploading will thus be done in the callback function
		self.manager.get_file_info(osf_id, self.__prepare_experiment_sync)

	def event_open_experiment(self, path):
		""" Check if opened experiment is linked to the OSF and set parameters
		accordingly """
		# Only take action if user is logged in
		if self.manager.logged_in_user:
			# Check if exp is linked to OSF. 
			# If so, display this information in the OSF explorer.
			if self.experiment.var.has('osf_id'):
				self.manager.get_file_info(self.experiment.osf_id,
					self.__process_file_info)
			else:
				# Reset GUI if no osf_id is present
				self.set_linked_experiment(None)

			# Check if a node to upload data to has been linked for this experiment
			# If so, display this information in the OSF explorer.
			if self.experiment.var.has('osf_datanode_id'):
				self.manager.get_file_info(self.experiment.osf_datanode_id,
					self.__process_datafolder_info)
			else:
				# Reset GUI if this data is not present
				self.set_linked_experiment_datanode(None)
			# Refresh contents of the tree so linked items will be marked.
			if not self.project_tree.isRefreshing:
				self.project_tree.refresh_contents()
		# If user is not logged in, issue a warning on opening that a linkt to
		# the OSF has been detected, but no syncing can occur as long is the user
		# is not logged in.
		elif self.experiment.var.has('osf_id') or \
			self.experiment.var.has('osf_datanode_id'):
			self.notifier.info(_(u'OSF link detected'),
				_(u'This experiment is linked to the Open Science Framework. '
					'Please login if you want to use the synchronization functionalities'))
			self.sync_check_required = True

	def event_process_data_files(self, data_files):
		""" See if datafiles need to be saved to OSF """
		# Check if data link has been set, and if a user is logged in.
		
		if not self.experiment.var.has('osf_datanode_id') or \
			not self.experiment.var.osf_datanode_id or \
			not self.manager.logged_in_user:
			return
	
		# If the autosave checkbox is not checked, ask the user for permission
		# to upload the data to OSF
		if not self.experiment.var.has('osf_always_upload_data') or \
			self.experiment.var.osf_always_upload_data != 'yes':
			reply = QtWidgets.QMessageBox.question(
				None,
				_(u"Upload data to OSF"),
				_(u"Would you like to upload the data files to your linked"
					" folder on the Open Science Framework?"),
				QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes
			)
			if reply == QtWidgets.QMessageBox.No:
				return

		node_id = self.experiment.var.osf_datanode_id

		# If there is a colon inside the datanode_id, then we are looking at
		# a reference to a top-level repository node
		if ':' in node_id:
			project_id, repo = node_id.split(':')
			osf_url = osf.api_call('project_repos', project_id)
		# If not, it is a normal osf id for a file or folder
		else:
			osf_url = osf.api_call('file_info', node_id)
		# Get the correct upload URL
		self.manager.get(osf_url, self.__prepare_experiment_data_sync_get_upload_url,
			data_files=data_files, node_id=node_id)

	### Other internal events
	def handle_login(self):
		""" Event fired upon login to OSF """
		if self.sync_check_required and self.experiment.var.has('osf_id'):
			self.manager.get_file_info(self.experiment.osf_id,
				self.__process_file_info)

	def handle_logout(self):
		""" Event fired upon logout from the OSF """
		pass

	### Private functions
		
	def __initialize(self):
		""" Intialization of the extension """
		tokenfile = os.path.abspath("token.json")
		
		# Initialize notifier
		self.notifier = Notifier(self.extension_manager)

		# Create manager object
		self.manager = manager.ConnectionManager(tokenfile, self.notifier)

		# Init and set up user badge
		icon_size = self.toolbar.iconSize()
		self.user_badge = widgets.UserBadge(self.manager, icon_size)
		firstAction = self.user_badge.logged_in_menu.actions()[0]
		show_explorer = QtWidgets.QAction(_(u"Show explorer"), 
			self.user_badge.logged_in_menu)
		show_explorer.triggered.connect(self.activate)
		self.user_badge.logged_in_menu.insertAction(firstAction, show_explorer)

		# Set-up project tree
		self.project_tree = widgets.ProjectTree(self.manager)
		# Change button availability depending on currently selected item.
		self.project_tree.currentItemChanged.connect(self.__set_button_availabilty)
		# Mark the items in the tree that are linked to this experiment
		self.project_tree.refreshFinished.connect(self.__mark_linked_nodes)
		# Add extra column for remarks
		self.project_tree.setColumnCount(self.project_tree.columnCount()+1)
		header = self.project_tree.headerItem()
		header.setText(self.project_tree.columnCount()-1,_(u'Remarks'))

		# Inject OpenSesame items into the OSF Explorers context menu

		# Save osf_icon for later usage
		self.osf_icon = self.project_tree.get_icon('folder', 'osfstorage')

		# Init and set up Project explorer
		# Pass it the project tree instance from
		self.project_explorer = widgets.OSFExplorer(
			self.manager, tree_widget=self.project_tree
		)

		# Set up the link and save to OSF buttons
		self.__setup_buttons(self.project_explorer)

		# Add a widget to the project explorer with info about link to OSF states
		self.__add_info_linked_widget(self.project_explorer)

		# Override the trees contextMenuEvent (again) and handle it here
		self.project_tree.contextMenuEvent = self.__show_tree_context_menu

		# Token file listener writes the token to a json file if it receives
		# a logged_in event and removes this file after logout
		self.tfl = events.TokenFileListener(tokenfile)

		# Add items as listeners to the event Notifier
		self.manager.dispatcher.add_listeners(
			[
				self, self.manager, self.tfl, self.user_badge, 
				self.project_explorer, self.project_tree
			]
		)
		# Connect click on user badge log in/out button to osf log in/out actions
		self.user_badge.logout_request.connect(self.manager.logout)
		self.user_badge.login_request.connect(self.manager.login)

		# Show the user badge
		self.toolbar.addWidget(self.user_badge)

		# Button mode feature no longer used, so the line below could be removed
		# (but do check if that breaks anything)
		self.current_mode = u"full"

		# Initialize linked tree widget items
		self.linked_experiment_treewidgetitem = None
		self.linked_datanode_treewidgetitem = None

		# Set to true, when an experiment is linked to the OSF, but no user is 
		# currently logged in to the OSF. Upon login, the local file version is 
		# checked against the linked on on the OSF to see if they are still synced.
		self.sync_check_required = False

	def __show_tree_context_menu(self, e):
		item = self.project_tree.itemAt(e.pos())
		if item is None:
			return

		context_menu = self.project_explorer.create_context_menu(item)
		if not context_menu is None:
			context_menu = self.__inject_context_menu_items(item, context_menu)
			context_menu.popup(e.globalPos())

	def __inject_context_menu_items(self, item, context_menu):
		data = item.data(0,QtCore.Qt.UserRole)
		kind = data["attributes"]["kind"]
		
		firstAction = context_menu.actions()[0]
		if kind == 'folder':
			# Sync experiment entry
			sync_experiment = QtWidgets.QAction(QtGui.QIcon.fromTheme('insert-link'),
				_(u"Sync experiment to this folder"), 
				context_menu)
			sync_experiment.triggered.connect(self.__link_experiment_to_osf)
			context_menu.insertAction(firstAction, sync_experiment)
			# Sync data entry
			sync_data = QtWidgets.QAction(QtGui.QIcon.fromTheme('insert-link'),
				_(u"Sync data to this folder"), 
				context_menu)
			sync_data.triggered.connect(self.__link_data_to_osf)
			context_menu.insertAction(firstAction, sync_data)
			context_menu.insertSeparator(firstAction)
		elif kind == "file":
			name = data["attributes"]["name"]
			if widgets.check_if_opensesame_file(name, True):
				open_experiment = QtWidgets.QAction(QtGui.QIcon.fromTheme('document-open'),
					_(u"Open experiment"), context_menu)
				open_experiment.triggered.connect(self.__open_osf_experiment)
				context_menu.insertAction(firstAction, open_experiment)
				context_menu.insertSeparator(firstAction)
		return context_menu

	def __setup_buttons(self, explorer):
		""" Set up the extra buttons which the extension adds to the standard
		OSF explorer's """
		## Link to OpenSesame buttons

		# Link experiment to folder
		self.button_link_exp_to_osf = QtWidgets.QPushButton(_(u'Link experiment'))
		self.button_link_exp_to_osf.setIcon(QtGui.QIcon.fromTheme('gcolor2'))
		self.button_link_exp_to_osf.clicked.connect(self.__link_experiment_to_osf)
		self.button_link_exp_to_osf.setDisabled(True)

		# Link data folder
		self.button_link_data_to_osf = QtWidgets.QPushButton(_(u'Link data'))
		self.button_link_data_to_osf.setIcon(QtGui.QIcon.fromTheme('mail-inbox'))
		self.button_link_data_to_osf.clicked.connect(self.__link_data_to_osf)
		self.button_link_data_to_osf.setDisabled(True)
		
		## Unlink buttons

		# Unlink experiment button
		self.button_unlink_experiment = QtWidgets.QPushButton(_(u'Unlink'))
		self.button_unlink_experiment.clicked.connect(self.__unlink_experiment)
		self.button_unlink_experiment.setDisabled(True)

		# Unlink data button
		self.button_unlink_data = QtWidgets.QPushButton(_(u'Unlink'))
		self.button_unlink_data.clicked.connect(self.__unlink_data)
		self.button_unlink_data.setDisabled(True)

		# Open from OSF button
		self.button_open_from_osf = QtWidgets.QPushButton(_(u'Open'))
		self.button_open_from_osf.setIcon(QtGui.QIcon.fromTheme('document-open'))
		self.button_open_from_osf.clicked.connect(self.__open_osf_experiment)
		self.button_open_from_osf.setDisabled(True)

		# Separator line
		line = QtWidgets.QFrame();
		line.setFrameShape(line.VLine);
		line.setFrameShadow(line.Sunken);

		# Add everything to the OSF explorer's buttonbar
		explorer.buttonbar.layout().insertWidget(2, line)
		explorer.buttonbar.layout().insertWidget(2, self.button_open_from_osf)
		explorer.buttonbar.layout().insertWidget(2, self.button_link_exp_to_osf)
		explorer.buttonbar.layout().insertWidget(2, self.button_link_data_to_osf)
		
		# Add buttons to default explorer buttonset
		explorer.buttonsets['default'].append(self.button_open_from_osf)
		explorer.buttonsets['default'].append(self.button_link_exp_to_osf)
		explorer.buttonsets['default'].append(self.button_link_data_to_osf)

		# Remove labels from default buttons
		explorer.refresh_button.setText("")
		explorer.new_folder_button.setText("")
		explorer.delete_button.setText("")
		explorer.upload_button.setText("")
		explorer.download_button.setText("")

	def __add_info_linked_widget(self, explorer):
		# Create widget
		info_widget = QtWidgets.QWidget()

		# Set up layout
		info_layout = QtWidgets.QGridLayout()
		#info_layout.setContentsMargins(15, 11, 15, 40)

		# Set up labels
		linked_experiment_label = QtWidgets.QLabel(_(u"Experiment linked to:"))
		linked_data_label = QtWidgets.QLabel(_(u"Data stored to:"))

		# set up link information
		self.linked_experiment_value = QtWidgets.QLabel(_(u"Not linked"))
		self.linked_experiment_value.setStyleSheet("font-style: italic")
		self.linked_data_value = QtWidgets.QLabel(_(u"Not linked"))
		self.linked_data_value.setStyleSheet("font-style: italic")

		# Widgets for automatically uploading experiment to OSF on save
		self.widget_autosave_experiment =  QtWidgets.QWidget()
		autosave_exp_layout = QtWidgets.QHBoxLayout()
		autosave_exp_layout.setContentsMargins(0, 0, 0, 0)
		self.widget_autosave_experiment.setLayout(autosave_exp_layout)
		autosave_exp_label = QtWidgets.QLabel(_(u"Always upload experiment on save"))
		self.checkbox_autosave_experiment = QtWidgets.QCheckBox()
		self.checkbox_autosave_experiment.setToolTip(_(
			u"If this box is checked OpenSesame will not ask for permission to\n"
			"upload an experiment to the OSF and will always do so after an experiment\n"
			"has been saved."))
		self.checkbox_autosave_experiment.stateChanged.connect(
			self.__handle_check_autosave_experiment)
		autosave_exp_layout.addWidget(self.checkbox_autosave_experiment)
		autosave_exp_layout.addWidget(autosave_exp_label, QtCore.Qt.AlignLeft)
		self.widget_autosave_experiment.setDisabled(True)

		# Widgets for the automatic uploading of experiment data to OSF
		self.widget_autosave_data = QtWidgets.QWidget()
		autosave_data_layout = QtWidgets.QHBoxLayout()
		autosave_data_layout.setContentsMargins(0, 0, 0, 0)
		self.widget_autosave_data.setLayout(autosave_data_layout)
		self.checkbox_autosave_data = QtWidgets.QCheckBox()
		self.checkbox_autosave_data.setToolTip(_(
			u"If this box is checked OpenSesame will not ask for permission to\n"
			"upload collected data to the OSF and will always do so after an experiment\n"
			"has (successfully) finished."))
		self.checkbox_autosave_data.stateChanged.connect(
			self.__handle_check_autosave_data)
		autosave_data_label = QtWidgets.QLabel(_(u"Always upload collected data"))
		autosave_data_layout.addWidget(self.checkbox_autosave_data)
		autosave_data_layout.addWidget(autosave_data_label, QtCore.Qt.AlignLeft)
		self.widget_autosave_data.setDisabled(True)

		# Add labels to layout
		# First row
		info_layout.addWidget(linked_experiment_label, 1, 1, QtCore.Qt.AlignRight)
		info_layout.addWidget(self.linked_experiment_value, 1, 2)
		info_layout.addWidget(self.button_unlink_experiment, 1, 3)
		info_layout.addWidget(self.widget_autosave_experiment, 1, 4)
		# Second row
		info_layout.addWidget(linked_data_label, 2, 1, QtCore.Qt.AlignRight)
		info_layout.addWidget(self.linked_data_value, 2, 2)
		info_layout.addWidget(self.button_unlink_data, 2, 3)
		info_layout.addWidget(self.widget_autosave_data, 2, 4)
		info_widget.setLayout(info_layout)

		info_widget.setContentsMargins(0, 0, 0, 0)
		info_widget.layout().setContentsMargins(0, 0, 0, 0)

		# Make sure the column containing the linked location info takes up the
		# most space
		info_layout.setColumnStretch(2, 1)

		# Make sure the info_widget is vertically as small as possible.
		info_widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, 
			QtWidgets.QSizePolicy.Fixed)
		
		explorer.main_layout.insertWidget(1, info_widget)

	def __process_file_info(self, reply):
		""" Callback for event_open_experiment """
		# Parse the response
		data = json.loads(safe_decode(reply.readAll().data()))
		# Check if structure is valid, and if so, parse experiment's osf path
		# from the data.
		try:
			osf_file_path = data['data']['links']['self']
		except KeyError as e:
			warnings.warn('Invalid OSF response format: {}'.format(e))
			return
		
		self.set_linked_experiment(osf_file_path)
		# See if always upload experiment flag has been set in the experiment
		if self.experiment.var.has('osf_always_upload_experiment') and \
			self.experiment.var.osf_always_upload_experiment == u"yes":
			self.checkbox_autosave_experiment.setCheckState(QtCore.Qt.Checked)

		# Check if local and remote versions of experiment are synced
		self.compare_versions(data)

	def __process_datafolder_info(self, reply):
		""" Callback for event_open_experiment """
		data = json.loads(safe_decode(reply.readAll().data()))
		try:
			osf_folder_path = data['data']['links']['self']
		except KeyError as e:
			warnings.warn('Invalid OSF response format: {}'.format(e))
		else:
			self.set_linked_experiment_datanode(osf_folder_path)
			# See if always upload data flag has been set in the experiment
			if not self.experiment.var.has('osf_always_upload_data'):
				return
			if self.experiment.var.osf_always_upload_data == u"yes":
				self.checkbox_autosave_data.setCheckState(QtCore.Qt.Checked)

	def __set_button_availabilty(self, tree_widget_item, col):
		""" Handles the QTreeWidget currentItemChanged event.

		Checks if buttons should be disabled or not, depending on the currently 
		selected tree item. For example, the Open button is only activated if an 
		OpenSesame experiment is selected."""
		# If selection changed to no item, disable all buttons
		if tree_widget_item is None:
			self.button_link_exp_to_osf.setDisabled(True)
			self.button_open_from_osf.setDisabled(True)
			return

		data = tree_widget_item.data(0, QtCore.Qt.UserRole)
		if data['type'] == 'nodes':
			name = data["attributes"]["title"]
			kind = data["attributes"]["category"]
		if data['type'] == 'files':
			name = data["attributes"]["name"]
			kind = data["attributes"]["kind"]

		# The save button should only be present when a folder
		# or an OpenSesame file is selected.
		if kind == "folder":
			self.button_link_exp_to_osf.setDisabled(False)
			self.button_link_data_to_osf.setDisabled(False)
		else:
			self.button_link_exp_to_osf.setDisabled(True)
			self.button_link_data_to_osf.setDisabled(True)

		# The open button should only be present when 
		# an OpenSesame file is selected.
		if widgets.check_if_opensesame_file(name, os3_only=True):
			self.button_open_from_osf.setDisabled(False)
		else:
			self.button_open_from_osf.setDisabled(True)

	def __mark_treewidget_item(self, item, remark_text):
		""" Makes all columns of the tree item bold and puts remarkt_text in the
		remark column. Used to show which treewidget items represent a linked
		experiment or data folder. """
		# Make all but the last columns to bold
		columns = self.project_tree.columnCount()
		font = item.font(0)
		font.setBold(True)
		for i in range(columns-2):
			item.setFont(i,font)
		# Last column contains remark_text. Make it italic
		item.setText(columns-1, remark_text)
		font = item.font(columns-1)
		font.setItalic(True)
		item.setFont(columns-1,font)

	def __unmark_treewidget_item(self, item):
		""" Removes marking of widget item as linked element """
		# Make all but the last columns to bold
		columns = self.project_tree.columnCount()
		font = item.font(0)
		font.setBold(False)
		for i in range(columns-2):
			item.setFont(i,font)
		# Last column contains remark_text. Make it italic
		item.setText(columns-1, '')
		font = item.font(columns-1)
		font.setItalic(False)
		item.setFont(columns-1,font)

	### PyQt slots

	def __show_explorer_tab(self):
		""" Shows the OSF tab in the main content section """
		self.tabwidget.add(self.project_explorer, self.osf_icon, _(u'OSF Explorer'))

	def __handle_check_autosave_experiment(self, state):
		""" slot for checkbox_autosave_experiment"""
		if state == QtCore.Qt.Checked:
			self.experiment.var.osf_always_upload_experiment = u"yes"
		else:
			self.experiment.var.osf_always_upload_experiment = u"no"

	def __handle_check_autosave_data(self, state):
		""" slot for checkbox_autosave_data"""		
		if state == QtCore.Qt.Checked:
			self.experiment.var.osf_always_upload_data = u"yes"
		else:
			self.experiment.var.osf_always_upload_data = u"no"

	def __mark_linked_nodes(self):
		""" Callback for self.tree.refreshFinished. Marks all files that are
		connected to the OSF in the tree. """
		
		iterator = QtWidgets.QTreeWidgetItemIterator(self.project_tree)
		while(iterator.value()):
			item = iterator.value()
			item_data = item.data(0,QtCore.Qt.UserRole)
			# Mark linked experiment
			if self.experiment.var.has('osf_id'):
				if item_data['id'] == self.experiment.var.osf_id:
					self.__mark_treewidget_item(item, _(u"Linked experiment"))
					self.linked_experiment_treewidgetitem = item
			if self.experiment.var.has('osf_datanode_id'):
				if item_data['id'] == self.experiment.var.osf_datanode_id:
					self.__mark_treewidget_item(item, _(u"Linked data folder"))
					self.linked_datanode_treewidgetitem = item
			iterator += 1

	### Actions for experiments

	def __prepare_experiment_sync(self, reply, *args, **kwargs):
		""" Callback for event_save_experiment.

		Retrieves the correct upload(/update) link for an experiment on the OSF.
		And uploads the currently open/linked experiment to that link. """
		# Parse the response
		data = json.loads(safe_decode(reply.readAll().data()))
		# Check if structure is valid, and if so, parse experiment's osf path
		# from the data.
		try:
			upload_url = data['data']['links']['upload']
		except KeyError as e:
			warnings.warn('Invalid OSF response format: {}'.format(e))
			return

		# Convert to QFile (to get size info later)
		file_to_upload = QtCore.QFile(self.main_window.current_path)
		# Add this parameters so OSF knows what we want
		upload_url += '?kind=file'

		# Create a progress dialog to show upload status for large experiments
		# that take a while to transfer
		progress_dialog = QtWidgets.QProgressDialog()
		progress_dialog.hide()
		progress_dialog.setLabelText(_(u"Please wait. Syncing") + u" " \
			+ file_to_upload.fileName())
		progress_dialog.setMinimum(0)
		progress_dialog.setMaximum(file_to_upload.size())

		self.manager.upload_file(
			upload_url,
			file_to_upload,
			uploadProgress=self.project_explorer._transfer_progress,
			progressDialog=progress_dialog,
			finishedCallback=self.project_explorer._upload_finished,
			afterUploadCallback=self.__notify_sync_complete,
			message=_(u"Experiment"
				" successfully synced to the Open Science Framework")
		)

	def __open_osf_experiment(self):
		""" Downloads and then opens an OpenSesame experiment from the OSF """
		selected_item = self.project_tree.currentItem()
		# If no item is selected, this result will be None
		if not selected_item:
			return
		# Get the selected item's name
		data = selected_item.data(0, QtCore.Qt.UserRole)
		download_url = data['links']['download']
		filename = data['attributes']['name']

		# If the selected item is not an OpenSesame file, stop.
		if not widgets.check_if_opensesame_file(filename, os3_only=True):
			return

		# See if a previous folder was set, and if not, try to set
		# the user's home folder as a starting folder of the dialog
		if not hasattr(self.project_explorer, 'last_dl_destination_folder'):
			self.project_explorer.last_dl_destination_folder = os.path.expanduser("~")

		# Show dialog in which user chooses where to save the experiment locally
		# If the experiment already exists, check if it is the same linked experiment.
	
		destination = QtWidgets.QFileDialog.getSaveFileName(self.project_explorer,
			_("Choose location on your computer to store experiment"),
			os.path.join(self.project_explorer.last_dl_destination_folder, filename),
		)

		# PyQt5 returns a tuple, because it actually performs the function of
		# PyQt4's getSaveFileNameAndFilter() function
		if isinstance(destination, tuple):
			destination = destination[0]

		if destination:
			# Remember this folder for later when this dialog has to be presented again
			self.last_dl_destination_folder = os.path.dirname(destination)
			# Some file providers do not report the size. Check for that here
			if data['attributes']['size']:
				# Configure progress dialog
				download_progress_dialog = QtWidgets.QProgressDialog()
				download_progress_dialog.hide()
				download_progress_dialog.setLabelText(_("Downloading") + " " + filename)
				download_progress_dialog.setMinimum(0)
				download_progress_dialog.setMaximum(data['attributes']['size'])
				progress_cb = self.project_explorer._transfer_progress
			else:
				download_progress_dialog = None
				progress_cb = None
			
			# Download the file
			self.manager.download_file(
				download_url,
				destination,
				downloadProgress=progress_cb,
				progressDialog=download_progress_dialog,
				finishedCallback=self.__experiment_downloaded,
				osf_data=data
			)
			
	def __experiment_downloaded(self, reply, progressDialog, *args, **kwargs):
		""" Callback for __open_osf_experiment() """

		saved_exp_location = kwargs.get('destination')
	
		if isinstance(progressDialog, QtWidgets.QWidget):
			progressDialog.deleteLater()

		# Open experiment in OpenSesame
		self.main_window.open_file(path=saved_exp_location, add_to_recent=True)

		# Show notification
		self.manager.success_message.emit(_(u'Experiment opened'),_(u'Your '
		'experiment was successfully downloaded to {}'.format(saved_exp_location)))

		# Embed OSF node id in the experiment (if it's not already there)
		if not self.experiment.var.has('osf_id'):
			# Embed osf id in the experiment
			self.experiment.var.osf_id = kwargs['osf_data']['id']
			# And save it
			self.main_window.save_file()
			self.set_linked_experiment(kwargs['osf_data']['links']['self'])

	### Actions for experiment data
	
	def __prepare_experiment_data_sync_get_upload_url(self, reply, data_files, node_id):
		data = json.loads(safe_decode(reply.readAll().data()))['data']

		if isinstance(data, dict):
			#probabaly a subfolder of a repo
			try:
				upload_url = data['links']['upload']
				files_url = data['relationships']['files']['links']['related']['href']
			except KeyError as e:
				warnings.warn("Invalid OSF data structure: {}".format(e))
				return
		if isinstance(data, list):
			# Probably a listing of project repositories
			# Search for selected repository
			node = next((item for item in data if item["id"] == node_id), None)
			# In the unlikely case that repository hasn't been found, quit
			if node is None:
				self.notifier.danger('Error','Something went wrong in node selection')
				return

			try:
				upload_url = node['links']['upload']
				files_url = node['relationships']['files']['links']['related']['href']
			except KeyError as e:
				warnings.warn("Invalid OSF data structure: {}".format(e))
				return

		# Check for duplicates
		self.manager.get(files_url, self.__prepare_experiment_data_sync,
			data_files=data_files, upload_url=upload_url)

	def __prepare_experiment_data_sync(self, reply, data_files, upload_url):
		""" Callback for event_process_data_files.

		Retrieves the correct upload link for experiment data on the OSF.
		Checks if the files to upload are not already present in the folder."""
		# Parse the response
		data = json.loads(safe_decode(reply.readAll().data()))['data']

		# Generate a list of files already present in this folder
		present_files = [f['attributes']['name'] for f in data]

		for data_file in data_files:
			# Check if data file is already present on the server
			filename = os.path.basename(data_file)
			if filename in present_files:
				reply = QtWidgets.QMessageBox.question(
					None,
					_(u"Please confirm"),
					_(u"A data file with the same name is already present at "
						"the linked location. Do you want to overwrite it?"),
					QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes
				)
				if reply == QtWidgets.QMessageBox.No:
					continue

				file_on_osf = next((item for item in data if \
					item['attributes']['name'] == filename), None)

				# Safety check, should never occur because it's logically
				# impossible, but hey...
				if not file_on_osf:
					warnings.warn(_(u"Something went wrong at checking for duplicate "
						"file: {}".format(filename)))
					continue
				file_upload_url = file_on_osf['links']['upload']
				upload_url = "{}?kind=file".format(file_upload_url)
			else:
				upload_url = "{}?kind=file&name={}".format(
					upload_url, filename)

			# Convert to QFile (to get size info later)
			file_to_upload = QtCore.QFile(data_file)

			# Create a progress dialog to show upload status for large experiments
			# that take a while to transfer
			progress_dialog = QtWidgets.QProgressDialog()
			progress_dialog.hide()
			progress_dialog.setLabelText(_(u"Please wait. Syncing") + u" " \
				+ file_to_upload.fileName())
			progress_dialog.setMinimum(0)
			progress_dialog.setMaximum(file_to_upload.size())

			self.manager.upload_file(
				upload_url,
				file_to_upload,
				uploadProgress=self.project_explorer._transfer_progress,
				progressDialog=progress_dialog,
				finishedCallback=self.project_explorer._upload_finished,
				afterUploadCallback=self.__notify_sync_complete,
				message=_(u"{} successfully synced to the Open Science "
					"Framework".format(filename))
			)

	### (Un)linking of experiments

	def __link_experiment_to_osf(self):
		""" Links an experiment to a folder on the OSF and uploads it to that
		location """
		# Check if an experiment is opened
		if not self.main_window.current_path:
			self.notifier.warning(_(u'File not saved'), 
				_(u"Please save experiment before linking it to the Open "
					"Science Framework"))
			return

		#If opened, check if the experiment is already linked to OSF
		if self.experiment.var.has('osf_id'):
			reply = QtWidgets.QMessageBox.question(
				None,
				_(u"Please confirm"),
				_(u"This experiment already seems to be linked to a location "
					"on the OSF. Are you sure you want to change this link?"),
				QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes
			)
			if reply == QtWidgets.QMessageBox.No:
				return

		# Get the data for the selected item and check if it is valid
		try:
			selected_item = self.__get_selected_node_for_link()
			data = selected_item.data(0, QtCore.Qt.UserRole)
		except ValueError as e:
			warnings.warn(e)
			return

		# Get URL to upload to
		upload_url = data['links']['upload']
		experiment_filename = os.path.split(self.main_window.current_path)[1]

		# Convert to QFile (to get size info later)
		file_to_upload = QtCore.QFile(self.main_window.current_path)

		# See if file is already present in this folder
		index_if_present = self.project_explorer.tree.find_item(
			selected_item, 0, experiment_filename)

		# If index_is_present is None, the file is probably new
		if index_if_present is None:
			# add required query parameters
			upload_url += '?kind=file&name={}'.format(experiment_filename)
		# If index_is_present is a number, it means the file is present
		# and that file needs to be updated.
		else:
			# If the file is already found, ask the user if it should be 
			# overwritten
			reply = QtWidgets.QMessageBox.question(
				None,
				_(u"Please confirm"),
				_(u"An experiment with the same filename was already found in"
					" this folder. Are you sure you want to overwrite it?"),
				QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes
			)
			if reply == QtWidgets.QMessageBox.No:
				return
			
			old_item = selected_item.child(index_if_present)
			# Get data stored in item
			old_item_data = old_item.data(0,QtCore.Qt.UserRole)
			# Get file specific update utrl
			upload_url = old_item_data['links']['upload']
			upload_url += '?kind=file'

		# Create a progress dialog to show upload status for large experiments
		# that take a while to transfer
		progress_dialog = QtWidgets.QProgressDialog()
		progress_dialog.hide()
		progress_dialog.setLabelText(_(u"Please wait. Syncing") + u" " \
			+ file_to_upload.fileName())
		progress_dialog.setMinimum(0)
		progress_dialog.setMaximum(file_to_upload.size())

		self.manager.upload_file(
			upload_url,
			file_to_upload,
			uploadProgress=self.project_explorer._transfer_progress,
			progressDialog=progress_dialog,
			finishedCallback=self.project_explorer._upload_finished,
			afterUploadCallback=self.__link_experiment_succeeded,
			selectedTreeItem=selected_item,
			updateIndex=index_if_present
		)		
		
	def __link_experiment_succeeded(self, *args, **kwargs):
		""" Callback for __link_experiment_to_osf if it succeeded. This function
		adds the new item to the tree, without refreshing it completely. For now,
		it only works with items added to osfstorage as the data return by other
		providers is very unpredicatble. These simply trigger a full refresh of
		the tree and don't supply 'new_item_data' to this function. If this is the
		case, this function simply returns. """
		
		# Get the data returned by the OSF for the newly created item. This data
		# is severely lacking compared to what it normally returns for info requests
		# The complete new tree_widget_item should also be available as the 
		# 'new_item' kwarg	
		# for any other provider than osfstorage, new_item_data is useless.
		new_item_data = kwargs.get('new_item_data')
		if new_item_data is None:
			return

		try:
			# The data returne by OSF is really messy, but since we don't have access
			# to the refreshed data yet, we'll have to make due with it.
			# Parse OSF id from download url (it is the final component) 
			self.experiment.var.osf_id = \
				os.path.basename(new_item_data['data']['links']['download'])
		except KeyError as e:
			self.notifier.error('Error',
				_(u'Received data structure not as expected: {}'.format(e)))
			return
		# Generate the api url ourselves with the id we just determined
		osf_path = osf.api_call('file_info', self.experiment.var.osf_id)
		# Set the linked information
		self.set_linked_experiment(osf_path)

		new_item = kwargs.get('new_item')
		# Mark the current item as linked, and unmark the old one if present
		if isinstance(self.linked_experiment_treewidgetitem, 
			QtWidgets.QTreeWidgetItem) and new_item:
			self.__unmark_treewidget_item(self.linked_experiment_treewidgetitem)
			self.__mark_treewidget_item(new_item, _(u"Linked experiment"))
			self.linked_experiment_treewidgetitem = new_item

		# Notify the user about the success
		self.notifier.success(_(u'Experiment successfully linked'),
			_(u'The experiment has been linked to the OSF at ') + osf_path)

	def __unlink_experiment(self):
		""" Unlinks the experiment from the OSF """
		reply = QtWidgets.QMessageBox.question(
			None,
			_(u'Please confirm'),
			_(u'Are you sure you want to unlink this experiment from OSF?'),
			QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes
		)
		if reply == QtWidgets.QMessageBox.No:
			return

		if isinstance(self.linked_experiment_treewidgetitem, 
			QtWidgets.QTreeWidgetItem):
			self.__unmark_treewidget_item(self.linked_experiment_treewidgetitem)
			self.linked_experiment_treewidgetitem = None	

		self.set_linked_experiment(None)
		self.experiment.var.unset('osf_id')
		self.experiment.var.unset('osf_always_upload_experiment')

	### (Un)linking of experiment data

	def __link_data_to_osf(self):
		""" Creates a link to an OSF node to which to (automatically) upload the
		data of an experiment to, after it is finished. """
		# Check if an experiment is opened
		if not self.main_window.current_path:
			self.notifier.warning(_(u'File not saved'), 
				_(u'Please save experiment before linking it to the Open '
					'Science Framework'))
			return

		#If opened, check if the experiment is already linked to OSF
		if self.experiment.var.has('osf_datanode_id') and \
			self.experiment.var.osf_datanode_id:
			reply = QtWidgets.QMessageBox.question(
				None,
				_(u'Please confirm'),
				_(u'This experiment already seems have a linked location '
					'on the OSF to upload data to. Are you sure you want to '
					' change this link?'),
				QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes
			)
			if reply == QtWidgets.QMessageBox.No:
				return

		# Get the data for the selected item and check if it is valid
		try:
			selected_item = self.__get_selected_node_for_link()
			data = selected_item.data(0, QtCore.Qt.UserRole)
		except ValueError as e:
			warnings.warn(str(e))
			return

		# Get URL to upload to
		# If selected item is a normal folder it, will have a 'self' entry
		# use that if available
		try:
			node_url = data['links']['self']
		except KeyError:
			# If selected item is a data provider node, it can only be referenced
			# by its 'upload' entry. Display that in this case.
			try:
				node_url = data['links']['upload']
			except:
				warnings.warn("Could not determine folder url")
				return	

		self.experiment.var.osf_datanode_id = data['id']
		self.set_linked_experiment_datanode(node_url)

		# Mark the current item as linked, and unmark the old one if present
		if isinstance(self.linked_datanode_treewidgetitem, 
			QtWidgets.QTreeWidgetItem) and selected_item:
			self.__unmark_treewidget_item(self.linked_datanode_treewidgetitem)
			self.__mark_treewidget_item(selected_item, _(u"Linked data folder"))
			self.linked_datanode_treewidgetitem = selected_item

		# Notify the user about the success
		self.notifier.success(_(u'Data folder successfully linked'),
			_(u'The data upload folder has been set to ') + node_url)
			
	def __unlink_data(self):
		""" Unlinks the experiment from the OSF """
		reply = QtWidgets.QMessageBox.question(
			None,
			_(u"Please confirm"),
			_(u"Are you sure you want to unlink this experiment's data storage from OSF?"),
			QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes
		)
		if reply == QtWidgets.QMessageBox.No:
			return

		if isinstance(self.linked_datanode_treewidgetitem, 
			QtWidgets.QTreeWidgetItem):
			self.__unmark_treewidget_item(self.linked_datanode_treewidgetitem)
			self.linked_datanode_treewidgetitem = None

		self.set_linked_experiment_datanode(None)
		self.experiment.var.unset('osf_datanode_id')
		self.experiment.var.unset('osf_always_upload_data')
		
	### Other common utility functions
	def __notify_sync_complete(self, message, data_to_send):
		""" Callback for __prepare_experiment_sync and __prepare_experiment_data_sync.
		Simply notifies if the syncing operation completed successfully. """
		self.notifier.success(_(u'Sync success'), message)

	def __get_selected_node_for_link(self):
		""" Checks if current selection is valid for linking operation, which
		can only be done to folders (DRY). Returns the selected tree item containing
		the node information. """
		selected_item = self.project_tree.currentItem()

		# If no item is selected, this result will be None
		if not selected_item:
			raise ValueError('No item was selected')
		# Get the selected item's name
		data = selected_item.data(0, QtCore.Qt.UserRole)
		
		# Data is 'node' if a top-level project is selected.
		if data['type'] != 'files':
			raise ValueError('Top-level repository selected, only folders allowed')

		# If the selected item is not an OpenSesame file or folder to store
		# the experiment in, stop.
		if not data['attributes']['kind'] == 'folder':
			raise ValueError('Only folders can be linkd to')

		return selected_item
	
	