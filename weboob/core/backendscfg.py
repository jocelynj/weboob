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


from __future__ import with_statement

import stat
import os
from ConfigParser import RawConfigParser, DuplicateSectionError
from logging import warning

__all__ = ['BackendsConfig', 'BackendAlreadyExists']

class BackendAlreadyExists(Exception):
    pass

class BackendsConfig(object):
    class WrongPermissions(Exception):
        pass

    def __init__(self, confpath):
        self.confpath = confpath
        try:
            mode = os.stat(confpath).st_mode
        except OSError:
            os.mknod(confpath, 0600)
        else:
            if mode & stat.S_IRGRP or mode & stat.S_IROTH:
                raise self.WrongPermissions(
                    u'Weboob will not start until config file %s is readable by group or other users.' % confpath)

    def iter_backends(self):
        config = RawConfigParser()
        config.read(self.confpath)
        for instance_name in config.sections():
            params = dict(config.items(instance_name))
            try:
                backend_name = params.pop('_backend')
            except KeyError:
                try:
                    backend_name = params.pop('_type')
                    warning(u'Please replace _type with _backend in your config file "%s", for backend "%s"' % (
                        self.confpath, backend_name))
                except KeyError:
                    warning('Missing field "_backend" for configured backend "%s"', instance_name)
                    continue
            yield instance_name, backend_name, params

    def add_backend(self, instance_name, backend_name, params, edit=False):
        if not instance_name:
            raise ValueError(u'Please give a name to the configured backend.')
        config = RawConfigParser()
        config.read(self.confpath)
        if not edit:
            try:
                config.add_section(instance_name)
            except DuplicateSectionError:
                raise BackendAlreadyExists(instance_name)
        config.set(instance_name, '_backend', backend_name)
        for key, value in params.iteritems():
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            config.set(instance_name, key, value)
        with open(self.confpath, 'wb') as f:
            config.write(f)

    def edit_backend(self, instance_name, backend_name, params):
        return self.add_backend(instance_name, backend_name, params, True)

    def get_backend(self, instance_name):
        config = RawConfigParser()
        config.read(self.confpath)
        if not config.has_section(instance_name):
            raise KeyError(u'Configured backend "%s" not found' % instance_name)

        items = dict(config.items(instance_name))

        try:
            backend_name = items.pop('_backend')
        except KeyError:
            try:
                backend_name = items.pop('_type')
                warning(u'Please replace _type with _backend in your config file "%s"' % self.confpath)
            except KeyError:
                warning('Missing field "_backend" for configured backend "%s"', instance_name)
                raise KeyError(u'Configured backend "%s" not found' % instance_name)
        return backend_name, items

    def remove_backend(self, instance_name):
        config = RawConfigParser()
        config.read(self.confpath)
        if not config.remove_section(instance_name):
            return False
        with open(self.confpath, 'w') as f:
            config.write(f)
        return True


