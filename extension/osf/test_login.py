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
		self.nam = self.page().networkAccessManager()
		self.nam.finished.connect(self.checkResponse)
		
	def checkResponse(self,reply):
		request = reply.request()
		# Get the HTTP statuscode for this response
		statuscode = reply.attribute(request.HttpStatusCodeAttribute)
		# The accesstoken is given with a 302 statuscode to redirect
		
		if statuscode == 302:
			redirectUrl = reply.attribute(request.RedirectionTargetAttribute)
			if redirectUrl.hasFragment():
				r_url = redirectUrl.toString()
				if osf.redirect_uri in r_url:
					self.token = osf.parse_token_from_url(r_url)
					if self.token:
						self.close()
						self.quit()
							
	def set_state(self,state):
		self.state = state
		
	def check_URL(self, url):
		new_url = url.toEncoded()
		
		if not osf.base_url in new_url:
			print("URL CHANGED: Unexpected url: {}".format(url))
		
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
	#sys.exit(exitcode)
	



