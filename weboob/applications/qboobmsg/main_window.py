# -*- coding: utf-8 -*-

# Copyright(C) 2010  Romain Bignon
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

from PyQt4.QtCore import SIGNAL

from weboob.tools.application.qt import QtMainWindow
from weboob.tools.application.qt.backendcfg import BackendCfg
from weboob.capabilities.messages import ICapMessages

from .ui.main_window_ui import Ui_MainWindow
from .messages_manager import MessagesManager

class MainWindow(QtMainWindow):
    def __init__(self, config, weboob, parent=None):
        QtMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.config = config
        self.weboob = weboob
        self.manager = MessagesManager(weboob, self)

        self.setCentralWidget(self.manager)

        self.connect(self.ui.actionModules, SIGNAL("triggered()"), self.modulesConfig)
        self.connect(self.ui.actionRefresh, SIGNAL("triggered()"), self.refresh)

    def modulesConfig(self):
        bckndcfg = BackendCfg(self.weboob, (ICapMessages,), self)
        bckndcfg.show()

    def refresh(self):
        self.centralWidget().refresh()