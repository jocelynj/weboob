# -*- coding: utf-8 -*-

# Copyright(C) 2008-2010  Romain Bignon, Christophe Benz
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


import datetime
import time
import random
import urllib
try:
    import simplejson
except ImportError:
    # Python 2.6+ has a module similar to simplejson
    import json as simplejson

from weboob.tools.browser import BaseBrowser, BrowserUnavailable
from weboob.tools.parsers.html5libparser import Html5libParser

from weboob.backends.aum.exceptions import AdopteWait

from weboob.backends.aum.pages.account import AccountPage
from weboob.backends.aum.pages.home import HomePage
from weboob.backends.aum.pages.contact_list import ContactListPage
from weboob.backends.aum.pages.contact_thread import ContactThreadPage
from weboob.backends.aum.pages.baskets import BasketsPage
from weboob.backends.aum.pages.profile import ProfilePage
from weboob.backends.aum.pages.search import SearchPage
from weboob.backends.aum.pages.login import LoginPage, RedirectPage, BanPage, ErrPage, RegisterPage, \
                                            RegisterWaitPage, RegisterConfirmPage, ShopPage, InvitePage
from weboob.backends.aum.pages.edit import EditPhotoPage, EditPhotoCbPage, EditAnnouncePage, \
                                           EditDescriptionPage, EditSexPage, EditPersonalityPage
from weboob.backends.aum.pages.wait import WaitPage

from weboob.capabilities.chat import ChatException, ChatMessage


__all__ = ['AuMBrowser']


