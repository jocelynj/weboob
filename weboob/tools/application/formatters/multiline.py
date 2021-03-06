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


from weboob.capabilities.base import NotLoaded, NotAvailable
from .iformatter import IFormatter


__all__ = ['MultilineFormatter']


class MultilineFormatter(IFormatter):
    def __init__(self, key_value_separator=u': ', after_item=u'\n'):
        IFormatter.__init__(self)
        self.key_value_separator = key_value_separator
        self.after_item = after_item

    def flush(self):
        pass

    def format_dict(self, item):
        result = u'\n'.join(u'%s%s' % (
            (u'%s%s' % (k, self.key_value_separator) if self.display_keys else ''), v)
            for k, v in item.iteritems() if (v is not NotLoaded and v is not NotAvailable))
        if len(item) > 1:
            result += self.after_item
        return result

    def set_header(self, string):
        if self.display_header:
            print string.encode('utf-8')
