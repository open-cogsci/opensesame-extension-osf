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

from libopensesame import debug
from libqtopensesame.extensions import base_extension

__author__ = u"Daniel Schreij"
__license__ = u"Apache2"

# Use Python3 string instead of deprecated QString
class OpenScienceFramework(base_extension):
	def __init__(self):
		pass
	
	def activate(self):
		debug.msg(u'OSF extension activated')
	
	def event_save_experiment(self, path):
		debug.msg(u'OSF: Event caught: save_experiment(path=%s)' % path)
		
	
	