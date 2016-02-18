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
import inspect

# Required QT classes
from PyQt4 import QtGui, QtCore

# Oauth2 connection to OSF
import connection as osf

# Widgets
import widgets


class EventDispatcher(object):
	# List of possible events this dispatcher can emit
	events = ["login","logout"]	
	
	def __init__(self):
		super(EventDispatcher, self).__init__()
		self.__listeners = []
	
	def __check_events(self,item):
		"""Checks if the passed object has the required handler functions.
		Args:
			item - the object to check
		Raises:
			NameError - if the object does not have the required event handling 
			functions
		"""
		for event in self.events:
			if not hasattr(item,"handle_"+event) or not inspect.ismethod(getattr(item,"handle_"+event)):
				raise NameError("{} does not have the required function {}".\
					format(item.__name__, "handle_"+event))
	
	def add(self, obj):
		""" Add (a) new object(s) to the list of objects listening for the events 
	
		Args:
			obj - the listener to add. Can be a single listener or a list of listeners.
		"""
		# If the object passed is a list, check if each object in the list has the
		# required event handling functions
		if type(obj) == list:
			for item in obj:
				self.__check_events(item)
			self.__listeners.extend(obj)
		else:
		# If a single object is passed, check if it has the required functions
			self.__check_events(obj)
			self.__listeners.append(obj)
		return self
			
	def remove(self,obj):
		for item in self.__listeners:
			# Delete by object reference
			if obj is item:
				del self.__listeners[self.__listeners.index(item)]
			# Delete by index
			if type(obj) == int:
				del self.__listeners[obj]
		return self
			
	def get_listeners(self):
		return self.__listeners
		
	def dispatch(self,event):
		if not event in self.events:
			raise ValueError("Unknown event '{}'".format(event))
			
		for item in self.__listeners:
			# Check here again, just to be sure
			if not hasattr(item,"handle_"+event) or not inspect.ismethod(getattr(item,"handle_"+event)):
				raise NameError("{} does not have the required function {}".\
					format(item.__name__, "handle_"+event))
			# Call the function!
			getattr(item,"handle_"+event)()	
			
class TestListener(object):
	def handle_login(self):
		print("Login event received")
		
	def handle_logout(self):
		print("logout event received")
		
if __name__ == "__main__":
	""" Test if user can connect to OSF. Opens up a browser window in the form
	of a QWebView window to do so."""
	# Import QT libraries

	app = QtGui.QApplication(sys.argv)
	browser = widgets.LoginWindow()
	user_badge = widgets.UserBadge()
	dispatcher = EventDispatcher()
	
	auth_url, state = osf.get_authorization_url()
	print("Generated authorization url: {}".format(auth_url))
	
	# Set up browser
	browser_url = QtCore.QUrl.fromEncoded(auth_url)
	browser.load(browser_url)
	browser.show()
	
	# Set up user badge
	user_badge.move(1000,100)
	user_badge.show()

	# Connect login events of browser to EventDispatcher's dispatch function	
	browser.logged_in.connect(dispatcher.dispatch)
	
	tl = TestListener() # To be removed later	
	dispatcher.add([user_badge, tl])
	
	exitcode = app.exec_()
	print("App exiting with code {}".format(exitcode))
	#sys.exit(exitcode)
	



