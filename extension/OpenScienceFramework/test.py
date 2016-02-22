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

# Import basics
import sys
import os
import json
import time

# Required QT classes
from PyQt4 import QtGui, QtCore

# Oauth2 connection to OSF
import connection as osf

# Widgets
import widgets

# Event dispatcher
from util import EventDispatcher, TestListener
		
class TokenFileListener(object):
	def __init__(self,tokenfile):
		super(TokenFileListener,self).__init__()
		self.tokenfile = tokenfile
	
	def handle_login(self):
		if osf.session.token:
			tokenstr = json.dumps(osf.session.token)
			with open(self.tokenfile,'w') as f:
				f.write(tokenstr)
		else:
			print("Error, could not find authentication token")

	def handle_logout(self):
		if os.path.isfile(self.tokenfile):
			try:
				os.remove(self.tokenfile)
			except Exception as e:
				print("WARNING: {}".format(e.message))
		
			
		
if __name__ == "__main__":
	""" Test if user can connect to OSF. Opens up a browser window in the form
	of a QWebView window to do so."""
	# Import QT libraries

	app = QtGui.QApplication(sys.argv)
	user_badge = widgets.UserBadge()
	dispatcher = EventDispatcher()
	browser = widgets.LoginWindow()
	
	tokenfile = "token.json"	
	
	# Set up user badge
	user_badge.move(1100,100)
	user_badge.show()

	# Connect login events of browser to EventDispatcher's dispatch function	
	browser.logged_in.connect(dispatcher.dispatch)
	
	tl = TestListener() # To be removed later	
	tfl = TokenFileListener(tokenfile)
	dispatcher.add([user_badge, tl, tfl])
	
	if os.path.isfile(tokenfile):
		with open(tokenfile,"r") as f:
			token = json.loads(f.read())
			
		# Check if token has not yet expired
		if token["expires_at"] > time.time():
			osf.session.token = token
		else:
			print("Token expired; need log-in")
	
	if not osf.is_authorized():
		auth_url, state = osf.get_authorization_url()
		print("Generated authorization url: {}".format(auth_url))
		
		# Set up browser
		browser_url = QtCore.QUrl.fromEncoded(auth_url)
		browser.load(browser_url)
		browser.show()
	else:
		dispatcher.dispatch("login")
	
	exitcode = app.exec_()
	print("App exiting with code {}".format(exitcode))
	#sys.exit(exitcode)
	



