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


class ConfigError(Exception):
    pass


class IConfig:
    def load(self, default={}):
        raise NotImplementedError()

    def save(self):
        raise NotImplementedError()

    def set(self, *args):
        raise NotImplementedError()

    def delete(self, *args):
        raise NotImplementedError()

    def get(self, *args, **kwargs):
        raise NotImplementedError()
