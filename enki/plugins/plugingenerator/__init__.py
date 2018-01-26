"""Generates and activates a new bare bones plugin."""

__author__ = "Marco Laspe"
__pluginname__ = "Plugin Generator"
__copyright__ = "Copyright 2018"
__credits__ = ["Marco Laspe", "Andrei Kopats", "Filipe Azevedo", "Bryan A. Jones"]
__license__ = "GPL3"
__version__ = "0.1.0"
__maintainer__ = "Marco Laspe"
__email__ = "marco@rockiger.com"

# import moduls or defer for later
os = None
shutil = None

QFileDialog = None

CONFIG_DIR = None
from enki.core.core import core


class Plugin:
    """Plugin interface implementation"""

    def __init__(self):
        """Setup settings and activate plugin, if feasable."""
        # add action
        generatePluginAction = core.actionManager().addAction(
            "mPlugins/aGeneratePlugin",
            "Generate Mamba Plugin")
        generatePluginAction.triggered.connect(self._onGeneratePluginAction)
        self._generatePluginAction = generatePluginAction

    def terminate(self):
        """clean up"""
        core.actionManager().removeAction(self._generatePluginAction)

    def _onGeneratePluginAction(self):
        # local imports to save startup time
        global os, shutil, QFileDialog, CONFIG_DIR
        if os is None:
            import os
        if shutil is None:
            import shutil
        if QFileDialog is None:
            from PyQt5.QtWidgets import QFileDialog
        if CONFIG_DIR is None:
            from enki.core.defines import CONFIG_DIR

        directory = os.path.join(CONFIG_DIR, "userplugins")
        packagePath = QFileDialog.getExistingDirectory(
            parent=core.mainWindow(),
            caption="Where do you want to create the plugin? Carful, existing files are overwritten!",
            directory=directory
        )

        # current file path
        curDir = os.path.dirname(os.path.abspath(__file__))
        print(curDir)
        shutil.copyfile(os.path.join(curDir, "barebones.template"),
                        os.path.join(packagePath, "__init__.py"))
        shutil.copyfile(os.path.join(curDir, "gitignore"),
                        os.path.join(packagePath, ".gitignore"))
        shutil.copy(os.path.join(curDir, "CHANGELOG.md"), packagePath)
        shutil.copy(os.path.join(curDir, "LICENCE"), packagePath)
        shutil.copy(os.path.join(curDir, "README.md"), packagePath)

        # open project
        core.project().open(packagePath)
