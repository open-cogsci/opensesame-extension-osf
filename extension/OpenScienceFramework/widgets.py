# -*- coding: utf-8 -*-
"""
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

import os
import sys
import logging

# QT classes
from qtpy import QtGui, QtCore, QtWebKit, QtWidgets
# Font Awesome icons for QT
import qtawesome as qta
# Mimetypes for file type recognition
import mimetypes
# OSF connection interface
import connection as osf
# For performing HTTP requests
import requests

class LoginWindow(QtWebKit.QWebView):
	""" A Login window for the OSF """
	# Login event is emitted after successfull login
	
	def __init__(self):
		""" Constructor """
		super(LoginWindow, self).__init__()
		
		# Create Network Access Manager to listen to all outgoing
		# HTTP requests. Necessary to work around the WebKit 'bug' which
		# causes it drop url fragments, and thus the access_token that the
		# OSF Oauth system returns
		self.nam = self.page().networkAccessManager()
		
		# Connect event that is fired after an URL is changed
		# (does not fire on 301 redirects, hence the requirement of the NAM)
		self.urlChanged.connect(self.check_URL)
	
		# Connect event that is fired if a HTTP request is completed.
		self.nam.finished.connect(self.checkResponse)
		
	def checkResponse(self,reply):
		"""Callback function for NetworkRequestManager.finished event
		
		Parameters
		----------
		reply : The HTTPResponse object provided by NetworkRequestManager
		"""
		request = reply.request()
		# Get the HTTP statuscode for this response
		statuscode = reply.attribute(request.HttpStatusCodeAttribute)
		# The accesstoken is given with a 302 statuscode to redirect
		
		if statuscode == 302:
			redirectUrl = reply.attribute(request.RedirectionTargetAttribute)
			if redirectUrl.hasFragment():
				r_url = redirectUrl.toString()
				if osf.redirect_uri in r_url:
					logging.info("Token URL: {}".format(r_url))
					self.token = osf.parse_token_from_url(r_url)
					if self.token:
						self.close()
		
	def check_URL(self, url):
		""" Callback function for urlChanged event.
		
		Parameters
		----------
		command : url
			New url, provided by the urlChanged event
		
		"""
		new_url = url.toString()
		
		if not osf.base_url in new_url and not osf.redirect_uri in new_url:
			logging.warning("URL CHANGED: Unexpected url: {}".format(url))
			
class UserBadge(QtWidgets.QWidget):
	""" A Widget showing the logged in user """
	
	# Class variables
	
	# Size of avatar and osf logo display image
	image_size = QtCore.QSize(50,50)
	# Login and logout events
	logout_request = QtCore.pyqtSignal()
	login_request = QtCore.pyqtSignal()
	# button texts
	login_text = "Log in to OSF"
	logout_text = "Log out"
	
	def __init__(self):
		""" Constructor """
		super(UserBadge, self).__init__()

		# Set up general window
		self.resize(200,40)
		self.setWindowTitle("User badge")
		# Set Window icon
		osf_logo = os.path.abspath('../../resources/img/cos-white2.png')

		if not os.path.isfile(osf_logo):
			print("ERROR: OSF logo not found at {}".format(osf_logo))

		self.osf_logo_pixmap = QtGui.QPixmap(osf_logo).scaled(self.image_size)
		
		osf_icon = QtGui.QIcon(osf_logo)
		self.setWindowIcon(osf_icon)
		
		## Set up labels
		# User's name
		self.user_name = QtWidgets.QLabel()
		# User's avatar
		self.avatar = QtWidgets.QLabel()
		
		# Login button
		self.statusbutton = QtWidgets.QPushButton(self)
		self.statusbutton.clicked.connect(self.__handle_click)
		
		# Determine content of labels:
		self.check_user_status()
		
		# Set up layout
		grid = QtWidgets.QGridLayout()
		grid.setSpacing(5)
		grid.addWidget(self.avatar,1,0)
		
		login_grid = QtWidgets.QGridLayout()
		login_grid.setSpacing(5)
		login_grid.addWidget(self.user_name,1,1)
		login_grid.addWidget(self.statusbutton,2,1)
		
		grid.addLayout(login_grid,1,1)
		self.setLayout(grid)
	
	def __handle_click(self):
		button = self.sender()
		logging.info("Button {} clicked".format(button.text()))
		if button.text() == self.login_text:
			self.login_request.emit()
		elif button.text() == self.logout_text:
			button.setText("Logging out...")
			QtCore.QCoreApplication.instance().processEvents()
			self.logout_request.emit()
		
	def handle_login(self):
		""" Callback function for EventDispatcher when a login event is detected """
		self.check_user_status()
			
	def handle_logout(self):
		""" Callback function for EventDispatcher when a logout event is detected """
		self.check_user_status()			
			
	def check_user_status(self):
		""" Checks the current status of the user and adjusts the contents of 
		the badge accordingly."""
		
		if osf.is_authorized():
			# Request logged in user's info
			self.user = osf.get_logged_in_user()
			# Get user's name
			full_name = self.user["data"]["attributes"]["full_name"]
			# Download avatar image from the specified url
			avatar_url = self.user["data"]["links"]["profile_image"]
			avatar_img = requests.get(avatar_url).content
			pixmap = QtGui.QPixmap()
			pixmap.loadFromData(avatar_img)
			pixmap = pixmap.scaled(self.image_size)
			
			# Update sub-widgets
			self.user_name.setText(full_name)
			self.avatar.setPixmap(pixmap)
			self.statusbutton.setText(self.logout_text)
		else:
			self.user = None
			self.user_name.setText("")
			self.avatar.setPixmap(self.osf_logo_pixmap)
			self.statusbutton.setText(self.login_text)
			

class ProjectExplorer(QtWidgets.QWidget):
	""" An explorer of the current user's OSF account """
	
	preview_size = QtCore.QSize(150,150)
	
	def __init__(self, *args, **kwars):
		""" Constructor """
		super(ProjectExplorer, self).__init__(*args, **kwars)
		
		self.setWindowTitle("Project explorer")
		self.resize(800,500)
		# Set Window icon
		osf_logo = os.path.abspath('../../resources/img/cos-white2.png')
		if not os.path.isfile(osf_logo):
			print("ERROR: OSF logo not found at {}".format(osf_logo))
		osf_icon = QtGui.QIcon(osf_logo)
		self.setWindowIcon(osf_icon)
		
		# globally accessible items
		self.tree = ProjectTree()
		self.properties_grid = self.__create_properties_pane()
		self.image_space = QtWidgets.QLabel()
		self.image_space.setAlignment(QtCore.Qt.AlignCenter)
		
		# Create layouts
		hbox = QtWidgets.QHBoxLayout(self)
		
		# Grid layout for the info consisting of an image space and the
		# properties grid
		info_grid = QtWidgets.QGridLayout()
		info_grid.setSpacing(5)
		info_grid.addWidget(self.image_space,1,1)
		info_grid.addLayout(self.properties_grid,2,1)
		
		# The widget to hold the infogrid
		info_frame = QtWidgets.QWidget()
		info_frame.resize(400,250)
		info_frame.setLayout(info_grid)
		
		splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
		splitter.addWidget(self.tree)
		splitter.addWidget(info_frame)
		
		hbox.addWidget(splitter)
		self.setLayout(hbox)
		
		# Event connections
		self.tree.itemClicked.connect(self.item_clicked)
		
	def __create_properties_pane(self):
		# Box to show the properties of the selected item
		properties_grid = QtWidgets.QGridLayout()
		properties_grid.setSpacing(5)
		
		nameLabel = QtWidgets.QLabel('Name')
		typeLabel = QtWidgets.QLabel('Type')
		
		self.nameValue = QtWidgets.QLabel('')
		self.typeValue = QtWidgets.QLabel('')
		
		# Labels
		properties_grid.addWidget(nameLabel,1,1)
		properties_grid.addWidget(typeLabel,2,1)
		
		# Values
		properties_grid.addWidget(self.nameValue,1,2)
		properties_grid.addWidget(self.typeValue,2,2)
		
		return properties_grid
		
		
	def item_clicked(self,item,col):
		data = item.data
		if data['type'] == 'nodes':
			name = data["attributes"]["title"]
			kind = data["attributes"]["category"]
		if data['type'] == 'files':
			name = data["attributes"]["name"]
			kind = data["attributes"]["kind"]

		pm = self.tree.get_icon(kind, name).pixmap(self.preview_size)
		self.image_space.setPixmap(pm)
		
		# Set name
		self.nameValue.setText(name)
		# Set label
		self.typeValue.setText(kind)
		
		
	def handle_login(self):
		self.tree.handle_login()
		
	def handle_logout(self):
		""" Callback function for EventDispatcher when a logout event is detected """
		self.tree.handle_logout()
		self.image_space.setPixmap(QtGui.QPixmap())
		self.nameValue.setText("")
		self.typeValue.setText("")
		
			
