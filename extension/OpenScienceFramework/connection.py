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

# Module for easy OAuth2 usage, based on the requests library,
# which is the easiest way to perform HTTP requests.

# OAuth2Session object
from requests_oauthlib import OAuth2Session
# Mobile application client that does not need a client_secret
from oauthlib.oauth2 import MobileApplicationClient
# Easier function decorating
from functools import wraps

#%%---------------------- Main configuration settings --------------------------
client_id = "cbc4c47b711a4feab974223b255c81c1"
redirect_uri = "https://www.getpostman.com/oauth2/callback"

# Generate correct URLs
base_url = "https://test-accounts.osf.io/"
auth_url = base_url + "oauth2/authorize"
token_url = base_url + "oauth2/token"

api_base_url = "https://test-api.osf.io/v2/"


#%%-----------------------------------------------------------------------------

mobile_app_client = MobileApplicationClient(client_id)

# Create an OAuth2 session for the OSF
session = OAuth2Session(
	client_id, 
	mobile_app_client,
	scope="osf.full_write", 
	redirect_uri=redirect_uri,
)

api_calls = {
	"logged_in_user":"users/me",
}

def get_api_endpoint(command):
	return api_base_url + api_calls[command]

def get_authorization_url():
	""" Generate the URL with which one can authenticate at the OSF and allow 
	OpenSesame access to his or her account."""
	return session.authorization_url(auth_url)
	
def parse_token_from_url(url):
	""" Parse token from url fragment """
	return session.token_from_fragment(url)
	
def is_authorized():
	""" Convenience function simply returning OAuth2Session.authorized. """
	return session.authorized
	
def requires_authentication(func):
	""" Decorator function which checks if a user is authenticated before he
	performs the desired action. """
	
	@wraps(func)
	def func_wrapper(*args, **kwargs):
		if not is_authorized():
			print("You are not authenticated. Please log in first.")
			return False
		return func(*args, **kwargs)
	return func_wrapper
	
@requires_authentication
def logged_in_user():
	return session.get(get_api_endpoint("logged_in_user")).json()
		
if __name__ == "__main__":
	print(get_authorization_url())
	
	
	
	


