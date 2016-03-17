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

from libopensesame import debug
from libqtopensesame.extensions import base_extension

__author__ = u"Daniel Schreij"
__license__ = u"Apache2"

from openscienceframework import widgets, events, manager
import os

class OpenScienceFramework(base_extension):

	def event_startup(self):
		tokenfile = os.path.abspath("token.json")
		# Create manager object
		self.manager = manager.ConnectionManager(tokenfile)

		# Init and set up user badge
		self.user_badge = widgets.UserBadge(self.manager)

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
				self.tfl, project_tree,
				self.user_badge, self.project_explorer
			]
		)
		# Connect click on user badge logout button to osf logout action
		self.user_badge.logout_request.connect(self.manager.logout)
		self.user_badge.login_request.connect(self.manager.login)

		# Show the user badge
		self.toolbar.addWidget(self.user_badge)
	
	def activate(self):
		""" Show OSF Explorer in full glory (all possibilities enabled """
		self.tabwidget.add(self.project_explorer, self.osf_icon, 'OSF Explorer')
		#self.project_explorer.show()
	
	def event_save_experiment(self, path):
		debug.msg(u'OSF: Event caught: save_experiment(path=%s)' % path)
		
	
	