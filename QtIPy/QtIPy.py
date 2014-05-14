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
from datetime import datetime

sys.setcheckinterval(1000)

from distutils.version import StrictVersion

VERSION_STRING = '0.0.1'

from pyqtconfig import ConfigManager

import os,sys,time

from Queue import Empty

try:
    from IPython.kernel import KernelManager
except ImportError:
    from IPython.zmq.blockingkernelmanager import BlockingKernelManager as KernelManager

from IPython.nbformat.current import reads, NotebookNode
from IPython.nbconvert.exporters import export as IPyexport
from IPython.nbconvert.exporters.export import exporter_map as IPyexporter_map

from IPython.utils.ipstruct import Struct
from runipy.notebook_runner import NotebookRunner


_w = None

MODE_MANUAL = 0
MODE_WATCH_FILES = 1
MODE_TIMER = 2

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
    
    mode_options = {
        'Manual': MODE_MANUAL,
        'Watch files or folders': MODE_WATCH_FILES,
        'Timer': MODE_TIMER,
    }
    
    
    def __init__(self, parent, **kwargs):
        super(AutomatonDialog, self).__init__(parent, **kwargs)
        self.setWindowTitle("Edit Automaton")
    
        self.config = ConfigManager()

        gb = QGroupBox('Mode')
        grid = QGridLayout()
        mode_cb = QComboBox()
        mode_cb.addItems( self.mode_options.keys() )
        self.config.add_handler('mode', mode_cb, mapper=self.mode_options)
        grid.addWidget(QLabel('Mode'), 0, 0)
        grid.addWidget(mode_cb, 0, 1)

        grid.addWidget(QLabel('Hold trigger'), 1, 0)
        watcher_hold_sb = QSpinBox()
        watcher_hold_sb.setRange(0, 60)
        watcher_hold_sb.setSuffix(' secs')
        self.config.add_handler('trigger_hold', watcher_hold_sb)

        grid.addWidget(watcher_hold_sb, 1, 1)
        gb.setLayout(grid)

        self.layout.addWidget(gb)
        
        gb = QGroupBox('Watch target (file/folder)')
        grid = QGridLayout()

        watched_path_le = QLineEdit()
        grid.addWidget(watched_path_le, 0, 0, 1,2)
        self.config.add_handler('watched_path', watched_path_le)
        
        watched_path_btn = QToolButton()
        watched_path_btn.setIcon( QIcon(os.path.join(utils.scriptdir, 'icons', 'folder-horizontal-open.png')) )
        watched_path_btn.clicked.connect( lambda: self.onFileBrowse(watched_path_le) )
        grid.addWidget(watched_path_btn, 0, 2, 1,1)
        gb.setLayout(grid)


        self.layout.addWidget(gb)

        gb = QGroupBox('IPython Notebook (*.ipynb)')
        grid = QGridLayout()
        notebook_path_le = QLineEdit()
        self.config.add_handler('notebook_path', notebook_path_le)
        grid.addWidget(notebook_path_le, 0, 0, 1,2)

        notebook_path_btn = QToolButton()
        notebook_path_btn.setIcon( QIcon(os.path.join(utils.scriptdir, 'icons', 'folder-horizontal-open.png')) )
        notebook_path_btn.clicked.connect( lambda: self.onNotebookBrowse(notebook_path_le) )
        grid.addWidget(notebook_path_btn, 0, 2, 1,1)
        gb.setLayout(grid)
        
        self.layout.addWidget(gb)
        
        gb = QGroupBox('Output')
        grid = QGridLayout()
        output_path_le = QLineEdit()
        self.config.add_handler('output_path', output_path_le)
        grid.addWidget(output_path_le, 0, 0, 1,2)
        
        notebook_path_btn = QToolButton()
        notebook_path_btn.setIcon( QIcon(os.path.join(utils.scriptdir, 'icons', 'folder-horizontal-open.png')) )
        notebook_path_btn.clicked.connect( lambda: self.onFolderBrowse(notebook_path_le) )
        grid.addWidget(notebook_path_btn, 0, 2, 1,1)

        export_cb = QComboBox()
        export_cb.addItems( IPyexporter_map.keys() )
        self.config.add_handler('output_format', export_cb)
        grid.addWidget(QLabel('Notebook output format'), 1, 0)
        grid.addWidget(export_cb, 1, 1)


        gb.setLayout(grid)

        self.layout.addWidget(gb)        
        
        self.finalise()
        
    def onNotebookBrowse(self, t):
        global _w
        filename, _ = QFileDialog.getOpenFileName(_w, "Load IPython notebook", '', "IPython Notebooks (*.ipynb);;All files (*.*)")
        if filename:
            t.setText( filename )

    def onFolderBrowse(self, t):
        global _w
        filename, _ = QFileDialog.getExistingDirectory(_w, "Select folder to watch")
        if filename:
            t.setText( filename )

    def onFileBrowse(self, t):
        global _w
        filename, _ = QFileDialog.getOpenFileName(_w, "Select file to watch")
        if filename:
            t.setText( filename )
        
    def sizeHint(self):
        return QSize(400,200)     


