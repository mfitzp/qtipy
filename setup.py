#!/usr/bin/env python
# coding=utf-8
import sys
from copy import copy

from setuptools import setup, find_packages


# Defaults for py2app / cx_Freeze
default_build_options=dict(
    packages=[
        'pyqtconfig',
        ],
    includes=[
        ],
    excludes=[
        ],
    )



setup(

    name='QtIPy',
    version="0.1",
    author='Martin Fitzpatrick',
    author_email='martin.fitzpatrick@gmail.com',
    url='https://github.com/mfitzp/qtipy',
    download_url='https://github.com/mfitzp/qtipy/zipball/master',
    description='The data automator! Auto-run IPython notebooks on file triggers. Qt interface.',
    long_description='QtIPy is a simple tool for auto-running IPython scripts on file or folder changes. Use it \
    - a simple way to automate your analysis worflows!',

    packages = find_packages(),
    include_package_data = True,
    package_data = {
        '': ['*.txt', '*.rst', '*.md'],
    },
    exclude_package_data = { '': ['README.txt'] },

    entry_points = {},

    install_requires = [
            ],

    keywords='bioinformatics research analysis science',
    license='GPL',
    classifiers=['Development Status :: 4 - Beta',
               'Natural Language :: English',
               'Operating System :: OS Independent',
               'Programming Language :: Python :: 2',
               'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
               'Topic :: Scientific/Engineering :: Bio-Informatics',
               'Topic :: Education',
               'Intended Audience :: Science/Research',
               'Intended Audience :: Education',
              ],

    options={},
    )
