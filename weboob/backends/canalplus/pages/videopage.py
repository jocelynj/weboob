# -*- coding: utf-8 -*-

# Copyright(C) 2010  Nicolas Duhamel
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


from datetime import datetime

from weboob.capabilities.video import VideoThumbnail
from weboob.tools.browser import BasePage
from .video import CanalplusVideo


__all__ = ['VideoPage']


class VideoPage(BasePage):
    def parse_video(self, el, video=None, quality=None):
        _id = el.find('ID').text
        if _id == '-1':
            # means the video is not found
            return None

        if not video:
            video = CanalplusVideo(_id)

        infos = el.find('INFOS')
        video.title = u''
        for part in infos.find('TITRAGE'):
            if len(part.text.strip()) == 0:
                continue
            if len(video.title) > 0:
                video.title += u' — '
            video.title += part.text.strip()
        video.description = infos.find('DESCRIPTION').text

        media = el.find('MEDIA')
        video.thumbnail = VideoThumbnail(media.find('IMAGES').find('PETIT').text)
        lastest_format = None
        for format in media.find('VIDEOS'):
            if format.text is None:
                continue
            if format.tag == quality:
                video.url = format.text
                break
            lastest_format = format
        if not video.url and lastest_format is not None:
            video.url = lastest_format.text

        day, month, year = map(int, infos.find('PUBLICATION').find('DATE').text.split('/'))
        hour, minute, second = map(int, infos.find('PUBLICATION').find('HEURE').text.split(':'))
        video.date = datetime(year, month, day, hour, minute, second)

        return video

    def iter_results(self):
        for vid in self.document.getchildren():
            yield self.parse_video(vid)

    def get_video(self, video, quality):
        _id = self.group_dict['id']
        for vid in self.document.getchildren():
            if not _id in vid.find('ID').text:
                continue
            return self.parse_video(vid, video, quality)
