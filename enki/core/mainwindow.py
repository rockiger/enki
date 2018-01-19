"""
mainwindow --- Main window of the UI. Fills main menu.
======================================================


Module contains :class:`enki.core.mainwindow.MainWindow` implementation
"""

import sys
import os.path
import platform

from PyQt5.QtCore import pyqtSignal, QSize, Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtWidgets import QApplication, QLabel, QMessageBox, QMainWindow, \
    QSizePolicy, QStatusBar, QToolBar, QVBoxLayout, QWidget

from enki.widgets.dockwidget import DockWidget
from enki.core.actionmanager import ActionMenuBar

from enki.core.core import core
import enki.core.defines
import enki.core.json_wrapper


class _StatusBar(QStatusBar):
    """Extended status bar. Supports HTML messages
    """

    def __init__(self, *args):
        QStatusBar.__init__(self, *args)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        self.setSizeGripEnabled(False)
        self.setStyleSheet("QStatusBar {border: 0} QStatusBar::item {border: 0}")
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self._label.setStyleSheet("color: red")
        self.addWidget(self._label)
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.clearMessage)

    def term(self):
        self._timer.stop()

    def showMessage(self, text, timeout=0):
        """QStatusBar.showMessage()
        """
        self._label.setText(text)
        self._timer.stop()
        if timeout > 0:
            self._timer.start(timeout)

    def clearMessage(self):
        """QStatusBar.clearMessage()
        """
        self._label.clear()

    def currentMessage(self):
        return self._label.text()


