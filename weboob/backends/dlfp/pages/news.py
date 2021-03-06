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


from datetime import datetime
from logging import warning

from weboob.tools.misc import local2utc
from weboob.backends.dlfp.tools import url2id

from .index import DLFPPage

class Comment(object):
    def __init__(self, browser, div, reply_id):
        self.browser = browser
        self.id = ''
        self.reply_id = reply_id
        self.title = u''
        self.author = u''
        self.date = None
        self.body = u''
        self.score = 0
        self.url = u''
        self.comments = []

        for sub in div.getchildren():
            if sub.tag == 'a':
                self.id = sub.attrib['name']
                self.url = u'https://linuxfr.org/comments/%s.html#%s' % (self.id, self.id)
            elif sub.tag == 'h1':
                try:
                    self.title = sub.find('b').text
                except UnicodeError:
                    warning('Bad encoded title, but DLFP sucks')
            elif sub.tag == 'div' and sub.attrib.get('class', '').startswith('comment'):
                self.author = sub.find('a').text if sub.find('a') is not None else 'Unknown'
                self.date = self.parse_date(sub.find('i').tail)
                self.score = int(sub.findall('i')[-1].find('span').text)
                self.body = self.browser.parser.tostring(sub.find('p'))
            elif sub.attrib.get('class', '') == 'commentsul':
                comment = Comment(self.browser, sub.find('li'), self.id)
                self.comments.append(comment)

    def parse_date(self, date_s):
        date_s = date_s.strip().encode('utf-8')
        if not date_s:
            date = datetime.now()
        else:
            date = datetime.strptime(date_s, u'le %d/%m/%Y \xe0 %H:%M.'.encode('utf-8'))
        return local2utc(date)

    def iter_all_comments(self):
        for comment in self.comments:
            yield comment
            for c in comment.iter_all_comments():
                yield c

    def __repr__(self):
        return u"<Comment id='%s' author='%s' title='%s'>" % (self.id, self.author, self.title)

class Article(object):
    def __init__(self, browser, _id, tree):
        self.browser = browser
        self.id = _id
        self.title = u''
        self.author = u''
        self.body = u''
        self.part2 = u''
        self.date = None
        self.url = u''
        self.comments = []

        for div in tree.findall('div'):
            if div.attrib.get('class', '').startswith('titlediv '):
                self.author = div.find('a').text
                for a in div.find('h1').getiterator('a'):
                    if a.text: self.title += a.text
                    if a.tail: self.title += a.tail
                self.title = self.title.strip()
                # TODO use the date_s
                #subdivs = div.findall('a')
                #if len(subdivs) > 1:
                #    date_s = unicode(subdivs[1].text)
                #else:
                #    date_s = unicode(div.find('i').tail)
            if div.attrib.get('class', '').startswith('bodydiv '):
                self.body = self.browser.parser.tostring(div)

    def append_comment(self, comment):
        self.comments.append(comment)

    def iter_all_comments(self):
        for comment in self.comments:
            yield comment
            for c in comment.iter_all_comments():
                yield c

    def parse_part2(self, div):
        self.part2 = self.browser.parser.tostring(div)

class ContentPage(DLFPPage):
    def on_loaded(self):
        self.article = None
        for div in self.document.find('body').find('div').findall('div'):
            self.parse_div(div)
            if div.attrib.get('class', '') == 'centraldiv':
                for subdiv in div.findall('div'):
                    self.parse_div(subdiv)

    def parse_div(self, div):
        if div.attrib.get('class', '') in ('newsdiv', 'centraldiv'):
            self.article = Article(self.browser, url2id(self.url), div)
            self.article.url = self.url
        if div.attrib.get('class', '') == 'articlediv':
            self.article.parse_part2(div)
        if div.attrib.get('class', '') == 'comments':
            comment = Comment(self.browser, div, 0)
            self.article.append_comment(comment)

    def get_article(self):
        return self.article
