#!/usr/bin/env python

import os
import glob
import yaml
from setuptools import setup

with open('opensesame_extensions/OpenScienceFramework/info.yaml') as fd:
	d = yaml.load(fd)
version = d['version']
print('Version %s' % version)

def files(path):
	l = [fname for fname in glob.glob(path) if os.path.isfile(fname) \
		and not fname.endswith('.pyc')]
	print(l)
	return l


def data_files():
	"""
	desc:
		The OpenSesame extension are installed as additional data. Under Windows,
		there is no special folder to put these plug-ins in, so we skip this
		step.
	returns:
		desc:	A list of data files to include.
		type:	list
	"""

	return [
		("share/opensesame_extensions/OpenScienceFramework",
			files("opensesame_extensions/OpenScienceFramework/*")),
		]

setup(
	name="opensesame-extension-osf",
	version=version,
	description="OpenSesame OSF extension",
	author="Daniel Schreij",
	author_email="dschreij@gmail.com",
	url="https://github.com/dschreij/opensesame-osf",
	classifiers=[
		'Intended Audience :: Science/Research',
		'Topic :: Scientific/Engineering',
		'Environment :: MacOS X',
		'Environment :: Win32 (MS Windows)',
		'Environment :: X11 Applications',
		'License :: OSI Approved :: Apache Software License',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 3',
	],
	install_requires=[
		'python-qosf',
	],
	include_package_data=False,
	packages = [],
	data_files=data_files()
	)
print(data_files())