class MainWindow(QMainWindow):
    """
    Main UI window

    Class creates window elements, fills main menu with items.

    If you need to access to some existing menu items - check action path
    in the class constructor, than use next code: ::

        core.actionManager().action("mFile/aOpen").setEnabled(True)
        core.actionManager().action("mFile/aOpen").triggered.connect(self.myCoolMethod)

    MainWindow instance is accessible as: ::

        from enki.core.core import core
        core.mainwindow()

    Created by the core
    """

    hideAllWindows = pyqtSignal()
    """
    hideAllWindows()

    **Signal** emitted, when user toggled "Hide all" .
    Dock widgets are closed automatically, but other widgets, i.e. search widget, must catch this signal and close
    themselves.
    """  # pylint: disable=W0105

    directoryDropt = pyqtSignal(str)
    """
    directoryDropt()

    **Signal** emitted, when user drag-n-dropt directory to main windowd.
    FileBrowser shows directory
    """  # pylint: disable=W0105

    _STATE_FILE = os.path.join(enki.core.defines.CONFIG_DIR, "main_window_state.bin")
    _GEOMETRY_FILE = os.path.join(enki.core.defines.CONFIG_DIR, "main_window_geometry.bin")

    def __init__(self):
        QMainWindow.__init__(self)

        self._queuedMessageToolBar = None
        self._createdMenuPathes = []
        self._createdActions = []

        self._addedDockWidgets = []

        if hasattr(self, 'setUnifiedTitleAndToolBarOnMac'):  # missing on some PyQt5 versions
            self.setUnifiedTitleAndToolBarOnMac(True)
        self.setIconSize(QSize(16, 16))
        self.setAcceptDrops(True)

        # Set corner settings for dock widgets
        self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)

        self.setWindowTitle(self.defaultTitle())  # overwriten by workspace when file or it's modified state changes
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        logo_path = os.path.join(scriptDir,'../../icons/logo/mamba.svg')
        self.setWindowIcon(QIcon(logo_path))

        # Create top tool bar
        self._topToolBar = QToolBar("topToolBar")
        self._topToolBar.setObjectName("topToolBar")
        self._topToolBar.setMovable(False)
        self._topToolBar.setIconSize(QSize(16, 16))
        self._topToolBar.setContextMenuPolicy(Qt.PreventContextMenu)  # to avoid possibility to hide the toolbar

        # Create menu bar
        self._menuBar = ActionMenuBar(self, core.actionManager())
        self._initMenubarAndStatusBarLayout()

        # create central layout
        widget = QWidget(self)
        self._centralLayout = QVBoxLayout(widget)
        self._centralLayout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(widget)
        self.setStyleSheet('QMainWindow::separator{width: 4px}')

    def _initActions(self):
        """ Public method for actionManager. """

        self._createMenuStructure()
        core.actionManager().action('mView/aOpenMainMenu').triggered.connect(self._openMainMenu)
        core.actionManager().action('mFile/aQuit').triggered.connect(self.onQuit)

    def terminate(self):
        """Explicitly called destructor
        """
        if self._queuedMessageToolBar:
            self.removeToolBar(self._queuedMessageToolBar)
            del self._queuedMessageToolBar

        for act in self._createdActions:
            core.actionManager().removeAction(act)
        for menuPath in self._createdMenuPathes[::-1]:
            core.actionManager().removeMenu(menuPath)

    @staticmethod
    def _isMenuEmbeddedToTaskBar():
        """On Unity (Ubuntu) and MacOS menu bar is embedded to task bar
        """
        return 'UBUNTU_MENUPROXY' in os.environ or \
               os.environ.get('XDG_CURRENT_DESKTOP') == 'Unity' or \
               'darwin' == sys.platform

    def _initMenubarAndStatusBarLayout(self):
        """Create top widget and put it on its place
        """
        # if not 'darwin' == sys.platform:
        #     # on Ubuntu toolbar, docs and editor area look as one widget. Ugly
        #     # Therefore it is separated with line. On Mac seems OK
        #     # I can't predict, how it will look on other platforms, therefore line is used for all, except Mac
        #     toolBarStyleSheet = "QToolBar {border: 0; border-bottom-width: 1; border-bottom-style: solid}"""
        #     self._topToolBar.setStyleSheet(toolBarStyleSheet)

        area = Qt.BottomToolBarArea if self._isMenuEmbeddedToTaskBar() else Qt.TopToolBarArea
        self.addToolBar(area, self._topToolBar)

        if self._isMenuEmbeddedToTaskBar():  # separate menu bar
            self.setMenuBar(self._menuBar)
        else:  # menubar, statusbar and editor tool bar on one line
            self._menuBar.setAutoFillBackground(False)
            menuBarStyleSheet = """
            QMenuBar {background-color: transparent;
                      color: %s}
            QMenuBar::item:!selected {background: transparent;}
            """ % self.palette().color(QPalette.WindowText).name()
            self._menuBar.setStyleSheet(menuBarStyleSheet)
            self._menuBar.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

            self._topToolBar.addWidget(self._menuBar)

        # Create status bar
        self._statusBar = _StatusBar(self)
        self._topToolBar.addWidget(self._statusBar)

    def _initQueuedMessageToolBar(self):
        from enki.core.queued_msg_tool_bar import QueuedMessageToolBar

        self._queuedMessageToolBar = QueuedMessageToolBar(self)
        area = Qt.TopToolBarArea if self._isMenuEmbeddedToTaskBar() else Qt.BottomToolBarArea
        self.addToolBar(area, self._queuedMessageToolBar)
        self._queuedMessageToolBar.setVisible(False)

    def _createMenuStructure(self):
        """Fill menu bar with items. The majority of items are not connected to the slots,
        Connections made by module, which implements menu item functionality, but, all items are in one place,
        because it's easier to create clear menu layout
        """
        # create menubar menus and actions

        def menu(path, name, icon, visible=True):
            """Subfunction for create a menu in the main menu"""
            menuObject = core.actionManager().addMenu(path, name)
            if icon :
                menuObject.setIcon(QIcon.fromTheme(icon))
            self._createdMenuPathes.append(path)
            if not visible:
                menuObject.setVisible(False)

        def action(path, name, icon, shortcut, tooltip, enabled, checkable=False):  # pylint: disable=R0913
            """Subfunction for create an action in the main menu"""
            if icon:  # has icon
                actObject = core.actionManager().addAction(
                    path,
                    name,
                    QIcon.fromTheme(icon),
                    shortcut)
            else:
                actObject = core.actionManager().addAction(path, name, shortcut=shortcut)
            if tooltip:
                actObject.setStatusTip(tooltip)
            actObject.setEnabled(enabled)
            actObject.setCheckable(checkable)
            self._createdActions.append(actObject)

        def separator(menu):
            """Subfunction for insert separator to the menu"""
            core.actionManager().action(menu).menu().addSeparator()

        # pylint: disable=C0301
        # enable long lines for menu items
        # Menu or action path                          Name                     Icon                    Shortcut        Hint                     enabled  checkable
        menu  ("mFile",                               "File"                  , ""           )
        action("mFile/aOpenProject",                  "Open Pro&ject..."      , "project-open",         "Shift+Ctrl+O" ,"Open a project"         , True)
        separator("mFile")
        menu  ("mFile/mUndoClose",                    "Undo Close"            , "document-open-recent")
        separator("mFile")
        action("mFile/aNew",                          "&New file..."          , "document-new",          'Ctrl+N',       "New file"               , True)
        action("mFile/aOpen",                         "&Open..."              , "document-open",        "Ctrl+O" ,      "Open a file"            , True)
        menu  ("mFile/mSave",                         "&Save"                 , "document-save"   )
        action("mFile/mSave/aCurrent",                "&Save"                 , "document-save" ,        "Ctrl+S" ,      "Save the current file"  , False)
        action("mFile/mSave/aSaveAs",                 "Save As..."            , "document-save-as" ,        "Shift+Ctrl+S" ,  ""                  , False)
        action("mFile/mSave/aAll",                    "Save &All"             , "document-save-all",      'Ctrl+Alt+S', "Save all files"         , False)
        menu  ("mFile/mReload",                       "&Reload"               , "refresh"   )
        action("mFile/mReload/aCurrent",              "Reload"                , "refresh"  ,     'F5',           "Reload the current file", False)
        action("mFile/mReload/aAll",                  "Reload All"            , "update-none"  ,     'Shift+F5',     "Reload all files"       , True)
        menu  ("mFile/mClose",                        "&Close"                , "document-close"  )
        action("mFile/mClose/aCurrent",               "&Close"                , "document-close",    "Ctrl+W",       "Close the current file" , False)
        action("mFile/mClose/aAll",                   "Close &All"            , "project-development-close", 'Shift+Ctrl+W', "Close all files"        , False)
        menu  ("mFile/mFileSystem",                   "File System"           , "drive-harddisk")
        action("mFile/mFileSystem/aRename",           "Rename"                , "document-edit",     '',             "Rename current file"    , False)
        if platform.system() != 'Windows':
            action("mFile/mFileSystem/aToggleExecutable", "Make executable"   , "text-x-script",            '',             "Toggle executable mode" , False)
        separator("mFile")
        action("mFile/aQuit",                         "Quit"                  , "application-exit",     'Ctrl+Q',       "Quit"                  , True)
        separator("mFile")

        menu  ("mEdit",                               "Edit"                  , ""           )
        separator("mEdit")
        menu  ("mEdit/mCopyPasteLines",               "Copy-paste lines"      , ""           )
        menu  ("mEdit/mIndentation",                  "Indentation"           , ""           )
        separator("mEdit")

        menu  ("mView",                               "View"                  , ""           )
        action("mView/aShowIncorrectIndentation",      "Show incorrect indentation", "",       "",              ""                       , False, True)
        action("mView/aShowAnyWhitespaces",     "Show any whitespace",        "",              "",              ""                       , False, True)
        separator("mView")
        action("mView/aHideAll",                      "Hide all / Restore"   , "",             "Shift+Esc",   "Hide all widgets"          , True)
        action("mView/aOpenMainMenu",                 "Open main menu"       , "",             "F10",         ""                          , True)
        separator("mView")


        menu  ("mNavigation",                          "Navigation"            , ""          )
        action("mNavigation/aFocusCurrentDocument",   "Focus to editor"       , "story-editor",     "Ctrl+Return",  "Focus current document" , False)

        menu  ("mNavigation/mSearchReplace",           "&Search && Replace"    , "search")
        menu  ("mNavigation/mBookmarks",               "&Bookmarks"            , "bookmarks")

        separator("mNavigation"),
        action("mNavigation/aNext",                   "&Next file"            , "go-next",     "Ctrl+PgDown",    "Next file"              , False)
        action("mNavigation/aPrevious",               "&Previous file"        , "go-previous", "Ctrl+PgUp",     "Previous file"          , False)
        separator("mNavigation")
        action("mNavigation/aGoto",                   "Go to line..."         , "go-jump",     "Ctrl+G",       "Go to line..."          , False)
        menu  ("mNavigation/mFileBrowser",            "File browser"          , 'system-file-manager', visible=False)
        menu  ("mNavigation/mScroll",                 "Scroll file"           , 'transform-move-vertical')

        menu  ("mSettings",                           "Settings"              , ""           )
        action("mSettings/aStripTrailingWhitespace",      "Strip trailing whitespace when saving", "", "",            ""                   , True, True)
        action("mSettings/aEnableVimMode",                "Enable Vim mode"       , "",             "",             ""                      , False, True)

        #menu  ("mTools",                              "Tools"                 , ""           )
        menu  ("mHelp",                               "Help"                  , ""           )

    @pyqtSlot()
    def _openMainMenu(self):
        fileMenu = core.actionManager().menu('mFile')
        self._menuBar.setActiveAction(fileMenu.menuAction())

    def menuBar(self):
        """Reference to menuBar
        """
        return self._menuBar

    def topToolBar(self):
        """Top tool bar. Contains main menu, position indicator, etc
        """
        return self._topToolBar

    def statusBar(self):
        """Return main window status bar.
        It is located on the top tool bar
        """
        return self._statusBar

    def setWorkspace(self, workspace):
        """Set central widget of the main window.
        Normally called only by core when initializing system
        """
        self._centralLayout.addWidget(workspace)
        self.setFocusProxy(workspace)

    def defaultTitle(self):
        """Default title. Contains  name and version
        """
        return "%s v.%s" % (enki.core.defines.PACKAGE_NAME, enki.core.defines.PACKAGE_VERSION)

    def centralLayout(self):
        """Layout of the central widget. Contains Workspace and search widget
        """
        return self._centralLayout

    def appendMessage(self, text, timeoutMs=10000):
        """Append message to the queue. It will be shown as non-modal at the bottom of the window.
        Use such notifications, which are too long or too important for status bar
        but, not so important, to interrupt an user with QMessageBox
        """
        if self._queuedMessageToolBar is None:
            self._initQueuedMessageToolBar()

        self._queuedMessageToolBar.appendMessage(text, timeoutMs)

    def closeEvent(self, event):
        """NOT A PUBLIC API
        Close event handler.
        Shows save files dialog. Cancels close, if dialog was rejected
        """

        # saving geometry BEFORE closing widgets, because state might be changed, when docks are closed
        self._saveState()
        self._saveGeometry()

        # request close all documents
        if not core.workspace().askToCloseAll():
            event.ignore()
            return

        core.aboutToTerminate.emit()
        self.hide()

        core.workspace().forceCloseAllDocuments()

        return QMainWindow.closeEvent(self, event)

    def onQuit(self):
        # saving geometry BEFORE closing widgets, because state might be changed, when docks are closed
        self._saveState()
        self._saveGeometry()

        # request close all documents
        if not core.workspace().askToCloseAll():
            return

        core.aboutToTerminate.emit()
        self.hide()

        core.workspace().forceCloseAllDocuments()

        return QApplication.quit()

    def _saveByteArray(self, path, title, data):
        """Load data, show error and return None if failed"""
        try:
            with open(path, 'wb') as f:
                f.write(data)
        except (OSError, IOError) as ex:
            error = str(ex)
            QMessageBox.critical(None,
                                 self.tr("Cannot save {}".format(title)),
                                 self.tr("Cannot create file '%s'\nError: %s" % (path, error)))
            return

    def _loadByteArray(self, path, title):
        """Load data, show error and return None if failed"""
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    return f.read()
            except (OSError, IOError) as ex:
                error = str(ex)
                QMessageBox.critical(None,
                                     self.tr("Cannot restore {}".format(title)),
                                     self.tr("Cannot read file '%s'\nError: %s" % (path, error)))

        return None

    def _saveState(self):
        """Save window state to main_window_state.bin file in the config directory
        """
        self._saveByteArray(self._STATE_FILE, "main window state", self.saveState())

    def loadState(self):
        """Restore window state from main_window_state.bin and config.
        Called by the core after all plugins had been initialized
        """
        self._restoreGeometry()

        state = self._loadByteArray(self._STATE_FILE, "main window state")

        if state is not None:
            self.restoreState(state)
        else:  # no state, first start
            self.showMaximized()
            for dock in self.findChildren(DockWidget):
                dock.show()

    def _saveGeometry(self):
        """Save window geometry to the config file
        """
        self._saveByteArray(self._GEOMETRY_FILE, "main window geometry", self.saveGeometry())

    def _restoreGeometry(self):
        """Restore window geometry to the config file
        """
        geometry = self._loadByteArray(self._GEOMETRY_FILE, "main window geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

    def sizeHint(self):
        return QSize(900, 560)

    def dragEnterEvent(self, event):
        """QMainWindow method reimplementation.
        Say, that we are ready to accept dragged urls
        """
        if event.mimeData().hasUrls():
            # accept drag
            event.acceptProposedAction()

        # default handler
        QMainWindow.dragEnterEvent(self, event)

    def dropEvent(self, event):
        """QMainWindow method reimplementation.
        Open dropt files
        """
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                localFile = url.toLocalFile()
                if os.path.isfile(localFile):
                    core.workspace().openFile(localFile)
                elif os.path.isdir(localFile):
                    self.directoryDropt.emit(localFile)

        # default handler
        QMainWindow.dropEvent(self, event)

    def addDockWidget(self, area, dock):
        pass  # not a plugin API method
        """Add dock widget to previous position, if known.
        Otherwise add to specified area
        """
        assert not dock in self._addedDockWidgets
        self._addedDockWidgets.append(dock)

        if not self.restoreDockWidget(dock):
            QMainWindow.addDockWidget(self, area, dock)

        """ Scroll view to make the cursor visible.
        Otherwise cursor can disappear from the viewport.
        QTimer is used because ensureCursorVisible works only after the dock has been drawn.
        A bad fix for #319
        """
        QTimer.singleShot(0, self._ensureCursorVisible)

    def _ensureCursorVisible(self):
        # When the timer fires, first check that there's still a workspace/document.
        if core.workspace() is not None:
            document = core.workspace().currentDocument()
            if document is not None:
                document.qutepart.ensureCursorVisible

    def removeDockWidget(self, dock):
        pass  # not a plugin API method
        """Remove dock widget"""
        assert dock in self._addedDockWidgets
        self._addedDockWidgets.remove(dock)
        QMainWindow.removeDockWidget(self, dock)

    def restoreState(self, state):
        pass  # not a plugin API method
        """Restore state shows widgets, which exist
        but shall not be installed on main window
        """
        QMainWindow.restoreState(self, state)
        for dock in self.findChildren(DockWidget):
            if not dock in self._addedDockWidgets:
                dock.hide()
