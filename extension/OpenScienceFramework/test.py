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
import logging
logging.basicConfig(level=logging.INFO)

# Required QT classes
from PyQt4 import QtGui, QtCore

# Oauth2 connection to OSF
import connection as osf

# Widgets
import widgets

# Event dispatcher and listeners
from util import EventDispatcher, TestListener, TokenFileListener

def showLoginWindow(browser):
	auth_url, state = osf.get_authorization_url()
	logging.info("Generated authorization url: {}".format(auth_url))
	
	# Set up browser
	browser_url = QtCore.QUrl.fromEncoded(auth_url)
	browser.load(browser_url)
	browser.show()
		
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
	osf.logged_in = dispatcher.dispatch_login
	# Dispatch logout events
	osf.logged_out = dispatcher.dispatch_logout
	
	tl = TestListener() # To be removed later	
	tfl = TokenFileListener(tokenfile, osf)
	dispatcher.add([user_badge, tl, tfl])
	
	# Connect click on user badge logout button to osf logout action
	user_badge.logout_request.connect(osf.logout)
	user_badge.login_request.connect(osf.login)
	
	if os.path.isfile(tokenfile):
		with open(tokenfile,"r") as f:
			token = json.loads(f.read())
			
		# Check if token has not yet expired
		if token["expires_at"] > time.time():
			# Load the token information in the session object, but check its
			# validity!
			osf.session.token = token
			# See if a request succeeds without errors
			try:
				osf.logged_in_user()
			except osf.TokenError as e:
				logging.error(e.strerror)
				osf.reset_session()
				os.remove(tokenfile)
		else:
			logging.info("Token expired; need log-in")
	
	if not osf.is_authorized():
		showLoginWindow(browser)
	else:
		dispatcher.dispatch("login")
	
	exitcode = app.exec_()
	logging.info("App exiting with code {}".format(exitcode))
	#sys.exit(exitcode)
	