class ProjectTree(QtWidgets.QTreeWidget):
	""" A tree representation of projects and files on the OSF for the current user
	in a treeview widget"""
	
	def __init__(self, *args, **kwars):
		""" Constructor """
		super(ProjectTree, self).__init__(*args, **kwars)
		
		# Set up general window
		self.resize(400,500)
		
		# Set Window icon
		osf_logo = os.path.abspath('../../resources/img/cos-white2.png')
		if not os.path.isfile(osf_logo):
			print("ERROR: OSF logo not found at {}".format(osf_logo))
		osf_icon = QtGui.QIcon(osf_logo)
		self.setWindowIcon(osf_icon)
		
		# Set column labels
		self.setHeaderLabels(["Name","Kind"])
		self.setColumnWidth(0,300)
		
		# Event handling
		self.itemExpanded.connect(self.set_expanded_icon)
		self.itemCollapsed.connect(self.set_collapsed_icon)
		
		self.setIconSize(QtCore.QSize(20,20))
		
	def set_expanded_icon(self,item):
		if item.data['type'] == 'files' and item.data['attributes']['kind'] == 'folder':
			item.setIcon(0,self.get_icon('folder-open',item.data['attributes']['name']))
		
	def set_collapsed_icon(self,item):
		if item.data['type'] == 'files' and item.data['attributes']['kind'] == 'folder':
			item.setIcon(0,self.get_icon('folder',item.data['attributes']['name']))
		

	def get_icon(self, datatype, name):
		""" 
		Retrieves the icon for a certain object (project, folder) or filetype.
		Uses mimetypes to determine the file type.
		
		Parameters
		----------
		datatype : string
			The kind of object, which can be project, folder or file
		name : string
			The name of the object, which is the project, folder or file name
			
		Returns
		-------
		QIcon : The icon for the current file/objec type """
		
		providers = {
			'osfstorage':'fa.connectdevelop',
			'github':'fa.github',
			'dropbox':'fa.dropbox',
			'googledrive':'fa.google'
		}
		
		if datatype == 'project':
			icon = 'fa.cubes'
		elif datatype == "folder":
			if name in providers:
				icon = providers[name]
			else:
				icon = 'fa.folder-o'
		elif datatype == "folder-open":
			if name in providers:
				icon = providers[name]
			else:
				icon = 'fa.folder-open-o'
		elif datatype == "file":
			filetype, encoding = mimetypes.guess_type(name)
			if filetype:
				if "image" in filetype:
					icon = 'fa.file-image-o'
				elif "pdf" in filetype:
					icon = 'fa.file-pdf-o'
				elif "text/x-" in filetype:
					icon = 'fa.file-code-o'
				elif "text/plain" in filetype:
					icon = 'fa.file-text-o'
				elif "msword" in filetype or \
					"officedocument.wordprocessingml" in filetype or \
					"opendocument.text" in filetype:
					icon = 'fa.file-word-o'
				elif "powerpoint" in filetype or \
					"presentation" in filetype:
					icon = 'fa.file-powerpoint-o'
				elif "excel" in filetype or \
					"spreadsheet" in filetype:
					icon = 'fa.file-excel-o'				
				elif "zip" in filetype or "x-tar" in filetype\
					or "compressed" in filetype:
					icon = 'fa.file-archive-o'
				elif "video" in filetype:
					icon = 'fa.file-video-o'
				elif "audio" in filetype:
					icon = 'fa.file-video-o'
				else:
					icon = 'fa.file-o'
		else:
			icon = 'fa.file-o'
		return qta.icon(icon)

	def populate_tree(self, entrypoint, parent=None):
		""" 
		Populates the tree with content retrieved from a certain entrypoint, 
		specified as an api endpoint of the OSF, such a a project or certain 
		folder inside a project. The JSON representation that the api endpoint 
		returns is used to build the tree contents.
		
		Parameters
		----------
		entrypoint : string
			uri to the OSF api from where the 
		parent : QtWidgets.QTreeWidgetItem (options)
			The parent item to which the generated tree should be attached.
			Is mainly used for the recursiveness that this function implements.
			If not specified the invisibleRootItem() is used as a parent.
			
		Returns
		-------
		list : The list of tree items that have just been generated """
		
		osf_response = osf.direct_api_call(entrypoint)
		treeItems = []

		if parent is None:
			parent = self.invisibleRootItem()

		for entry in osf_response["data"]:
			if entry['type'] == 'nodes':
				name = entry["attributes"]["title"]
				kind = entry["attributes"]["category"]
			if entry['type'] == 'files':
				name = entry["attributes"]["name"]
				kind = entry["attributes"]["kind"]

			item = QtWidgets.QTreeWidgetItem(parent,[name,kind])
			icon = self.get_icon(kind, name)
			item.setIcon(0,icon)
			item.data = entry

			if kind in ["project","folder"]:
				next_entrypoint = entry['relationships']['files']['links']['related']['href']
				children = self.populate_tree(next_entrypoint, item)	
				item.addChildren(children)
			treeItems.append(item)
		return treeItems	
		
	#
	# Event handling functions required by EventDispatcher	
	#
		
	def handle_login(self):
		""" Callback function for EventDispatcher when a login event is detected """
		logged_in_user = osf.get_logged_in_user()
		# Get url to user projects. Use that as entry point to populate the tree
		user_nodes_api_call = logged_in_user['data']['relationships']['nodes']['links']['related']['href']
		self.populate_tree(user_nodes_api_call)
		
	def handle_logout(self):
		""" Callback function for EventDispatcher when a logout event is detected """
		self.clear()
		
		
		
		
		
		
		
		
		
		
		
		
		

		
		
	
	