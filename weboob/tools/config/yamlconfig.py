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

from __future__ import with_statement

import yaml

from .iconfig import IConfig, ConfigError

class YamlConfig(IConfig):
    def __init__(self, path):
        self.path = path
        self.values = {}

    def load(self, default={}):
        self.values = default.copy()

        try:
            with open(self.path, 'r') as f:
                self.values = yaml.load(f)
        except IOError:
            pass

        if self.values is None:
            self.values = {}

    def save(self):
        with open(self.path, 'w') as f:
            yaml.dump(self.values, f)

    def get(self, *args, **kwargs):
        default = None
        if 'default' in kwargs:
            default = kwargs['default']

        v = self.values
        for a in args[:-1]:
            try:
                v = v[a]
            except KeyError:
                if not default is None:
                    v[a] = {}
                    v = v[a]
                else:
                    raise ConfigError()
            except TypeError:
                raise ConfigError()

        try:
            v = v[args[-1]]
        except KeyError:
            v[args[-1]] = default
            v = v[args[-1]]

        return v

    def set(self, *args):
        v = self.values
        for a in args[:-2]:
            try:
                v = v[a]
            except KeyError:
                v[a] = {}
                v = v[a]
            except TypeError:
                raise ConfigError()

        v[args[-2]] = args[-1]