class AuMBrowser(BaseBrowser):
    DOMAIN = 'www.adopteunmec.com'
    ENCODING = 'iso-8859-1'
    PAGES = {'http://www.adopteunmec.com/': LoginPage,
             'http://www.adopteunmec.com/index.html': LoginPage,
             'http://www.adopteunmec.com/index.php': LoginPage,
             'http://www.adopteunmec.com/loginErr.php.*': ErrPage,
             'http://www.adopteunmec.com/bans.php.*': BanPage,
             'http://www.adopteunmec.com/redirect.php\?action=login': RedirectPage,
             'http://www.adopteunmec.com/wait.php': WaitPage,
             'http://www.adopteunmec.com/invits.php': InvitePage,
             'http://www.adopteunmec.com/register2.php': RegisterPage,
             'http://www.adopteunmec.com/register3.php.*': RegisterWaitPage,
             'http://www.adopteunmec.com/register4.php.*': RegisterConfirmPage,
             'http://www.adopteunmec.com/home.php': HomePage,
             'http://www.adopteunmec.com/shop2c.php': ShopPage,
             'http://www.adopteunmec.com/mails.php': ContactListPage,
             'http://www.adopteunmec.com/mails.php\?type=1': BasketsPage,
             'http://www.adopteunmec.com/thread.php\?id=([0-9]+)(&see=all)?': ContactThreadPage,
             'http://www.adopteunmec.com/edit.php\?type=1': EditPhotoPage,
             'http://s\d+.adopteunmec.com/upload\d.php\?.*': EditPhotoCbPage,
             'http://www.adopteunmec.com/edit.php\?type=2': EditAnnouncePage,
             'http://www.adopteunmec.com/edit.php\?type=3': EditDescriptionPage,
             'http://www.adopteunmec.com/edit.php\?type=4': EditSexPage,
             'http://www.adopteunmec.com/edit.php\?type=5': EditPersonalityPage,
             'http://www.adopteunmec.com/search.php.*': SearchPage,
             'http://www.adopteunmec.com/searchRes.php.*': SearchPage,
             'http://www.adopteunmec.com/rencontres-femmes/(.*)/([0-9]+)': ProfilePage,
             'http://www.adopteunmec.com/catalogue-hommes/(.*)/([0-9]+)': ProfilePage,
             'http://www.adopteunmec.com/view2.php': ProfilePage, # my own profile
             'http://www.adopteunmec.com/(\w+)': ProfilePage, # a custom profile url
             'http://www.adopteunmec.com/account.php': AccountPage,
            }

    def __init__(self, *args, **kwargs):
        kwargs['parser'] = Html5libParser(api='dom')
        BaseBrowser.__init__(self, *args, **kwargs)
        self.my_id = 0

    def id2url(self, _id):
        return u'%s://%s/%s' % (self.PROTOCOL, self.DOMAIN, _id)

    def login(self):
        if not self.is_on_page(LoginPage):
            self.home()
        self.page.login(self.username, self.password)

    def is_logged(self):
        return not self.is_on_page(LoginPage)

    def home(self):
        return self.location('http://www.adopteunmec.com/home.php')

    def pageaccess(func):
        def inner(self, *args, **kwargs):
            if self.is_on_page(WaitPage):
                if not self.page.check():
                    raise AdopteWait(u'Could not connect between 6pm and 1am.')
                self.home()
            if not self.page or self.is_on_page(LoginPage) and self.password:
                self.home()

            return func(self, *args, **kwargs)
        return inner

    def register(self, password, sex, birthday_d, birthday_m, birthday_y, zipcode, country, godfather=None):
        if not self.is_on_page(RegisterPage):
            self.location('http://www.adopteunmec.com/register2.php')
        self.page.register(password, sex, birthday_d, birthday_m, birthday_y, zipcode, country)
        if godfather:
            if not self.is_on_page(AccountPage):
                self.location('http://www.adopteunmec.com/account.php')
            self.page.set_godfather(godfather)

    @pageaccess
    def add_photo(self, name, f):
        if not self.is_on_page(EditPhotoPage):
            self.location('/edit.php?type=1')
        return self.page.add_photo(name, f)

    @pageaccess
    def set_nickname(self, nickname):
        if not self.is_on_page(EditAnnouncePage):
            self.location('/edit.php?type=2')
        return self.page.set_nickname(nickname)

    @pageaccess
    def set_announce(self, title=None, description=None, lookingfor=None):
        if not self.is_on_page(EditAnnouncePage):
            self.location('/edit.php?type=2')
        return self.page.set_announce(title, description, lookingfor)

    @pageaccess
    def set_description(self, **args):
        if not self.is_on_page(EditDescriptionPage):
            self.location('/edit.php?type=3')
        return self.page.set_description(**args)

    @pageaccess
    def score(self):
        if time.time() - self.last_update > 60:
            self.home()
        return self.page.score()

    @pageaccess
    def get_my_name(self):
        if time.time() - self.last_update > 60:
            self.home()
        return self.page.get_my_name()

    def get_my_id(self):
        if self.my_id:
            return self.my_id

        try:
            if not self.is_on_page(HomePage):
                self.home()
        except AdopteWait:
            self.location('/invits.php')

        self.my_id = self.page.get_my_id()
        return self.my_id

    @pageaccess
    def nb_new_mails(self):
        if time.time() - self.last_update > 60:
            self.home()
        return self.page.nb_new_mails()

    @pageaccess
    def nb_new_baskets(self):
        if time.time() - self.last_update > 60:
            self.home()
        return self.page.nb_new_baskets()

    @pageaccess
    def nb_new_visites(self):
        if time.time() - self.last_update > 60:
            self.home()
        return self.page.nb_new_visites()

    @pageaccess
    def nb_available_charms(self, reload=False):
        if reload or not self.is_on_page(HomePage):
            self.home()
        return self.page.nb_available_charms()

    @pageaccess
    def nb_godchilds(self, reload=False):
        if reload or not self.is_on_page(HomePage):
            self.home()
        return self.page.nb_godchilds()

    @pageaccess
    def get_baskets(self):
        self.location('/mails.php?type=1')
        return self.page.get_profiles_ids_list()

    @pageaccess
    def flush_visits(self):
        """ Does nothing, only flush new visits to increase my score """
        self.openurl('/mails.php?type=3')

    @pageaccess
    def get_threads_list(self):
        if not self.is_on_page(ContactListPage):
            self.location('/mails.php')

        return self.page.get_contact_list()

    @pageaccess
    def get_thread_mails(self, id, full=False):
        if not self.is_on_page(ContactThreadPage) or self.page.id != int(id) or full:
            self.page.open_thread_page(id, full)
        return self.page.mails

    @pageaccess
    def post_mail(self, id, content):
        if not self.is_on_page(ContactThreadPage) or self.page.id != int(id):
            self.page.open_thread_page(id)
        self.page.post(content)

    @pageaccess
    def delete_thread(self, id):
        data = 'delete=true&suppr%%5B%%5D=%s' % id
        url = 'http://www.adopteunmec.com/mail.php'
        self.openurl(url, data).read()

        return True

    @pageaccess
    def send_charm(self, id):
        result = self.openurl('http://www.adopteunmec.com/fajax_addBasket.php?id=%s' % id).read()
        self.logger.debug('Charm: %s' % result)
        return result.find('noMoreFlashes') < 0

    @pageaccess
    def add_basket(self, id):
        result = self.openurl('http://www.adopteunmec.com/fajax_addBasket.php?id=%s' % id).read()
        self.logger.debug('Basket: %s' % result)
        # TODO check if it works (but it should)
        return True

    @pageaccess
    def deblock(self, id):
        self.readurl('http://www.adopteunmec.com/fajax_postMessage.php?action=deblock&to=%s' % id)
        return True

    @pageaccess
    def report_fake(self, id):
        return self.readurl('http://www.adopteunmec.com/fake.php', 'id=%s' % id)

    @pageaccess
    def rate(self, id, what, rating):
        result = self.openurl('http://www.adopteunmec.com/fajax_vote.php', 'member=%s&what=%s&rating=%s' % (id, what, rating)).read()
        return float(result)

    @pageaccess
    def search_profiles(self, **kwargs):
        self.location('/search.php?display=1')
        self.page.search(**kwargs)
        return self.page.get_profiles_ids()

    @pageaccess
    def get_profile(self, link):
        if isinstance(link, basestring):
            link = link.replace('http://www.adopteunmec.com/', '')
            if link.startswith('/'):
                link = link[1:]
        self.location('/%s' % link)
        return self.page

    @pageaccess
    def get_slut_state(self, id):
        result = self.openurl('http://www.adopteunmec.com/%s' % id).read()
        if result.find('<td align="right" style="font-size:12px;font-weight:bold">en ligne</td>') >= 0:
            r = 'online'
        elif result.find('Cet utilisateur a quitt\xe9 le site<br />') >= 0:
            r = 'removed'
        elif result.find('ce profil a \xe9t\xe9 bloqu\xe9 par l\'\xe9quipe de mod\xe9ration<br />') >= 0:
            r = 'removed'
        elif result.find('<div align=center style="color:#ff0000;font-size:16px"><br /><br />Cette personne<br>vous a bloqu\xe9</div>') >= 0:
            r = 'blocked'
        else:
            r = 'offline'

        print 'getSlutState(%s) = %s' % (id, r)
        return r

    @pageaccess
    def is_slut_online(self, id):
        result = self.openurl('http://www.adopteunmec.com/%s' % id).read()
        r = result.find('<td align="right" style="font-size:12px;font-weight:bold">en ligne</td>') >= 0
        print 'isSlutOnline(%s) = %s' % (id, r)
        return r

    def _get_chat_infos(self):
        try:
            json = simplejson.load(self.openurl('http://www.adopteunmec.com/1.1_cht_get.php?anticache=%f' % random.random()))
        except ValueError:
            raise BrowserUnavailable()

        if json['error']:
            raise ChatException(u'Error while getting chat infos. json:\n%s' % json)
        return json

    def iter_contacts(self):
        def iter_dedupe(contacts):
            yielded_ids = set()
            for contact in contacts:
                if contact['id'] not in yielded_ids:
                    yield contact
                yielded_ids.add(contact['id'])

        json = self._get_chat_infos()
        return iter_dedupe(json['contacts'])

    def iter_chat_messages(self, _id=None):
        json = self._get_chat_infos()
        if json['messages'] is not None:
            for message in json['messages']:
                yield ChatMessage(id_from=message['id_from'], id_to=message['id_to'], message=message['message'], date=message['date'])

    def send_chat_message(self, _id, message):
        url = 'http://www.adopteunmec.com/1.1_cht_send.php?anticache=%f' % random.random()
        data = dict(id=_id, message=message)
        headers = {
                'Content-type': 'application/x-www-form-urlencoded',
                'Accept': 'text/plain',
                'Referer': 'http://www.adopteunmec.com/chat.php',
                'Origin': 'http://www.adopteunmec.com',
                }
        request = self.request_class(url, urllib.urlencode(data), headers)
        response = self.openurl(request).read()
        try:
            datetime.datetime.strptime(response,  '%Y-%m-%d %H:%M:%S')
            return True
        except ValueError:
            return False
