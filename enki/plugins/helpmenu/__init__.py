"""
helpmenu --- Help main menu items. Aboout dialogue
==================================================

About dialogue and *Help* menu items
"""

import os.path


from PyQt5 import Qt
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QApplication, QDialog, QStyle
from PyQt5.QtGui import QIcon
from PyQt5 import uic

from enki.core.defines import PACKAGE_NAME, PACKAGE_VERSION
from enki.core.core import core

import qutepart


class Plugin(QObject):
    """Module implementation
    """

    def __init__(self):
        QObject.__init__(self)

        def createAction(menuItem, text, icon, tab):
            """Create a menu action and connect it to the slot
            """
            action = core.actionManager().addAction("mHelp/%s" % menuItem, text, QIcon.fromTheme(icon))
            slot = lambda: UIAbout(core.mainWindow(), tab).exec_()  # pylint: disable=W0108
            action.triggered.connect(slot)
            return action

        self._createdActions = [createAction('aAbout', self.tr('&About...'), 'help-about', 'about'),
                                createAction('aHelp', self.tr('&Help...'), 'help', 'help'),
                                createAction('aReportBug', self.tr('Report &Bug...'), 'tools-report-bug', 'bug'),
                                createAction('aDonate', self.tr('&Donate...'), 'help-donate', 'donate')]

        action = core.actionManager().addAction("mHelp/aAboutQt", self.tr('About &Qt...'), core.mainWindow().style().standardIcon(getattr(QStyle, "SP_TitleBarMenuButton")))
        action.triggered.connect(QApplication.instance().aboutQt)
        self._createdActions.append(action)

    def terminate(self):
        """Terminate the plugin
        """
        for action in self._createdActions:
            core.actionManager().removeAction(action)


class UIAbout(QDialog):
    """About dialogue
    """

    def __init__(self, parentWindow, tab):
        QDialog.__init__(self, parentWindow)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'UIAbout.ui'), self)
        self.setWindowTitle(self.tr("About : %s" % PACKAGE_NAME))

        self.lTitle.setText(PACKAGE_NAME)
        qpartNumbers = '.'.join([str(item) for item in qutepart.VERSION])
        qpartParser = 'binary' if qutepart.binaryParserAvailable else 'Python'
        qpartVersion = '{} (with {} parser)'.format(qpartNumbers, qpartParser)
        self.lVersion.setText(self.tr("Version %s\n Qutepart %s\n Qt %s") %
                              (PACKAGE_VERSION, qpartVersion, Qt.QT_VERSION_STR))

        tabs = {'about': self.wLogo,
                'help': self.tbHelp,
                'bug': self.tbReportBug,
                'donate': self.tbDonations}
        self.twAbout.setCurrentWidget(tabs[tab])
