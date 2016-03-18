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

from qtpy.QtWidgets import QMenu, QToolBar

from libopensesame import debug
from libqtopensesame.extensions import base_extension
from libqtopensesame.misc.translate import translation_context
_ = translation_context(u'undo_manager', category=u'extension')

__author__ = u"Daniel Schreij"
__license__ = u"Apache2"

from openscienceframework import widgets, events, manager
import os

class OpenScienceFramework(base_extension):

	### OpenSesame events
	def event_startup(self):
		self.__initialize()
	
	def activate(self):
		""" Show OSF Explorer in full glory (all possibilities enabled) """
		config = {'mode':'full'}
		self.project_explorer.config = config
		self.__show_explorer_tab()
	
	def event_save_experiment(self, path):
		debug.msg(u'OSF: Event caught: save_experiment(path=%s)' % path)

	### Other events
	def handle_login(self):
		self.save_to_osf.setDisabled(False)
		self.open_from_osf.setDisabled(False)

	def handle_logout(self):
		self.save_to_osf.setDisabled(True)
		self.open_from_osf.setDisabled(True)

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

		# Token file listener writes the token to a json file if it receives
		# a logged_in event and removes this file after logout
		# Filename of the file to store token information in.
		self.tfl = events.TokenFileListener(tokenfile)

		self.manager.dispatcher.add_listeners(
			[
				self, self.tfl, project_tree,
				self.user_badge, self.project_explorer
			]
		)
		# Connect click on user badge logout button to osf logout action
		self.user_badge.logout_request.connect(self.manager.logout)
		self.user_badge.login_request.connect(self.manager.login)

		# Show the user badge
		self.toolbar.addWidget(self.user_badge)

		# Save to OSF menu item
		self.save_to_osf = self.qaction(u'go-up', _(u'Save to OSF'), self.__save_exp,
			tooltip=_(u'Save an experiment to the OpenScienceFramework'))
		self.save_to_osf.setDisabled(True)

		# Open from OSF menu item
		self.open_from_osf = self.qaction(u'go-down', _(u'Open from OSF'), self.__open_exp,
			tooltip=_(u'Open an experiment stored on the OpenScienceFramework'))
		self.open_from_osf.setDisabled(True)

		# Add other actions to menu
		for w in self.action.associatedWidgets():
			if not isinstance(w, QMenu):
				continue
			w.addAction(self.save_to_osf)
			w.addAction(self.open_from_osf)

	def __show_explorer_tab(self):
		self.tabwidget.add(self.project_explorer, self.osf_icon, 'OSF Explorer')

	def __open_exp(self, *args, **kwargs):
		config = {'mode':'open'}
		self.project_explorer.config = config
		self.__show_explorer_tab()
		
	def __save_exp(self, *args, **kwargs):
		config = {'mode':'save'}
		self.project_explorer.config = config
		self.__show_explorer_tab()
		
	
	