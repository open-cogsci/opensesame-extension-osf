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

from qtpy import QtWidgets, QtCore

from libopensesame import debug
from libqtopensesame.extensions import base_extension
from libqtopensesame.misc.translate import translation_context
_ = translation_context(u'undo_manager', category=u'extension')

__author__ = u"Daniel Schreij"
__license__ = u"Apache2"

from openscienceframework import widgets, events, manager
import os

class OpenScienceFramework(base_extension):

	OpenSesame_filetypes = ['*.osexp','*.opensesame','*.opensesame.tar.gz']

	### OpenSesame events
	def event_startup(self):
		self.__initialize()
	
	def activate(self):
		""" Show OSF Explorer with  default buttons enabled """
		self.__set_full_mode()
	
	def event_save_experiment(self, path):
		""" See if experiment needs to be synced to OSF """
		debug.msg(u'OSF: Event caught: save_experiment(path=%s)' % path)

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
		# Create manager object
		self.manager = manager.ConnectionManager(tokenfile)

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

		# Add items as listeners to the event dispatcher
		self.manager.dispatcher.add_listeners(
			[
				self, self.tfl, self.project_tree,
				self.user_badge, self.project_explorer
			]
		)
		# Connect click on user badge log in/out button to osf log in/out actions
		self.user_badge.logout_request.connect(self.manager.logout)
		self.user_badge.login_request.connect(self.manager.login)

		# Show the user badge
		self.toolbar.addWidget(self.user_badge)

		# # Save to OSF menu item
		# self.save_to_osf = self.qaction(u'go-up', _(u'Save to OSF'), 
		# 	self.__set_save_expirment_mode,
		# 	tooltip=_(u'Save an experiment to the OpenScienceFramework'))
		# self.save_to_osf.setDisabled(True)

		# # Open from OSF menu item
		# self.open_from_osf = self.qaction(u'go-down', _(u'Open from OSF'), 
		# 	self.__set_open_experiment_mode,
		# 	tooltip=_(u'Open an experiment stored on the OpenScienceFramework'))
		# self.open_from_osf.setDisabled(True)

		# Add other actions to menu
		for w in self.action.associatedWidgets():
			if not isinstance(w, QtWidgets.QMenu):
				continue
			w.addAction(self.save_to_osf)
			w.addAction(self.open_from_osf)
		self.action.setDisabled(True)
		self.current_mode = u"full"

	def __setup_buttons(self, explorer):
		# Link to OpenSesame buttons
		self.__button_link_to_osf = QtWidgets.QPushButton(_(u'Link to OSF'))
		self.__button_link_to_osf.clicked.connect(self.__link_experiment_to_osf)
		# explorer.add_buttonset('link',[self.__button_link_to_osf])
		
		# Open from OSF buttons
		self.__button_open_from_osf = QtWidgets.QPushButton(_(u'Open from OSF'))
		self.__button_open_from_osf.clicked.connect(self.__open_osf_experiment)
		# explorer.add_buttonset('open',[self.__button_open_from_osf])

	def __add_info_linked_widget(self, explorer):
		# Create widget
		info_widget = QtWidgets.QWidget()

		# Set up layout
		info_layout = QtWidgets.QGridLayout()
		info_layout.setContentsMargins(15,11,15,40)

		# Set up labels
		currently_linked_label = QtWidgets.QLabel(_(u"Experiment linked to:"))
		current_data_label = QtWidgets.QLabel(_(u"Data stored to:"))
		self.currently_linked_value = QtWidgets.QLabel(_(u"Not linked"))
		self.currently_linked_value.setStyleSheet("font-style: italic")
		self.current_data_value = QtWidgets.QLabel(_(u"Not linked"))
		self.current_data_value.setStyleSheet("font-style: italic")

		autosave_exp_widget = QtWidgets.QWidget()
		autosave_exp_layout = QtWidgets.QHBoxLayout()
		autosave_exp_widget.setLayout(autosave_exp_layout)
		autosave_exp_label = QtWidgets.QLabel(_(u"Always upload experiment on save"))
		self.autosave_exp_checkbox = QtWidgets.QCheckBox()
		autosave_exp_layout.addWidget(self.autosave_exp_checkbox)
		autosave_exp_layout.addWidget(autosave_exp_label)

		autosave_data_widget = QtWidgets.QWidget()
		autosave_data_layout = QtWidgets.QHBoxLayout()
		autosave_data_widget.setLayout(autosave_data_layout)
		self.autosave_data_checkbox = QtWidgets.QCheckBox()
		autosave_data_label = QtWidgets.QLabel(_(u"Always upload data on save"))
		autosave_data_layout.addWidget(self.autosave_data_checkbox)
		autosave_data_layout.addWidget(autosave_data_label)

		# Add labels to layout
		info_layout.addWidget(currently_linked_label, 1, 1)
		info_layout.addWidget(self.currently_linked_value, 1, 2)
		info_layout.addWidget(self.__button_link_to_osf,1, 3)
		info_layout.addWidget(autosave_exp_widget, 1, 4)
		info_layout.addWidget(current_data_label, 2, 1)
		info_layout.addWidget(self.current_data_value, 2, 2)
		info_layout.addWidget(self.__button_open_from_osf, 2, 3)
		info_layout.addWidget(autosave_data_widget, 2, 4)
		info_widget.setLayout(info_layout)

		# Make sure the info_widget is vertically as small as possible.
		info_widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, 
			QtWidgets.QSizePolicy.Fixed)
		
		explorer.main_layout.insertWidget(0, info_widget)


	def __set_button_availabilty(self, tree_widget_item):
		""" Set button availability depending on current mode """

		# If selection changed to no item, disable all buttons
		if tree_widget_item is None:
			self.__button_link_to_osf.setDisabled(True)
			self.__button_open_from_osf.setDisabled(True)
			return

		data = tree_widget_item.data(0, QtCore.Qt.UserRole)
		if data['type'] == 'nodes':
			name = data["attributes"]["title"]
			kind = data["attributes"]["category"]
		if data['type'] == 'files':
			name = data["attributes"]["name"]
			kind = data["attributes"]["kind"]

		# If mode is 'save', the save button should only be present when a folder
		# or an OpenSesame file is selected.
		if self.current_mode == "save":
			if kind == "folder" or widgets.check_if_opensesame_file(name):
				self.__button_link_to_osf.setDisabled(False)
			else:
				self.__button_link_to_osf.setDisabled(True)

		# If mode is 'open', the open button should only be present when 
		# an OpenSesame file is selected.
		elif self.current_mode == "open":
			if widgets.check_if_opensesame_file(name):
				self.__button_open_from_osf.setDisabled(False)
			else:
				self.__button_open_from_osf.setDisabled(True)

	### PyQt slots

	def __show_explorer_tab(self):
		self.tabwidget.add(self.project_explorer, self.osf_icon, _(u'OSF Explorer'))

	def __currentTreeItemChanged(self, item, col):
		""" Handles the QTreeWidget currentItemChanged event. Checks if buttons.
		should be disabled or not, depending on the currently selected tree item.
		For example, the Open button is only activated if an OpenSesame experiment
		is selected. """

		# Tree item takes care of its own button settings in this mode
		if self.current_mode == "full":
			return

		self.__set_button_availabilty(item)

	# Actions on experiments

	def __open_osf_experiment(self):
		selected_item = self.project_tree.currentItem()
		# If no item is selected, this result will be None
		if not selected_item:
			return
		# Get the selected item's name
		data = selected_item.data(0, QtCore.Qt.UserRole)
		download_url = data['links']['download']
		filename = data['attributes']['name']

		# If the selected item is not an OpenSesame file, stop.
		if not widgets.check_if_opensesame_file(filename):
			return

		# See if a previous folder was set, and if not, try to set
		# the user's home folder as a starting folder of the dialog
		if not hasattr(self.project_explorer, 'last_dl_destination_folder'):
			self.project_explorer.last_dl_destination_folder = os.path.expanduser("~")

		# Show dialog in which user chooses where to save the experiment locally
		# If the experiment already exists, check if it is the same linked experiment.
		destination = QtWidgets.QFileDialog.getSaveFileName(self,
			_("Save file as"),
			os.path.join(self.project_explorer.last_dl_destination_folder, filename),
		)

		# PyQt5 returns a tuple, because it actually performs the function of
		# PyQt4's getSaveFileNameAndFilter() function
		if isinstance(destination, tuple):
			destination = destination[0]

		if destination:
			# Remember this folder for later when this dialog has to be presented again
			self.last_dl_destination_folder = os.path.split(destination)[0]
			# Configure progress dialog
			download_progress_dialog = QtWidgets.QProgressDialog()
			download_progress_dialog.hide()
			download_progress_dialog.setLabelText(_("Downloading") + " " + filename)
			download_progress_dialog.setMinimum(0)
			download_progress_dialog.setMaximum(data['attributes']['size'])
			# Download the file
			self.manager.download_file(
				download_url,
				destination,
				downloadProgress=self.project_explorer.__transfer_progress,
				progressDialog=download_progress_dialog,
				finishedCallback=self.__experiment_downloaded,
				osf_data=data
			)

	def __experiment_downloaded(self, reply, progressDialog, *args, **kwargs):
		""" Callback for __open_osf_experiment() """

		self.manager.info_message.emit(_(u'Experiment downloaded'),_(u'Your '
		'experiment downloaded successfully'))
		progressDialog.deleteLater()

		# Open experiment in OpenSesame
		saved_exp_location = kwargs.get('destination')
		# opensesame.open(saved_exp_location)

		# # Embed OSF data in the experiment (if it's not already there)
		# if not opensesame.experiment.var.has('osf_id'):
		# 	# Embed osf id in the experiment
		# 	opensesame.experiment.var.osf_id = kwargs['osf_data']['id']
		

	def __link_experiment_to_osf(self):
		selected_item = self.project_tree.currentItem()
		# If no item is selected, this result will be None
		if not selected_item:
			return
		# Get the selected item's name
		data = selected_item.data(0, QtCore.Qt.UserRole)
		osf_id = data['id']

		# Data is 'node' if a top-level project is selected.
		if data['type'] != 'files':
			return

		filename = data['attributes']['name']
		kind = data['attributes']['kind']

		# If the selected item is not an OpenSesame file or folder to store
		# the experiment in, stop.
		if not kind == 'folder': # and not widgets.check_if_opensesame_file(filename):
			return

		# #Check if an experiment is opened
		# SomeOpenSesameCall()
		
		# #If opened, check if the experiment is already linked to OSF
		# if experiment.var.has('osf_id'):
		# 	# Check

	## display modes
	def __set_full_mode(self):
		config = {'buttonset':'default','filter': None}
		self.project_explorer.config = config
		self.__show_explorer_tab()
		self.current_mode = u"full"

	def __set_open_experiment_mode(self, *args, **kwargs):
		# Set explorer config for current mode
		config = {
			'buttonset':'open',
			'filter': self.OpenSesame_filetypes
		}
		self.project_explorer.config = config
		self.__show_explorer_tab()
		self.current_mode = u"open"
		# See if button for this mode should be enabled for current selection
		self.__set_button_availabilty(self.project_tree.currentItem())
		
	def __set_save_expirment_mode(self, *args, **kwargs):
		# Set explorer config for current mode
		config = {
			'buttonset':'link',
			'filter': self.OpenSesame_filetypes
		}
		self.project_explorer.config = config
		self.__show_explorer_tab()
		self.current_mode = u"save"
		# See if button for this mode should be enabled for current selection
		self.__set_button_availabilty(self.project_tree.currentItem())
		
	
	