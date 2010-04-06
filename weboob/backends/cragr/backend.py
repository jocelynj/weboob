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

from weboob.backend import Backend
from weboob.capabilities.bank import ICapBank, AccountNotFound

from .browser import Cragr

class CragrBackend(Backend, ICapBank):
    NAME = 'cragr'
    MAINTAINER = 'Romain Bignon'
    EMAIL = 'romain@peerfuse.org'
    VERSION = '1.0'
    LICENSE = 'GPLv3'

    CONFIG = {'login':    Backend.ConfigField(description='Account ID'),
              'password': Backend.ConfigField(description='Password of account', is_masked=True),
              'website':  Backend.ConfigField(description='What website to use', default='m.lefil.com'),
             }
    browser = None

    def need_browser(func):
        def inner(self, *args, **kwargs):
            if not self.browser:
                self.browser = Cragr(self.config['website'], self.config['login'], self.config['password'])

            return func(self, *args, **kwargs)
        return inner

    @need_browser
    def iter_accounts(self):
        for account in self.browser.get_accounts_list():
            yield account

    @need_browser
    def get_account(self, _id):
        try:
            _id = long(_id)
        except ValueError:
            raise AccountNotFound()
        else:
            account = self.browser.get_account(_id)
            if account:
                return account
            else:
                raise AccountNotFound()

    @need_browser
    def iter_operations(self, account):
        """ Not supported yet """
        return iter([])