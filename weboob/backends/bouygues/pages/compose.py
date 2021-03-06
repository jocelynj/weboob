# -*- coding: utf-8 -*-

# Copyright(C) 2010  Christophe Benz
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


import re

from weboob.capabilities.messages import CantSendMessage
from weboob.tools.browser import BasePage
#from weboob.tools.parsers.lxmlparser import select, SelectElementException


__all__ = ['ComposeFrame', 'ComposePage', 'ConfirmPage', 'SentPage']


class ComposeFrame(BasePage):
    phone_regex = re.compile('^(\+33|0033|0)(6|7)(\d{8})$')

    def post_message(self, message):
        receiver_list = [re.sub(' +', '', receiver) for receiver in message.receivers]
        for receiver in receiver_list:
            if self.phone_regex.match(receiver) is None:
                raise CantSendMessage(u'Invalid receiver: %s' % receiver)
        self.browser.select_form(nr=0)
        self.browser['fieldMsisdn'] = ','.join(receiver_list)
        self.browser['fieldMessage'] = message.content
        self.browser.submit()


class ComposePage(BasePage):
    pass


class ConfirmPage(BasePage):
    def confirm(self):
        self.browser.location('http://www.mobile.service.bbox.bouyguestelecom.fr/services/SMSIHD/resultSendSMS.phtml')


class SentPage(BasePage):
    pass
