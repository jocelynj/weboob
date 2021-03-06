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


from .base import IBaseCap, CapBaseObject


__all__ = ['City', 'CityNotFound', 'Current', 'Forecast', 'ICapWeather']


class Forecast(CapBaseObject):
    def __init__(self, date, low, high, text, unit):
        CapBaseObject.__init__(self, date)
        self.date = date
        self.low = low
        self.high = high
        self.text = text
        self.unit = unit


class Current(CapBaseObject):
    def __init__(self, date, temp, text, unit):
        CapBaseObject.__init__(self, date)
        self.date = date
        self.temp = temp
        self.text = text
        self.unit = unit


class City(CapBaseObject):
    def __init__(self, id, name):
        self.id = id
        self.name = name


class CityNotFound(Exception):
    pass


class ICapWeather(IBaseCap):
    def iter_city_search(self, pattern):
        raise NotImplementedError()

    def get_current(self, city_id):
        raise NotImplementedError()

    def iter_forecast(self, city_id):
        raise NotImplementedError()
