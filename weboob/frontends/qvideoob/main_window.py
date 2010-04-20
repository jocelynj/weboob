# -*- coding: utf-8 -*-

"""
Copyright(C) 2010  Romain Bignon

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

"""

from PyQt4.QtCore import SIGNAL

from weboob.tools.application.qt import QtMainWindow

from weboob.frontends.qvideoob.ui.main_window_ui import Ui_MainWindow

from .video import Video
from .minivideo import MiniVideo

class MainWindow(QtMainWindow):
    def __init__(self, config, weboob, parent=None):
        QtMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.config = config
        self.weboob = weboob
        self.minivideos = []

        self.ui.backendEdit.addItem('All backends', '')
        for i, backend in enumerate(self.weboob.iter_backends()):
            self.ui.backendEdit.addItem(backend.name, backend.name)
            if backend.name == self.config.get('settings', 'backend'):
                self.ui.backendEdit.setCurrentIndex(i+1)
        self.ui.sortbyEdit.setCurrentIndex(int(self.config.get('settings', 'sortby')))
        self.ui.nsfwCheckBox.setChecked(bool(self.config.get('settings', 'nsfw')))

        self.connect(self.ui.searchEdit, SIGNAL("returnPressed()"), self.search)
        self.connect(self.ui.urlEdit, SIGNAL("returnPressed()"), self.openURL)
        self.connect(self.ui.nsfwCheckBox, SIGNAL("stateChanged(int)"), self.nsfwChanged)

    def nsfwChanged(self, state):
        self.config.set('settings', 'nsfw', self.ui.nsfwCheckBox.isChecked())
        for minivideo in self.minivideos:
            if minivideo.video.nsfw:
                if state:
                    minivideo.show()
                else:
                    minivideo.hide()

    def search(self):
        pattern = unicode(self.ui.searchEdit.text())
        if not pattern:
            return

        for minivideo in self.minivideos:
            self.ui.scrollAreaContent.layout().removeWidget(minivideo)
            minivideo.hide()

        self.minivideos = []

        backend_name = str(self.ui.backendEdit.itemData(self.ui.backendEdit.currentIndex()).toString())

        for backend in self.weboob.iter_backends():
            if backend_name and backend.name != backend_name:
                continue
            for video in backend.iter_search_results(pattern, self.ui.sortbyEdit.currentIndex()):
                minivideo = MiniVideo(backend, video)
                self.ui.scrollAreaContent.layout().addWidget(minivideo)
                self.minivideos.append(minivideo)
                if video.nsfw and not self.ui.nsfwCheckBox.isChecked():
                    minivideo.hide()

    def openURL(self):
        url = unicode(self.ui.urlEdit.text())
        if not url:
            return

        for backend in self.weboob.iter_backends():
            video = backend.get_video(url)
            if video:
                video_widget = Video(video, self)
                video_widget.show()

        self.ui.urlEdit.clear()

    def closeEvent(self, ev):
        self.config.set('settings', 'backend', str(self.ui.backendEdit.itemData(self.ui.backendEdit.currentIndex()).toString()))
        self.config.set('settings', 'sortby', self.ui.sortbyEdit.currentIndex())
        self.config.save()
        ev.accept()