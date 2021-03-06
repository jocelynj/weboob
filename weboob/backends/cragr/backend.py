# -*- coding: utf-8 -*-

# Copyright(C) 2010  Romain Bignon, Christophe Benz
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


from weboob.capabilities.bank import ICapBank, AccountNotFound
from weboob.tools.backend import BaseBackend
from weboob.tools.ordereddict import OrderedDict
from weboob.tools.value import ValuesDict, Value

from .browser import Cragr


__all__ = ['CragrBackend']


class CragrBackend(BaseBackend, ICapBank):
    NAME = 'cragr'
    MAINTAINER = 'Xavier Guerrin'
    EMAIL = 'xavier@tuxfamily.org'
    VERSION = '0.4'
    DESCRIPTION = 'Credit Agricole french bank\'s website'
    LICENSE = 'GPLv3'
    website_choices = OrderedDict([(k, u'%s (%s)' % (v, k)) for k, v in sorted({
        'm.ca-alpesprovence.fr': u'Alpes Provence',
        'm.ca-anjou-maine.fr': u'Anjou Maine',
        'm.ca-atlantique-vendee.fr': u'Atlantique Vendée',
        'm.ca-aquitaine.fr': u'Aquitaine',
        'm.ca-briepicardie.fr': u'Brie Picardie',
        'm.ca-centrefrance.fr': u'Centre France',
        'm.ca-centreloire.fr': u'Centre Loire',
        'm.ca-centreouest.fr': u'Centre Ouest',
        'm.ca-cb.fr': u'Champagne Bourgogne',
        'm.ca-charente-perigord.fr': u'Charente Périgord',
        'm.ca-cmds.fr': u'Charente-Maritime Deux-Sèvres',
        'm.ca-corse.fr': u'Corse',
        'm.ca-cotesdarmor.fr': u'Côtes d\'Armor',
        'm.ca-des-savoie.fr': u'Des Savoie',
        'm.ca-finistere.fr': u'Finistere',
        'm.ca-paris.fr': u'Ile-de-France',
        'm.ca-illeetvilaine.fr': u'Ille-et-Vilaine',
        'm.ca-languedoc.fr': u'Languedoc',
        'm.ca-loirehauteloire.fr': u'Loire Haute Loire',
        'm.ca-lorraine.fr': u'Lorraine',
        'm.ca-martinique.fr': u'Martinique Guyane',
        'm.ca-morbihan.fr': u'Morbihan',
        'm.ca-norddefrance.fr': u'Nord de France',
        'm.ca-nord-est.fr': u'Nord Est',
        'm.ca-nmp.fr': u'Nord Midi-Pyrénées',
        'm.ca-normandie.fr': u'Normandie',
        'm.ca-normandie-seine.fr': u'Normandie Seine',
        'm.ca-pca.fr': u'Provence Côte d\'Azur',
        'm.lefil.com': u'Pyrénées Gascogne',
        'm.ca-reunion.fr': u'Réunion',
        'm.ca-sudrhonealpes.fr': u'Sud Rhône Alpes',
        'm.ca-sudmed.fr': u'Sud Méditerranée',
        'm.ca-toulouse31.fr': u'Toulouse 31', # m.ca-toulousain.fr redirects here
        'm.ca-tourainepoitou.fr': u'Tourraine Poitou',
        }.iteritems())])
    CONFIG = ValuesDict(Value('website',  label='Website to use', choices=website_choices),
                        Value('login',    label='Account ID'),
                        Value('password', label='Password', masked=True))
    BROWSER = Cragr

    def create_default_browser(self):
        return self.create_browser(self.config['website'], self.config['login'], self.config['password'])

    def iter_accounts(self):
        for account in self.browser.get_accounts_list():
            yield account

    def get_account(self, _id):
        if not _id.isdigit():
            raise AccountNotFound()
        account = self.browser.get_account(_id)
        if account:
            return account
        else:
            raise AccountNotFound()

    def iter_history(self, account):
        for history in self.browser.get_history(account):
            yield history


    def transfer(self, account, to, amount, reason=None):
        return self.browser.do_transfer(account, to, amount, reason)
