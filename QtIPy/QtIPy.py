# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import logging

frozen = getattr(sys, 'frozen', None)
if frozen:
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)

try:
    import xml.etree.cElementTree as et
except ImportError:
    import xml.etree.ElementTree as et


import os
import re

from .qt import *
from . import utils
from .translate import tr

from datetime import datetime, timedelta
import traceback

VERSION_STRING = '0.0.1'

from pyqtconfig import ConfigManager

import os,sys,time

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
MODE_WATCH_FOLDER = 2
MODE_TIMER = 3


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


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
        'Watch files': MODE_WATCH_FILES,
        'Watch folder': MODE_WATCH_FOLDER,
        'Timer': MODE_TIMER,
    }
    
    
    def __init__(self, parent, **kwargs):
        super(AutomatonDialog, self).__init__(parent, **kwargs)
        self.setWindowTitle("Edit Automaton")
    
        self.config = ConfigManager()

        gb = QGroupBox('IPython notebook(s) (*.ipynb)')
        grid = QGridLayout()
        notebook_path_le = QLineEdit()
        self.config.add_handler('notebook_paths', notebook_path_le, mapper=(lambda x:x.split(";"), lambda x:";".join(x)))
        grid.addWidget(notebook_path_le, 0, 0, 1,2)

        notebook_path_btn = QToolButton()
        notebook_path_btn.setIcon( QIcon(os.path.join(utils.scriptdir, 'icons', 'document-attribute-i.png')) )
        notebook_path_btn.clicked.connect( lambda: self.onNotebookBrowse(notebook_path_le) )
        grid.addWidget(notebook_path_btn, 0, 2, 1,1)
        gb.setLayout(grid)
        
        self.layout.addWidget(gb)

        gb = QGroupBox('Automaton mode')
        grid = QGridLayout()
        mode_cb = QComboBox()
        mode_cb.addItems( self.mode_options.keys() )
        mode_cb.currentIndexChanged.connect(self.onChangeMode)
        self.config.add_handler('mode', mode_cb, mapper=self.mode_options)
        grid.addWidget(QLabel('Mode'), 0, 0)
        grid.addWidget(mode_cb, 0, 1)


        grid.addWidget(QLabel('Hold trigger'), 1, 0)
        fwatcher_hold_sb = QSpinBox()
        fwatcher_hold_sb.setRange(0, 60)
        fwatcher_hold_sb.setSuffix(' secs')
        self.config.add_handler('trigger_hold', fwatcher_hold_sb)
        grid.addWidget(fwatcher_hold_sb, 1, 1)
        gb.setLayout(grid)

        self.layout.addWidget(gb)
        
        self.watchfile_gb = QGroupBox('Watch files')
        grid = QGridLayout()

        watched_path_le = QLineEdit()
        grid.addWidget(watched_path_le, 0, 0, 1,2)
        self.config.add_handler('watched_files', watched_path_le, mapper=(lambda x:x.split(";"), lambda x:";".join(x)))
        
        watched_path_btn = QToolButton()
        watched_path_btn.setIcon( QIcon(os.path.join(utils.scriptdir, 'icons', 'document-copy.png')) )
        watched_path_btn.setStatusTip('Add file(s)')
        watched_path_btn.clicked.connect( lambda: self.onFilesBrowse(watched_path_le) )
        grid.addWidget(watched_path_btn, 0, 2, 1,1)
        
        grid.addWidget(QLabel('Watch window'), 1, 0)
        watch_window_sb = QSpinBox()
        watch_window_sb.setRange(0, 60)
        watch_window_sb.setSuffix(' secs')
        self.config.add_handler('watch_window', watch_window_sb)
        grid.addWidget(watch_window_sb, 1, 1)
        
        self.watchfile_gb.setLayout(grid)
        self.layout.addWidget(self.watchfile_gb)
        
        self.watchfolder_gb = QGroupBox('Watch folder')
        grid = QGridLayout()

        watched_path_le = QLineEdit()
        grid.addWidget(watched_path_le, 0, 0, 1,2)
        self.config.add_handler('watched_folder', watched_path_le)
        
        watched_path_btn = QToolButton()
        watched_path_btn.setIcon( QIcon(os.path.join(utils.scriptdir, 'icons', 'folder-horizontal-open.png')) )
        watched_path_btn.setStatusTip('Add folder')
        watched_path_btn.clicked.connect( lambda: self.onFolderBrowse(watched_path_le) )
        grid.addWidget(watched_path_btn, 0, 2, 1,1)

        grid.addWidget(QLabel('Iterate files in folder'), 3, 0)
        loop_folder_sb = QCheckBox()
        self.config.add_handler('loop_watched_folder', loop_folder_sb)
        grid.addWidget(loop_folder_sb, 3, 1)

        
        self.watchfolder_gb.setLayout(grid)
        self.layout.addWidget(self.watchfolder_gb)        


        self.timer_gb = QGroupBox('Timer')
        grid = QGridLayout()
        
        grid.addWidget(QLabel('Run every'), 0, 0)
        watch_timer_sb = QSpinBox()
        watch_timer_sb.setRange(0, 60)
        watch_timer_sb.setSuffix(' secs')
        self.config.add_handler('timer_seconds', watch_timer_sb)
        grid.addWidget(watch_timer_sb, 0, 1)
        
        self.timer_gb.setLayout(grid)
        self.layout.addWidget(self.timer_gb)

        self.manual_gb = QGroupBox('Manual') # No show
        grid = QGridLayout()
        grid.addWidget(QLabel('No configuration'), 0, 0)
        self.manual_gb.setLayout(grid)
        self.layout.addWidget(self.manual_gb)
        
        
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

        self.layout.addStretch()
        self.finalise()

        self.onChangeMode(mode_cb.currentIndex())
        
    def onNotebookBrowse(self, t):
        global _w
        filenames, _ = QFileDialog.getOpenFileNames(_w, "Load IPython notebook(s)", '', "IPython Notebooks (*.ipynb);;All files (*.*)")
        if filenames:
            self.config.set('notebook_paths',filenames)

    def onFolderBrowse(self, t):
        global _w
        filename = QFileDialog.getExistingDirectory(_w, "Select folder to watch")
        if filename:
            self.config.set('watched_folder',filename)

    def onFilesBrowse(self, t):
        global _w
        filenames, _ = QFileDialog.getOpenFileNames(_w, "Select file(s) to watch")
        if filenames:
            self.config.set('watched_files',filenames)
        
        
    def onChangeMode(self, i):
        for m,gb in { MODE_MANUAL: self.manual_gb, MODE_WATCH_FILES: self.watchfile_gb, MODE_WATCH_FOLDER: self.watchfolder_gb, MODE_TIMER: self.timer_gb }.items():
            if m == self.mode_options.items()[i][1]:
                gb.show()
            else:
                gb.hide()
        
        
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
        icn = QIcon(os.path.join(utils.scriptdir, 'icons', 'qtipy-sm.png') )
        painter.drawPixmap(r, icn.pixmap(QSize(12,12)))

        r = QRect(5, 20, 12, 12)
        r.translate(option.rect.x(), option.rect.y())
        icn = QIcon(os.path.join(utils.scriptdir, 'icons', 'folder-horizontal-open-sm.png') )
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

        # NOTEBOOK
        r = QRect(20, 4, option.rect.width()-40, 20)
        r.translate(option.rect.x(), option.rect.y())
        painter.drawText(r, Qt.AlignLeft, ";".join( automaton.config.get('notebook_paths') ))

        # WATCH PATH
        r = QRect(20, 20, option.rect.width()-40, 20)
        r.translate(option.rect.x(), option.rect.y())
        if automaton.config.get('mode') == MODE_WATCH_FILES:
            painter.drawText(r, Qt.AlignLeft, ";".join( automaton.config.get('watched_files') ))
        else:
            painter.drawText(r, Qt.AlignLeft, automaton.config.get('watched_folder') )

        # OUTPUT
        r = QRect(20, 36, option.rect.width()-40, 20)
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
        self.timer = QTimer() 
        
        self.watch_window = {}

        self.latest_run = {}
        self.is_running = False
        
        self.config = ConfigManager()
        self.config.set_defaults({
            'mode': MODE_WATCH_FOLDER,
            'is_active':True,
            'trigger_hold': 1,
            'notebook_paths':'',
            'output_path': '{home}/{notebook_filename}_{datetime}_',
            'output_format': 'html',

            'watched_files':[],
            'watched_folder':'',
            'watch_window':15,

            'loop_watched_folder':False,

            'timer_seconds':60,
        })

        self.runner = None
        self.lock = None

        self.latest_run = {
            'timestamp':None,
            'success':None,
        }
        
        # Set up all the triggers
        self.watcher.fileChanged.connect(self.file_trigger_accumulator)
        self.watcher.directoryChanged.connect(self.trigger)
        self.timer.timeout.connect(self.trigger)
        
    def startup(self):
        if self.config.get('mode') == MODE_TIMER:
            self.timer.setInterval( self.config.get('timer_seconds')*1000 )
            self.timer.start()
            
        elif self.config.get('mode') == MODE_WATCH_FILES:
            current_paths = self.watcher.files() + self.watcher.directories() 
            if current_paths:
                self.watcher.removePaths( current_paths )
            self.watch_window = {}
            self.watcher.addPaths( self.config.get('watched_files') )

        elif self.config.get('mode') == MODE_WATCH_FOLDER:
            current_paths = self.watcher.files() + self.watcher.directories() 
            if current_paths:
                self.watcher.removePaths( current_paths )
            self.watcher.addPath( self.config.get('watched_folder') )
        
    def shutdown(self):
        if self.config.get('mode') == MODE_TIMER:
            self.timer.stop()
            
        elif self.config.get('mode') == MODE_WATCH_FILES or self.config.get('mode') == MODE_WATCH_FOLDER:
            current_paths = self.watcher.files() + self.watcher.directories() 
            if current_paths:
                self.watcher.removePaths( current_paths )
            self.watch_window = {}

        
    def load_notebook(self, filename):
        try:
            with open(filename) as f:
                nb = reads(f.read(), 'json')
        except:
            return None
        else:
            return nb
            
    def file_trigger_accumulator(self, f):
        # Accumulate triggers from changed files: if 3 files are specified to watch
        # we only want to fire once _all_ files have changed (within the given watch window)
        current_time = datetime.now()
        self.watch_window[f] = current_time # timestamp
        self.watch_window = {k:v for k,v in self.watch_window.items() if current_time - timedelta(seconds=self.config.get('watch_window')) < v}
        
        if set( self.watch_window.keys() ) == set( self.watcher.files() + self.watcher.directories() ):
            self.trigger()

    def trigger(self, e=None):
        if self.config.get('is_active') == False:
            return False
        # Filesystemwatcher triggered
        # Get the file and folder information; make available in vars object for run
        if self.lock is None:
            self.is_running = True
            self.update()
            self.lock = QTimer.singleShot(self.config.get('trigger_hold')*1000, self.run)
            
    def run(self, vars={}):

        default_vars = {
            'home': os.path.expanduser('~'),
            'version': VERSION_STRING,
        }
        
        default_vars_and_config = dict( default_vars.items() + self.config.config.items() )

        if self.runner == None:
            # Postpone init to trigger for responsiveness on add/remove
            self.runner = NotebookRunner(None, pylab=True, mpl_inline=True)

        if self.config.get('mode') == MODE_WATCH_FOLDER and self.config.get('loop_watched_folder'):
            for (dirpath, dirnames, filenames) in os.walk(self.config.get('watched_folder')):
                break
            
            logging.info('Watched folder contains %d files; looping' % len(filenames))
            # Filenames contains the list of files in the folder
        else:
            filenames = [None]

        self.latest_run['timestamp'] = datetime.now()
            
        try:
            for f in filenames:
                now = datetime.now()
                current_vars = {
                    'datetime': now.strftime("%Y-%m-%d %H.%M.%S"),
                    'date': now.date().strftime("%Y-%m-%d"),
                    'time': now.time().strftime("%H.%M.%S"),
                    'filename': f,
                }
                vars = dict( default_vars_and_config.items() + current_vars.items() )

                for nb_path in self.config.get('notebook_paths'):
                    nb = self.load_notebook(nb_path)
        
                    if nb:
                        # Add currently running notebook path to vars
                        vars['notebook_path'] = nb_path
                        vars['notebook_filename'] = os.path.basename(nb_path)

                        vars['output_path'] = self.config.get('output_path').format(**vars)
                        parent_folder = os.path.dirname(vars['output_path'])
                        if parent_folder:
                            try:
                                utils.mkdir_p(parent_folder)
                            except: # Can't create folder
                                self.latest_run['success'] = False
                                raise
    
                        self.run_notebook(nb, vars)
                
                    else:
                        raise

        except:
            self.latest_run['success'] = False
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            logging.error("%s\n%s\n%s" % (exctype, value, traceback.format_exc()))
        
        finally:
            self.is_running = False
            self.lock = None
            self.update()

    def run_notebook(self, nb, vars={}):
        if len(nb['worksheets'])==0:
            nb['worksheets']=[NotebookNode({'cells':[], 'metadata':{}})]

        start = nb['worksheets'][0]['cells']
        start.insert(0, Struct(**{
            'cell_type': 'code',
            'language': 'python',
            'outputs': [],
            'collapsed': False,
            'prompt_number': -1,
            'input': 'qtipy=%s' % vars,
            'metadata': {},
        }) )
        self.runner.nb = nb

        try:
            self.runner.run_notebook()
        except:
            self.latest_run['success'] = False
            raise
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
        output_path = vars['output_path'] + 'notebook.%s' % ext[self.config.get('output_format')]
        logging.info("Exporting updated notebook to %s" % output_path)
        with open(output_path,"w") as f:
            f.write(output)
            

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
        action.setShortcut( QKeySequence.Open )
        action.setStatusTip('Load automatons')
        action.triggered.connect( self.load_automatons )
        t.addAction(action)
        self.menuBars['file'].addAction(action)

        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'disk.png')), tr('Save automatons'), self)
        action.setShortcut( QKeySequence.Save )
        action.setStatusTip('Save automatons')
        action.triggered.connect( self.save_automatons )
        t.addAction(action)
        self.menuBars['file'].addAction(action)

        t = self.addToolBar('Edit')
        t.setIconSize(QSize(16, 16))

        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'plus-circle.png')), tr('Add automaton'), self)
        action.setShortcut( QKeySequence.New )
        action.setStatusTip('Add new automaton')
        action.triggered.connect( self.add_new_automaton )
        t.addAction(action)
        self.menuBars['edit'].addAction(action)

        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'property.png')), tr('Edit automaton'), self)
        action.setStatusTip('Edit automaton')
        action.triggered.connect( self.edit_automaton )
        t.addAction(action)
        self.menuBars['edit'].addAction(action)


        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'cross.png')), tr('Delete automaton'), self)
        action.setShortcut( QKeySequence.Delete )
        action.setStatusTip('Delete automaton')
        action.triggered.connect( self.delete_automaton )
        t.addAction(action)
        self.menuBars['edit'].addAction(action)

        t = self.addToolBar('Control')
        t.setIconSize(QSize(16, 16))

        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'control.png')), tr('Enable'), self)
        action.setShortcut(tr("Ctrl+E"));
        action.setStatusTip('Enable automaton')
        action.triggered.connect( self.enable_automaton )
        t.addAction(action)
        self.menuBars['control'].addAction(action)

        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'control-pause.png')), tr('Pause'), self)
        action.setShortcut(tr("Ctrl+W"));
        action.setStatusTip('Pause automaton')
        action.triggered.connect( self.pause_automaton )
        t.addAction(action)
        self.menuBars['control'].addAction(action)

        t = self.addToolBar('Manual')
        t.setIconSize(QSize(16, 16))

        btn = QToolButton(self)
        action = QAction(QIcon(os.path.join(utils.scriptdir, 'icons', 'play.png')), tr('Run now'), self)
        action.setShortcut(tr("Ctrl+R"));
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
        
        automaton.shutdown()
        dlg = AutomatonDialog(self)
        dlg.config.set_many( automaton.config.config )
        if dlg.exec_():
            automaton.config.set_many( dlg.config.config )
            if automaton.config.get('is_active'):
                automaton.startup()
            automaton.update()

    def delete_automaton(self):
        '''
        '''
        _btn = QMessageBox.question(self, "Confirm delete", "Are you sure you want to delete this automaton?")
        if _btn == QMessageBox.Yes:
            automaton = self.automatons.itemFromIndex( self.viewer.selectionModel().currentIndex() )
            automaton.shutdown()
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
        automaton.startup()
        automaton.update()

    def pause_automaton(self):
        '''
        '''
        try:
            automaton = self.automatons.itemFromIndex( self.viewer.selectionModel().currentIndex() )
        except:
            return
        automaton.config.set('is_active', False)
        automaton.shutdown()
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
        global _w
        filename, _ = QFileDialog.getOpenFileName(_w, "Load QtIPy Automatons", '', "QtIPy Automaton File (*.qifx);;All files (*.*)")
        if filename:
        
            self.automatons.clear()
            
            tree = et.parse(filename)
            automatons = tree.getroot()
        
            for automatonx in automatons.findall('Automaton'):
                automaton = Automaton()
                automaton.config.setXMLConfig(automatonx)
            
                self.automatons.appendRow(automaton)
                
                if automaton.config.get('is_active'):
                    automaton.startup()
            
            
    def save_automatons(self):
        '''
        '''
        global _w
        filename, _ = QFileDialog.getSaveFileName(_w, "Save QtIPy Automatons", '', "QtIPy Automaton File (*.qifx);;All files (*.*)")
        if filename:
        
            root = et.Element("QtIPy")
            root.set('xmlns:mpwfml', "http://martinfitzpatrick.name/schema/QtIPy/2013a")

            # Build a JSONable object representing the entire current workspace and write it to file
            for i in range(0, self.automatons.rowCount()):
                a = self.automatons.item(i)
            
                automaton = et.SubElement(root, "Automaton")
                automaton = a.config.getXMLConfig(automaton)

            tree = et.ElementTree(root)
            tree.write(filename)  # , pretty_print=True)
                            
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