class AutomatonListDelegate(QAbstractItemDelegate):

    def paint(self, painter, option, index):
        # GET TITLE, DESCRIPTION AND ICON
        ic = QIcon(index.data(Qt.DecorationRole))
        automaton = index.data(Qt.UserRole)
        
        f = QFont()
        f.setPointSize(10)
        painter.setFont(f)

        if automaton.is_running:
            painter.setPen(QPalette().text().color())
            painter.fillRect(option.rect, QBrush(QColor(0,255,0,50) ))
        elif automaton.latest_run['success'] == False:
            painter.setPen(QPalette().text().color())
            painter.fillRect(option.rect, QBrush(QColor(255,0,0,50) ))
        elif option.state & QStyle.State_Selected:
            painter.setPen(QPalette().highlightedText().color())
            painter.fillRect(option.rect, QBrush(QPalette().highlight().color()))
        else:
            painter.setPen(QPalette().text().color())

        r = QRect(5, 4, 12, 12)
        r.translate(option.rect.x(), option.rect.y())
        icn = QIcon(os.path.join(utils.scriptdir, 'icons', 'folder-horizontal-open-sm.png') )
        painter.drawPixmap(r, icn.pixmap(QSize(12,12)))
        
        r = QRect(5, 20, 12, 12)
        r.translate(option.rect.x(), option.rect.y())
        icn = QIcon(os.path.join(utils.scriptdir, 'icons', 'qtipy-sm.png') )
        painter.drawPixmap(r, icn.pixmap(QSize(12,12)))

        r = QRect(5, 36, 12, 12)
        r.translate(option.rect.x(), option.rect.y())
        icn = QIcon(os.path.join(utils.scriptdir, 'icons', 'disk-sm.png') )
        painter.drawPixmap(r, icn.pixmap(QSize(12,12)))

        #r = option.rect.adjusted(26, 5, 0, 0)

        pen = QPen()
        if automaton.config.get('is_active'):
            pen.setColor(QColor('black'))
        else:
            pen.setColor(QColor('#aaaaaa'))

        painter.setPen(pen)

        # WATCH PATH
        r = QRect(20, 4, 200, 20)
        r.translate(option.rect.x(), option.rect.y())
        painter.drawText(r, Qt.AlignLeft, automaton.config.get('watched_path'))

        # NOTEBOOK
        r = QRect(20, 20, 200, 20)
        r.translate(option.rect.x(), option.rect.y())
        painter.drawText(r, Qt.AlignLeft, automaton.config.get('notebook_path'))

        # OUTPUT
        r = QRect(20, 36, 200, 20)
        r.translate(option.rect.x(), option.rect.y())
        painter.drawText(r, Qt.AlignLeft, automaton.config.get('output_path'))


        # LATEST RUN
        if automaton.latest_run['timestamp']:
            r = QRect(5, 52, 200, 20)
            r.translate(option.rect.x(), option.rect.y())
            painter.drawText(r, Qt.AlignLeft, "Latest run: %s" % automaton.latest_run['timestamp'].strftime("%Y-%m-%d %H:%M:%S"))

            # r = option.rect.adjusted(100, 40, 0, 0)
            # painter.drawText(r.left(), r.top(), r.width(), r.height(), Qt.AlignLeft, automaton.latest_run['datetime'].strftime("%Y-%m-%d %H:%M:%S"))
        

    def sizeHint(self, option, index):
        return QSize(200, 70)


