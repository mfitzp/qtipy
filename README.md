# QtIPy

A Qt-based automator for IPython notebooks. Attached triggers to files and folders and 
automatically run notebooks on file changes, or run a IPython notebook on a timer.

A dictionary of variables describing the current state is passed to the script (variable `qtipy`)
and can be read to direct script output to particular folders. Watching a folder optionally allows
iterating over all the files in a folder, which are also in passed to the script for processing. 

QtIPy therefore allows you to automatically process data files, generate figures, etc. 
without lifting a finger.

Automator sets and be saved and loaded for future use.

![Screenshot](https://raw.githubusercontent.com/mfitzp/qtipy/master/qtipy-screenshot.png)

Requires PyQt5. Compatible with both Python2.7 and Python3.4.

Backend running is based on https://github.com/paulgb/runipy/

