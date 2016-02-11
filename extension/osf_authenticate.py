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

# Import Python 3 compatibility functions
from libopensesame.py3compat import *

## END TEMP ###
__author__ = u"Daniel Schreij"
__license__ = u"Apache2"

# Module for easy OAuth2 usage, based on the requests library,
# which is the easiest way to perform HTTP requests.
from requests_oauth2 import OAuth2

# Create an OAuth2 handler to which requests are redirected that need authorization
oauth2_handler = OAuth2(
	client_id = u"cbc4c47b711a4feab974223b255c81c1", 
	client_secret = u"YIFLis1dq3Cnr3RenKFHXn03RtV1hwoeFKnycs91", 
	site = u"https://test-accounts.osf.io/", 
	redirect_uri = u"https://www.getpostman.com/oauth2/callback", 
	authorization_url=u'oauth2/authorize', 
	token_url=u'oauth2/token'
)


