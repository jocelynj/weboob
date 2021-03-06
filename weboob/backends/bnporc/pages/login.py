# -*- coding: utf-8 -*-

# Copyright(C) 2009-2010  Romain Bignon
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


from weboob.tools.mech import ClientForm
import urllib
from logging import error

from weboob.tools.browser import BasePage, BrowserUnavailable
from weboob.backends.bnporc.captcha import Captcha, TileError


__all__ = ['LoginPage', 'ConfirmPage', 'ChangePasswordPage']


class LoginPage(BasePage):
    def on_loaded(self):
        for td in self.document.getroot().cssselect('td.LibelleErreur'):
            if td.text is None:
                continue
            msg = td.text.strip()
            if 'indisponible' in msg:
                raise BrowserUnavailable(msg)

    def login(self, login, password):
        img = Captcha(self.browser.openurl('/NSImgGrille'))

        try:
            img.build_tiles()
        except TileError, err:
            error("Error: %s" % err)
            if err.tile:
                err.tile.display()

        self.browser.select_form('logincanalnet')
        # HACK because of fucking malformed HTML, the field isn't recognized by mechanize.
        self.browser.controls.append(ClientForm.TextControl('text', 'ch1', {'value': ''}))
        self.browser.set_all_readonly(False)

        self.browser['ch1'] = login
        self.browser['ch5'] = img.get_codes(password)
        self.browser.submit()

class ConfirmPage(BasePage):
    pass

class ChangePasswordPage(BasePage):
    def change_password(self, current, new):
        img = Captcha(self.browser.openurl('/NSImgGrille'))

        try:
            img.build_tiles()
        except TileError, err:
            error('Error: %s' % err)
            if err.tile:
                err.tile.display()

        code_current = img.get_codes(current)
        code_new = img.get_codes(new)

        data = {'ch1': code_current,
                'ch2': code_new,
                'ch3': code_new
               }

        self.browser.location('/SAF_CHM_VALID', urllib.urlencode(data))
