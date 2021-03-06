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


import urllib
from cStringIO import StringIO

from weboob.tools.browser import BaseBrowser
from weboob.tools.parsers.lxmlparser import LxmlHtmlParser

from .pages.index import IndexPage, LoginPage
from .pages.news import ContentPage
from .tools import id2url, id2threadid, id2contenttype

class Parser(LxmlHtmlParser):
    def parse(self, data, encoding=None):
        # Want to kill templeet coders
        data = StringIO(data.read().replace('<<', '<').replace('cite>', 'i>').replace('tt>', 'i>'))
        return LxmlHtmlParser.parse(self, data, encoding)

# Browser
class DLFP(BaseBrowser):
    DOMAIN = 'linuxfr.org'
    PROTOCOL = 'https'
    PAGES = {'https://linuxfr.org/': IndexPage,
             'https://linuxfr.org/pub/': IndexPage,
             'https://linuxfr.org/my/': IndexPage,
             'https://linuxfr.org/login.html': LoginPage,
             'https://linuxfr.org/.*/\d+.html': ContentPage
            }

    def __init__(self, *args, **kwargs):
        kwargs['parser'] = Parser()
        BaseBrowser.__init__(self, *args, **kwargs)

    def home(self):
        return self.location('https://linuxfr.org')

    def get_content(self, _id):
        self.location(id2url(_id))
        return self.page.get_article()

    def post_reply(self, thread, reply_id, title, message, is_html=False):
        content_type = id2contenttype(thread)
        thread_id = id2threadid(thread)
        thread_url = '%s://%s%s' % (self.PROTOCOL, self.DOMAIN, id2url(thread))
        reply_id = int(reply_id)

        if not content_type or not thread_id:
            return False

        url = '%s://%s/submit/comments,%d,%d,%d.html#post' % (self.PROTOCOL,
                                                              self.DOMAIN,
                                                              thread_id,
                                                              reply_id,
                                                              content_type)

        timestamp = ''
        if content_type == 1:
            res = self.openurl(url).read()
            const = 'name="timestamp" value="'
            i = res.find(const)
            if i >= 0:
                res = res[i + len(const):]
                timestamp = res[:res.find('"/>')]

        if is_html:
            format = 1
        else:
            format = 3

        # Define every data fields
        data = {'news_id': thread_id,
                'com_parent': reply_id,
                'timestamp': timestamp,
                'res_type': content_type,
                'referer': thread_url,
                'subject': unicode(title).encode('utf-8'),
                'body': unicode(message).encode('utf-8'),
                'format': format,
                'submit': 'Envoyer',
                }

        url = '%s://%s/submit/comments,%d,%d,%d.html#post' % (self.PROTOCOL, self.DOMAIN, thread_id, reply_id, content_type)

        request = self.request_class(url, urllib.urlencode(data), {'Referer': url})
        result = self.openurl(request)
        request = self.request_class(thread_url, None, {'Referer': result.geturl()})
        self.openurl(request).read()
        return None

    def login(self):
        self.location('/login.html', 'login=%s&passwd=%s&isauto=1' % (self.username, self.password))

    def is_logged(self):
        return (self.page and self.page.is_logged())

    def close_session(self):
        self.openurl('/close_session.html')

