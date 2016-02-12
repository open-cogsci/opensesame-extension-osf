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

__author__ = u"Daniel Schreij"
__license__ = u"Apache2"

# Import basics
import sys
import os

# Oauth2 connection to OSF
import osf

from PyQt4 import QtGui, QtCore, QtWebKit

class LoginWindow(QtWebKit.QWebView):
	""" A Login window for the OSF """
	
	def __init__(self):
		super(LoginWindow, self).__init__()
		self.state = None
		self.urlChanged.connect(self.check_URL)
		
	def set_state(self,state):
		self.state = state
		
	def load(self, url):
		print("Loading: {}".format(url))
		QtWebKit.QWebView.load(self,url)
		
	def check_URL(self, url):
		new_url = url.toString()
				
		if osf.base_url in new_url:
			print("Still in authentication process: {}".format(url))
		elif url.hasFragment():
			print("On token page: {}".format(url))
			self.token = osf.parse_token_from_url(new_url)
			print(self.token)
		else:
			print("Unexpected url: {}".format(url))
		
if __name__ == "__main__":
	""" Test if user can connect to OSF. Opens up a browser window in the form
	of a QWebView window to do so."""
	# Import QT libraries

	app = QtGui.QApplication(sys.argv)
	browser = LoginWindow()
	
	auth_url, state = osf.get_authorization_url()
	print("Generated authorization url: {}".format(auth_url))
	
	browser_url = QtCore.QUrl.fromEncoded(auth_url)
	browser.load(browser_url)
	browser.set_state(state)
	browser.show()

	exitcode = app.exec_()
	print("App exiting with code {}".format(exitcode))
	sys.exit(exitcode)
	



