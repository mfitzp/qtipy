from __future__ import unicode_literals
import logging

import re
import os
import errno


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def find_packager():

    import sys
    frozen = getattr(sys, 'frozen', None)

    if not frozen:
        # COULD be certain cx_Freeze options or bundlebuilder, nothing to worry about though
        return None
    elif frozen in ('dll', 'console_exe', 'windows_exe'):
        return 'py2exe'
    elif frozen in ('macosx_app', ):
        return 'py2app'
    elif frozen is True:
        return True  # it doesn't ALWAYS set this return 'cx_Freeze' 
    else:
        return '<unknown packager: %r>' % (frozen, )

# Get current running script folder (Pathomx app folder)
pkg = find_packager()
if pkg == None:
    scriptdir = os.path.dirname(os.path.realpath(__file__))  # .rpartition('/')[0]
elif pkg == True:
    scriptdir = os.path.dirname(sys.executable)
elif pkg == 'py2app':
    #'/Applications/Pathomx.app/Contents/Resources'
    scriptdir = os.environ['RESOURCEPATH']
elif pkg == 'py2exe':
    scriptdir = os.path.dirname(str(sys.executable, sys.getfilesystemencoding()))
