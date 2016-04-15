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

from qtpy import QtWidgets, QtCore, QtGui

from libopensesame import debug
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
		self.extension_manager.fire('notify', message=message, kind='danger')

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
		self.extension_manager.fire('notify', message=message, kind='warning')

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
		self.extension_manager.fire('notify', message=message, kind='info')

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
		self.extension_manager.fire('notify', message=message, kind='success')


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
		self.extension_manager.fire('notify', message=message, kind='primary')


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

	### OpenSesame events
	def event_startup(self):
		self.__initialize()
	
	def activate(self):
		""" Show OSF Explorer with default buttons enabled. Also check if osf_id
		is still set and if it is valid. Users have access to it through the 
		variable registry object, so it is possible they tampered with it. """
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
		self.__show_explorer_tab()	
	
	def event_save_experiment(self, path):
		""" See if experiment needs to be synced to OSF and do so if necessary"""
		# First check if OSF id has been set
		if not self.experiment.var.has('osf_id') or not self.manager.logged_in_user:
			return
		
		osf_id = self.experiment.var.osf_id

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
		# If user is not logged in, issue a warning on opening that a linkt to
		# the OSF has been detected, but no syncing can occur as long is the user
		# is not logged in.
		elif self.experiment.var.has('osf_id') or \
			self.experiment.var.has('osf_datanode_id'):
			self.notifier.info(_(u'OSF link detected'),
				_(u'This experiment seems to be linked to the Open Science '
					'Framework. Please login if you want to use the syncing '
					'functionalities'))

	def event_close(self):
		""" Reset the OSF parameters to unlinked """
		self.set_linked_experiment(None)
		self.set_linked_experiment_datanode(None)

	def event_end_experiment(self, ret_val):
		""" See if datafiles need to be saved to OSF """
		debug.msg(u'Event fired: end_experiment')

	### Other internal events
	def handle_login(self):
		# self.save_to_osf.setDisabled(False)
		# self.open_from_osf.setDisabled(False)
		self.action.setDisabled(False)

	def handle_logout(self):
		# self.save_to_osf.setDisabled(True)
		# self.open_from_osf.setDisabled(True)
		self.action.setDisabled(True)

	### Private functions
		
	def __initialize(self):
		tokenfile = os.path.abspath("token.json")
		
		# Initialize notifier
		self.notifier = Notifier(self.extension_manager)

		# Create manager object
		self.manager = manager.ConnectionManager(tokenfile, self.notifier)

		# Init and set up user badge
		icon_size = self.toolbar.iconSize()
		self.user_badge = widgets.UserBadge(self.manager, icon_size)

		# Set-up project tree
		self.project_tree = widgets.ProjectTree(self.manager)
		self.project_tree.currentItemChanged.connect(self.__currentTreeItemChanged)

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

		# Token file listener writes the token to a json file if it receives
		# a logged_in event and removes this file after logout
		self.tfl = events.TokenFileListener(tokenfile)

		# Add items as listeners to the event Notifier
		self.manager.dispatcher.add_listeners(
			[
				self, self.tfl, self.project_tree, self.manager,
				self.user_badge, self.project_explorer
			]
		)
		# Connect click on user badge log in/out button to osf log in/out actions
		self.user_badge.logout_request.connect(self.manager.logout)
		self.user_badge.login_request.connect(self.manager.login)

		# Show the user badge
		self.toolbar.addWidget(self.user_badge)
		self.current_mode = u"full"

	def __setup_buttons(self, explorer):
		""" Set up the extra buttons which the extension adds to the standard
		OSF explorer's """
		# Link to OpenSesame buttons

		# Link experiment to folder
		self.button_link_exp_to_osf = QtWidgets.QPushButton(_(u'Link experiment'))
		self.button_link_exp_to_osf.setIcon(QtGui.QIcon.fromTheme('insert-link'))
		self.button_link_exp_to_osf.clicked.connect(self.__link_experiment_to_osf)
		self.button_link_exp_to_osf.setDisabled(True)

		# Link data folder
		self.button_link_data_to_osf = QtWidgets.QPushButton(_(u'Link data folder'))
		self.button_link_data_to_osf.setIcon(QtGui.QIcon.fromTheme('insert-link'))
		self.button_link_data_to_osf.clicked.connect(self.__link_data_to_osf)
		self.button_link_data_to_osf.setDisabled(True)
		
		# Open from OSF buttons
		self.button_open_from_osf = QtWidgets.QPushButton(_(u'Open'))
		self.button_open_from_osf.setIcon(QtGui.QIcon.fromTheme('document-open'))
		self.button_open_from_osf.clicked.connect(self.__open_osf_experiment)
		self.button_open_from_osf.setDisabled(True)

		# Unlink experiment button
		self.button_unlink_experiment = QtWidgets.QPushButton(_(u'Unlink'))
		self.button_unlink_experiment.clicked.connect(self.__unlink_experiment)
		self.button_unlink_experiment.setDisabled(True)

		# Unlink data button
		self.button_unlink_data = QtWidgets.QPushButton(_(u'Unlink'))
		self.button_unlink_data.clicked.connect(self.__unlink_data)
		self.button_unlink_data.setDisabled(True)

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
		if not self.experiment.var.has('osf_always_upload_experiment'):
			return
		if self.experiment.var.osf_always_upload_experiment == u"yes":
			self.checkbox_autosave_experiment.setCheckState(QtCore.Qt.Checked)

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

	def __set_button_availabilty(self, tree_widget_item):
		""" Checks if buttons should be disabled or not, depending on the currently 
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
		else:
			self.button_link_exp_to_osf.setDisabled(True)

		# The open button should only be present when 
		# an OpenSesame file is selected.
		if widgets.check_if_opensesame_file(name, os3_only=True):
			self.button_open_from_osf.setDisabled(False)
		else:
			self.button_open_from_osf.setDisabled(True)

	### PyQt slots

	def __show_explorer_tab(self):
		""" Shows the OSF tab in the main content section """
		self.tabwidget.add(self.project_explorer, self.osf_icon, _(u'OSF Explorer'))

	def __currentTreeItemChanged(self, item, col):
		""" Handles the QTreeWidget currentItemChanged event. """
		self.__set_button_availabilty(item)

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

	### Actions for experiments

	def __prepare_experiment_sync(self, reply):
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
			afterUploadCallback=self.__notify_sync_complete
		)

	def __notify_sync_complete(self, *args, **kwargs):
		""" Callback for __prepare_experiment_sync.
		Simply notifies if the syncing operation completed successfully. """

		self.notifier.success(_(u'Sync success'),_(u'Experiment successfully'
			' synced to the Open Science Framework'))

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
			try:
				self.manager.download_file(
					download_url,
					destination,
					downloadProgress=progress_cb,
					progressDialog=download_progress_dialog,
					finishedCallback=self.__experiment_downloaded,
					osf_data=data
				)
			except Exception as e:
				print(e)

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

	def __link_experiment_to_osf(self):
		""" Links an experiment to a folder on the OSF and uploads it to that
		location """
		# Check if an experiment is opened
		if not self.main_window.current_path:
			self.notifier.warning(_(u'File not saved'), 
				_(u'Please save experiment before linking it to the Open '
					'Science Framework'))
			return

		#If opened, check if the experiment is already linked to OSF
		if self.experiment.var.has('osf_id'):
			reply = QtWidgets.QMessageBox.question(
				None,
				_("Please confirm"),
				_("This experiment already seems to be linked to a location "
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
		""" Callback for __link_experiment_to_osf if it succeeded """
		# Get the data returned by the OSF for the newly created item. This data
		# is severely lacking compared to what it normall returns for info requests
		new_item = kwargs.get('new_item')
		if new_item is None:
			self.notifier.error('Error',_(u'Could not retrieve added item info from OSF'))
			return

		try:
			# The data returne by OSF is really messy, but since we don't have access
			# to the refreshed data yet, we'll have to make due with it.
			# Parse OSF id from download url (it is the final component) 
			self.experiment.var.osf_id = \
				os.path.basename(new_item['data']['links']['download'])
		except KeyError as e:
			self.notifier.error('Error',
				_(u'Received data structure not as expected: {}'.format(e)))
			return
		# Generate the api url ourselves with the id we just determined
		osf_path = osf.api_call('file_info', self.experiment.var.osf_id)
		# Set the linked information
		self.set_linked_experiment(osf_path)
		# Notify the user about the success
		self.notifier.success(_(u"Experiment successfully linked"),
			_(u"The experiment has been linked to the OSF at ") + osf_path)

	def __unlink_experiment(self):
		""" Unlinks the experiment from the OSF """
		reply = QtWidgets.QMessageBox.question(
			None,
			_("Please confirm"),
			_("Are you sure you want to unlink this experiment from OSF?"),
			QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes
		)
		if reply == QtWidgets.QMessageBox.No:
			return
		self.set_linked_experiment(None)
		self.experiment.var.unset('osf_id')
		self.experiment.var.unset('osf_always_upload_experiment')

	### Actions for experiment data

	def __link_data_to_osf(self):
		try:
			selected_item = self.__get_selected_node_for_link()
			data = selected_item.data(0, QtCore.Qt.UserRole)
		except ValueError as e:
			warnings.warn(e)
			return

		osf_id = data['id']

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
		self.set_linked_experiment_datanode(None)
		self.experiment.var.unset('osf_datanode_id')
		self.experiment.var.unset('osf_always_upload_data')
		
	### Other common utility functions

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
	
	