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


# Installation

QtIPy requires PyQt5. Compatible with both Python2.7 and Python3.4.

Best installed via PyPi:

    pip install qtipy
    
Then from a command line run:

    QtIPy
    
For Mac users a launcher `.app` is available for download from [here](http://download.martinfitzpatrick.name/QtIPy.app.zip). Install
as above, then download the `.app` and drag to your dock. Click to launch QtIPy!

Backend running is based on https://github.com/paulgb/runipy/


