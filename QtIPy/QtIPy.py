# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import logging

frozen = getattr(sys, 'frozen', None)
if frozen:
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)

import os
import re

from .qt import *
from . import utils
from .translate import tr

import requests
import subprocess

sys.setcheckinterval(1000)

from distutils.version import StrictVersion

VERSION_STRING = '0.0.1'


import os,sys,time

from Queue import Empty

try:
    from IPython.kernel import KernelManager
except ImportError:
    from IPython.zmq.blockingkernelmanager import BlockingKernelManager as KernelManager

from IPython.nbformat.current import reads, NotebookNode
from IPython.nbconvert.exporters import export as IPyexport
from IPython.nbconvert.exporters import HTMLExporter
from IPython.utils.ipstruct import Struct
from runipy.notebook_runner import NotebookRunner

_w = None

# Generic configuration dialog handling class
class GenericDialog(QDialog):
    '''
    A generic dialog wrapper that handles most common dialog setup/shutdown functions.
    
    Support for config, etc. to be added for auto-handling widgets and config load/save. 
    '''

    def __init__(self, parent, buttons=['ok', 'cancel'], **kwargs):
        super(GenericDialog, self).__init__(parent, **kwargs)

        self.sizer = QVBoxLayout()
        self.layout = QVBoxLayout()

        QButtons = {
            'ok': QDialogButtonBox.Ok,
            'cancel': QDialogButtonBox.Cancel,
        }
        Qbtn = 0
        for k in buttons:
            Qbtn = Qbtn | QButtons[k]

        # Setup default button configurations etc.
        self.buttonBox = QDialogButtonBox(Qbtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def finalise(self):
        self.sizer.addLayout(self.layout)
        self.sizer.addWidget(self.buttonBox)

        # Set dialog layout
        self.setLayout(self.sizer)
        

class AutomatonDialog(GenericDialog):
    
    def __init__(self, parent, **kwargs):
        super(AutomatonDialog, self).__init__(parent, **kwargs)
        self.setWindowTitle("Edit Automaton")
    
        gb = QGroupBox('Watch target (file/folder)')
        grid = QGridLayout()

        self.watcher_path_le = QLineEdit()
        grid.addWidget(self.watcher_path_le, 0, 0, 1,2)
        self.watcher_path_btn = QToolButton()
        self.watcher_path_btn.setIcon( QIcon(os.path.join(utils.scriptdir, 'icons', 'folder-horizontal-open.png')) )
        self.watcher_path_btn.clicked.connect( lambda: self.onFileBrowse(self.watcher_path_le) )
        grid.addWidget(self.watcher_path_btn, 0, 2, 1,1)

        grid.addWidget(QLabel('Hold trigger'), 1, 0)
        self.watcher_hold_sb = QSpinBox()
        self.watcher_hold_sb.setSuffix(' secs')
        grid.addWidget(self.watcher_hold_sb, 1, 1)


        gb.setLayout(grid)

        self.layout.addWidget(gb)

        gb = QGroupBox('IPython Notebook (*.ipynb)')
        grid = QGridLayout()
        self.notebook_path_le = QLineEdit()
        grid.addWidget(self.notebook_path_le, 0, 0, 1,2)
        self.notebook_path_btn = QToolButton()
        self.notebook_path_btn.setIcon( QIcon(os.path.join(utils.scriptdir, 'icons', 'folder-horizontal-open.png')) )
        self.notebook_path_btn.clicked.connect( lambda: self.onFileBrowse(self.notebook_path_le) )
        grid.addWidget(self.notebook_path_btn, 0, 2, 1,1)
        gb.setLayout(grid)
        
        self.layout.addWidget(gb)
        
        self.finalise()
        
    def onFileBrowse(self, t):
        global _w
        filename, _ = QFileDialog.getOpenFileName(_w, "Load IPython notebook", '', "IPython Notebooks (*.ipynb);;All files (*.*)")
        if filename:
            t.setText( filename )

    def onFileFolderBrowse(self, t):
        global _w
        filename, _ = QFileDialog.getOpenFileName(_w, "Load IPython notebook", '', "IPython Notebooks (*.ipynb);;All files (*.*)")
        if filename:
            t.setText( filename )
        
    def sizeHint(self):
        return QSize(400,200)     


class AutomatonListDelegate(QAbstractItemDelegate):

    def paint(self, painter, option, index):
        # GET TITLE, DESCRIPTION AND ICON
        ic = QIcon(index.data(Qt.DecorationRole))
        automaton = index.data(Qt.UserRole)
        
        watch = automaton.watcher_path
        notebook = automaton.notebook_path
        
        f = QFont()
        f.setPointSize(10)
        painter.setFont(f)

        if option.state & QStyle.State_Selected:
            painter.setPen(QPalette().highlightedText().color())
            painter.fillRect(option.rect, QBrush(QPalette().highlight().color()))
        else:
            painter.setPen(QPalette().text().color())

        icw = QIcon(os.path.join(utils.scriptdir, 'icons', 'folder-horizontal-open-sm.png') )
        icw.paint(painter, option.rect.adjusted(10, 0, -2, -34), Qt.AlignVCenter | Qt.AlignLeft)
        
        icn = QIcon(os.path.join(utils.scriptdir, 'icons', 'qtipy-sm.png') )
        icn.paint(painter, option.rect.adjusted(10, 20, -2, -34), Qt.AlignVCenter | Qt.AlignLeft)

        r = option.rect.adjusted(26, 5, 0, 0)
        pen = QPen()
        pen.setColor(QColor('black'))

        # WATCH PATH
        painter.setPen(pen)
        painter.drawText(r.left(), r.top(), r.width(), r.height(), Qt.AlignLeft, watch)

        # NOTEBOOK
        r = option.rect.adjusted(26, 22, 0, 0)
        painter.drawText(r.left(), r.top(), r.width(), r.height(), Qt.AlignLeft, notebook)
        

    def sizeHint(self, option, index):
        return QSize(200, 60)


class Automaton(QStandardItem):

    notebook = None
    notebook_path = '~'

    watcher = QFileSystemWatcher()
    watcher_path = '~'
    
    def __init__(self, *args, **kwargs):
        super(Automaton, self).__init__(*args, **kwargs)
        
        self.setData(self, Qt.UserRole)

        self.runner = NotebookRunner(None, pylab=True, mpl_inline=True)

    
    def load_notebook(self, filename):
        with open(filename) as f:
            nb = reads(f.read(), 'json')

        if nb:
            self.notebook = nb   

    def trigger(self, e):
        # Filesystemwatcher triggered
        # Get the file and folder information; make available in vars object for run
        pass
            
    def run(self, vars={}):
        vars['path'] = '~'
        self.run_notebook(self.notebook, vars)

    def run_notebook(self, nb, vars={}):
        start = nb['worksheets'][0]['cells']
        start.insert(0, Struct(**{
            'cell_type': 'code',
            'language': 'python',
            'outputs': [],
            'collapsed': False,
            'prompt_number': -1,
            'input': 'a = "YAY!"',
            'metadata': {},
        }) )
        self.runner.nb = nb
        self.runner.run_notebook()
        
        output, resources = IPyexport(HTMLExporter, self.runner.nb)
        with open("/Users/mxf793/test.html","w") as f:
            f.write(output)


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.menuBars = {
            'file': self.menuBar().addMenu(tr('&File')),
            'edit': self.menuBar().addMenu(tr('&Edit')),
            'control': self.menuBar().addMenu(tr('&Control')),
        }        
        
        t = self.addToolBar('File')
        t.setIconSize(QSize(16, 16))

        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'folder-horizontal-open.png')), tr('Load automatons'), self)
        action.setStatusTip('Load automatons')
        action.triggered.connect( self.load_automatons )
        t.addAction(action)
        self.menuBars['file'].addAction(action)

        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'disk.png')), tr('Save automatons'), self)
        action.setStatusTip('Save automatons')
        action.triggered.connect( self.load_automatons )
        t.addAction(action)
        self.menuBars['file'].addAction(action)

        t = self.addToolBar('Edit')
        t.setIconSize(QSize(16, 16))

        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'plus-circle.png')), tr('Add automaton'), self)
        action.setStatusTip('Add new automaton')
        action.triggered.connect( self.add_new_automaton )
        t.addAction(action)
        self.menuBars['edit'].addAction(action)

        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'edit-diff.png')), tr('Edit automaton'), self)
        action.setStatusTip('Edit automaton')
        action.triggered.connect( self.edit_automaton )
        t.addAction(action)
        self.menuBars['edit'].addAction(action)


        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'cross.png')), tr('Delete automaton'), self)
        action.setStatusTip('Delete automaton')
        action.triggered.connect( self.delete_automaton )
        t.addAction(action)
        self.menuBars['edit'].addAction(action)

        t = self.addToolBar('Control')
        t.setIconSize(QSize(16, 16))

        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'control.png')), tr('Enable'), self)
        action.setStatusTip('Enable automaton')
        action.triggered.connect( self.enable_automaton )
        t.addAction(action)
        self.menuBars['control'].addAction(action)

        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'control-pause.png')), tr('Pause'), self)
        action.setStatusTip('Pause automaton')
        action.triggered.connect( self.pause_automaton )
        t.addAction(action)
        self.menuBars['control'].addAction(action)

        
        self.viewer = QListView()
        #self.viewer.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.viewer.setItemDelegate(AutomatonListDelegate(self.viewer))
        self.automatons = QStandardItemModel(self.viewer)
        self.viewer.setModel(self.automatons)
        
        self.setCentralWidget( self.viewer )

        self.setWindowTitle("QtIPy: The data automator")
        self.statusBar().showMessage(tr('Ready'))

        self.setMinimumSize( QSize(400,500) )
        self.show()
        
    def add_new_automaton(self):
        '''
        Define a new automaton and add to the list
        
        Show a dialog with options to:
        - define the notebook file to use (.pylnb)
        - define the file, folder or other to watch
        - define the output folder/file pattern
        - set config settings
        '''
        automaton = Automaton()
        self.automatons.appendRow(automaton)
        lastitem = self.automatons.item( self.automatons.rowCount()-1 )
        self.viewer.setCurrentIndex( lastitem.index() )
        self.edit_automaton()
        
    def edit_automaton(self):
        '''
        
        
        '''
        try:
            automaton = self.automatons.itemFromIndex( self.viewer.selectionModel().currentIndex() )
        except:
            return
        
        dlg = AutomatonDialog(self)
        dlg.config = {}
        if dlg.exec_():
            automaton.notebook_path = dlg.notebook_path_le.text()
            automaton.watcher_path = dlg.watcher_path_le.text()
            
            automaton.watcher.removePaths( automaton.watcher.files() + automaton.watcher.directories() )
            automaton.watcher.addPath( automaton.watcher_path )
        
            automaton.load_notebook( automaton.notebook_path )
        
    def delete_automaton(self):
        '''
        '''
        automaton = self.viewer.selectionModel().selectedIndexes()[0]
        self.automatons.removeRows( automaton.row(), 1, QModelIndex() )
        
    def enable_automaton(self):
        '''
        '''
        automaton = self.automatons.item(0)
        automaton.run()
        
        pass

    def pause_automaton(self):
        '''
        '''
        pass
        
    def load_automatons(self):
        '''
        '''
        pass

    def save_automatons(self):
        '''
        '''
        pass
                    
    def sizeHint(self):
        return QSize(400,500)     

def main():
    # Create a Qt application
    app = QApplication(sys.argv)
    app.setStyle('fusion')

    app.setOrganizationName("QtIPy")
    app.setOrganizationDomain("martinfitzpatrick.name")
    app.setApplicationName("QtIPy")

    locale = QLocale.system().name()

    global _w
    _w = MainWindow()
    logging.info('Ready.')
    app.exec_()  # Enter Qt application main loop
    logging.info('Exiting.')
    
    sys.exit()

if __name__ == "__main__":
    main()
