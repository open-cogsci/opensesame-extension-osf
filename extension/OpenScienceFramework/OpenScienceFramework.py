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
		""" Show OSF Explorer in full glory (all possibilities enabled) """
		config = {'buttonset':'default','filter': None}
		self.project_explorer.config = config
		self.__show_explorer_tab()
	
	def event_save_experiment(self, path):
		debug.msg(u'OSF: Event caught: save_experiment(path=%s)' % path)

	### Other internal events
	def handle_login(self):
		self.save_to_osf.setDisabled(False)
		self.open_from_osf.setDisabled(False)
		self.action.setDisabled(False)

	def handle_logout(self):
		self.save_to_osf.setDisabled(True)
		self.open_from_osf.setDisabled(True)
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
		project_tree = widgets.ProjectTree(self.manager)

		# Save osf_icon for later usage
		self.osf_icon = project_tree.get_icon('folder', 'osfstorage')

		# Init and set up Project explorer
		# Pass it the project tree instance from
		self.project_explorer = widgets.OSFExplorer(
			self.manager, tree_widget=project_tree
		)

		# Set up the link and save to OSF buttons
		self.__setup_buttons(self.project_explorer)

		# Token file listener writes the token to a json file if it receives
		# a logged_in event and removes this file after logout
		self.tfl = events.TokenFileListener(tokenfile)

		# Add items as listeners to the event dispatcher
		self.manager.dispatcher.add_listeners(
			[
				self, self.tfl, project_tree,
				self.user_badge, self.project_explorer
			]
		)
		# Connect click on user badge log in/out button to osf log in/out actions
		self.user_badge.logout_request.connect(self.manager.logout)
		self.user_badge.login_request.connect(self.manager.login)

		# Show the user badge
		self.toolbar.addWidget(self.user_badge)

		# Save to OSF menu item
		self.save_to_osf = self.qaction(u'go-up', _(u'Save to OSF'), 
			self.__set_save_expirment_mode,
			tooltip=_(u'Save an experiment to the OpenScienceFramework'))
		self.save_to_osf.setDisabled(True)

		# Open from OSF menu item
		self.open_from_osf = self.qaction(u'go-down', _(u'Open from OSF'), 
			self.__set_open_experiment_mode,
			tooltip=_(u'Open an experiment stored on the OpenScienceFramework'))
		self.open_from_osf.setDisabled(True)

		# Add other actions to menu
		for w in self.action.associatedWidgets():
			if not isinstance(w, QtWidgets.QMenu):
				continue
			w.addAction(self.save_to_osf)
			w.addAction(self.open_from_osf)
		self.action.setDisabled(True)

	def __setup_buttons(self, explorer):
		# Link to OpenSesame buttons
		self.__button_link_to_osf = QtWidgets.QPushButton(_(u'Save to OSF'))
		self.__button_link_to_osf.clicked.connect(self.__link_experiment_to_osf)
		explorer.add_buttonset('link',[self.__button_link_to_osf])
		
		# Open from OSF buttons
		self.__button_open_from_osf = QtWidgets.QPushButton(_(u'Open from OSF'))
		self.__button_open_from_osf.clicked.connect(self.__open_osf_experiment)
		explorer.add_buttonset('open',[self.__button_open_from_osf])

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

	## Callback or function above
	def __experiment_downloaded(self, reply, progressDialog, *args, **kwargs):
		self.manager.info_message.emit(__(u'Experiment downloaded'),__(u'Your '
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
		if not kind == 'folder' and not widgets.check_if_opensesame_file(filename):
			return

		# #Check if an experiment is opened
		# SomeOpenSesameCall()
		
		# #If opened, check if the experiment is already linked to OSF
		# if experiment.var.has('osf_id'):
		# 	# Check

	def __show_explorer_tab(self):
		self.tabwidget.add(self.project_explorer, self.osf_icon, _(u'OSF Explorer'))

	def __set_open_experiment_mode(self, *args, **kwargs):
		config = {
			'buttonset':'open',
			'filter': self.OpenSesame_filetypes
		}
		self.project_explorer.config = config
		self.__show_explorer_tab()
		
	def __set_save_expirment_mode(self, *args, **kwargs):
		config = {
			'buttonset':'link',
			'filter': self.OpenSesame_filetypes
		}
		self.project_explorer.config = config
		self.__show_explorer_tab()
		
	
	