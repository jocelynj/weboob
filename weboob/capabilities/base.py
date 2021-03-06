# -*- coding: utf-8 -*-

# Copyright(C) 2010  Christophe Benz, Romain Bignon
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


from weboob.tools.misc import iter_fields


__all__ = ['FieldNotFound', 'IBaseCap', 'NotAvailable', 'NotLoaded', 'CapBaseObject']


class FieldNotFound(Exception):
    def __init__(self, obj, field):
        Exception.__init__(self, u'Field "%s" not found for object %s' % (field, obj))


class NotAvailableMeta(type):
    def __str__(self):
        return unicode(self).decode('utf-8')

    def __unicode__(self):
        return u'Not available'

    def __nonzero__(self):
        return False


class NotAvailable(object):
    __metaclass__ = NotAvailableMeta


class NotLoadedMeta(type):
    def __str__(self):
        return unicode(self).decode('utf-8')

    def __unicode__(self):
        return u'Not loaded'

    def __nonzero__(self):
        return False


class NotLoaded(object):
    __metaclass__ = NotLoadedMeta


class IBaseCap(object):
    pass

class CapBaseObject(object):
    FIELDS = None
    _attribs = None

    def __init__(self, id, backend=None):
        self.id = id
        self.backend = backend

    def add_field(self, name, type, value=NotLoaded):
        """
        Add a field in list, which needs to be of type @type.

        @param name [str]  name of field
        @param type [class]  type accepted (can be a tuple of types)
        @param value [object]  value set to attribute (default is NotLoaded)
        """
        if not isinstance(self.FIELDS, list):
            self.FIELDS = []
        self.FIELDS.append(name)

        if self._attribs is None:
            self._attribs = {}
        self._attribs[name] = self._AttribValue(type, value)

    def __iscomplete__(self):
        """
        Return True if the object is completed.

        It is usefull when the object is a field of an other object which is
        going to be filled.

        The default behavior is to iter on fields (with iter_fields) and if
        a field is NotLoaded, return False.
        """
        for key, value in self.iter_fields():
            if value is NotLoaded:
                return False
        return True

    def iter_fields(self):
        """
        Iterate on the FIELDS keys and values.

        Can be overloaded to iterate on other things.

        @return [iter(key,value)]  iterator on key, value
        """

        if self.FIELDS is None:
            yield 'id', self.id
            for key, value in iter_fields(self):
                if key not in ('id', 'backend','FIELDS'):
                    yield key, value
        else:
            yield 'id', self.id
            for attrstr in self.FIELDS:
                yield attrstr, getattr(self, attrstr)

    def __eq__(self, obj):
        if isinstance(obj, CapBaseObject):
            return self.backend == obj.backend and self.id == obj.id
        else:
            return False

    class _AttribValue(object):
        def __init__(self, type, value):
            self.type = type
            self.value = value

    def __getattr__(self, name):
        if self._attribs is not None and name in self._attribs:
            return self._attribs[name].value
        else:
            raise AttributeError, "'%s' object has no attribute '%s'" % (self.__class__.__name__, name)

    def __setattr__(self, name, value):
        try:
            attr = (self._attribs or {})[name]
        except KeyError:
            object.__setattr__(self, name, value)
        else:
            if not isinstance(value, attr.type) and \
               value is not NotLoaded and \
               value is not NotAvailable and \
               value is not None:
                raise ValueError('Value for "%s" needs to be of type %r, not %r' % (name, attr.type, type(value)))
            attr.value = value