class Automaton(QStandardItem):
    
    def __init__(self, *args, **kwargs):
        super(Automaton, self).__init__(*args, **kwargs)
        
        self.setData(self, Qt.UserRole)
        self.watcher = QFileSystemWatcher()

        self.notebook = None
        self.latest_run = {}
        self.is_running = False
        
        self.config = ConfigManager()
        self.config.set_defaults({
            'mode': MODE_MANUAL,
            'is_active':True,
            'trigger_hold': 5,
            'notebook_path':'',
            'watched_path':'',
            'output_path': '{home}',
            'output_format': 'html',
        })

        self.runner = None
        self.trigger_hold = None

        self.latest_run = {
            'timestamp':None,
            'success':None,
        }
        
        self.watcher.fileChanged.connect(self.trigger)
        self.watcher.directoryChanged.connect(self.trigger)
        
    def load_notebook(self, filename):
        with open(filename) as f:
            nb = reads(f.read(), 'json')

        if nb:
            self.notebook = nb   

    def trigger(self, e):
        # Filesystemwatcher triggered
        # Get the file and folder information; make available in vars object for run
        if self.trigger_hold is None:
            self.is_running = True
            self.update()
            self.trigger_hold = QTimer.singleShot(self.config.get('trigger_hold')*100, self.run);
        
            
    def run(self, vars={}):
        default_vars = {
            'home': os.path.expanduser('~'),
            'datetime': datetime.now(),
            'date': datetime.now().date(),
            'time': datetime.now().time(),
            'version': VERSION_STRING
        }

        vars = dict( default_vars.items() + self.config.config.items() )
        vars['output_path'] = self.config.get('output_path').format(**vars)

        if self.runner == None:
            # Postpone init to trigger for responsiveness on add/remove
            self.runner = NotebookRunner(None, pylab=True, mpl_inline=True)
            
        self.run_notebook(self.notebook, vars)
        self.trigger_hold = None

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

        self.latest_run['timestamp'] = datetime.now()
        try:
            self.runner.run_notebook()
        except:
            self.latest_run['success'] = False
        else:
            self.latest_run['success'] = True
            
        ext = dict(
            html='html',
            slides='slides',
            latex='latex',
            markdown='md',
            python='py',
            rst='rst',        
        )
            
        output, resources = IPyexport(IPyexporter_map[self.config.get('output_format')], self.runner.nb)
        with open(os.path.join(vars['output_path'], 'output.%s' % ext[self.config.get('output_format')]),"w") as f:
            f.write(output)
            
        self.is_running = False
        self.update()

    def update(self):
        global _w
        _w.viewer.update( self.index())

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

        t = self.addToolBar('Manual')
        t.setIconSize(QSize(16, 16))

        btn = QToolButton(self)
        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'play.png')), tr('Run now'), self)
        btn.setText(tr('Run now'))
        btn.setStatusTip('Run now...')
        btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        btn.setDefaultAction(action)
        action.triggered.connect( self.run_automaton )
        t.addWidget(btn)
        #self.menuBars['control'].addAction(action)

        
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
        dlg.config.set_many( automaton.config.config )
        if dlg.exec_():
            automaton.config.set_many( dlg.config.config )
            
            automaton.watcher.removePaths( automaton.watcher.files() + automaton.watcher.directories() )
            automaton.watcher.addPath( automaton.config.get('watched_path') )
            automaton.load_notebook( automaton.config.get('notebook_path') )
            automaton.update()

    def delete_automaton(self):
        '''
        '''
        automaton_idx = self.viewer.selectionModel().selectedIndexes()[0]
        self.automatons.removeRows( automaton_idx.row(), 1, QModelIndex() )
        
    def enable_automaton(self):
        '''
        '''
        try:
            automaton = self.automatons.itemFromIndex( self.viewer.selectionModel().currentIndex() )
        except:
            return
        automaton.config.set('is_active', True)
        automaton.update()

    def pause_automaton(self):
        '''
        '''
        try:
            automaton = self.automatons.itemFromIndex( self.viewer.selectionModel().currentIndex() )
        except:
            return
        automaton.config.set('is_active', False)
        automaton.update()

    def run_automaton(self):
        '''
        '''
        try:
            automaton = self.automatons.itemFromIndex( self.viewer.selectionModel().currentIndex() )
        except:
            return
        automaton.trigger(None)
    
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
