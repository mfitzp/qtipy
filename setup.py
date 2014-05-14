#!/usr/bin/env python
# coding=utf-8
import sys
from copy import copy

from setuptools import setup, find_packages

setup(

    name='QtIPy',
    version="0.1.8",
    author='Martin Fitzpatrick',
    author_email='martin.fitzpatrick@gmail.com',
    url='https://github.com/mfitzp/qtipy',
    download_url='https://github.com/mfitzp/qtipy/zipball/master',
    description='The data automator! Auto-run IPython notebooks on file triggers. Qt interface.',
    long_description='QtIPy is a simple tool for auto-running IPython scripts on file or folder changes. Use it \
    - a simple way to automate your analysis worflows!',

    packages=find_packages(),
    include_package_data=True,
    package_data={
        'pyqti': ['*.txt', '*.rst', '*.md', 'icons/*'],
    },
    exclude_package_data={'': ['README.txt']},
    entry_points={
        'gui_scripts': [
            'QtIPy = QtIPy.cmd:main',
        ]
    },
        
    install_requires=[
        'pyqtconfig>=0.1',
        'runipy>=0.0.9',
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
