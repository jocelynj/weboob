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


import urllib2
from xml.dom import minidom

# TODO store datetime objects instead of strings
# from datetime import datetime

from weboob.capabilities.weather import ICapWeather, CityNotFound, Current, Forecast
from weboob.tools.backend import BaseBackend


__all__ = ['YahooBackend']


class YahooBackend(BaseBackend, ICapWeather):
    NAME = 'yahoo'
    MAINTAINER = 'Romain Bignon'
    EMAIL = 'romain@weboob.org'
    VERSION = '0.4'
    DESCRIPTION = 'Yahoo'
    LICENSE = 'GPLv3'
    WEATHER_URL = 'http://weather.yahooapis.com/forecastrss?w=%s&u=%s'

    def iter_city_search(self, pattern):
        raise NotImplementedError()

    def _get_weather_dom(self, city_id):
        handler = urllib2.urlopen(self.WEATHER_URL % (city_id, 'c'))
        dom = minidom.parse(handler)
        handler.close()
        if not dom.getElementsByTagName('yweather:condition'):
            raise CityNotFound('City not found: %s' % city_id)

        return dom

    def get_current(self, city_id):
        dom = self._get_weather_dom(city_id)
        current = dom.getElementsByTagName('yweather:condition')[0]
        return Current(current.getAttribute('date'), int(current.getAttribute('temp')), current.getAttribute('text'), 'C')

    def iter_forecast(self, city_id):
        dom = self._get_weather_dom(city_id)
        for forecast in dom.getElementsByTagName('yweather:forecast'):
            yield Forecast(forecast.getAttribute('date'),
                           int(forecast.getAttribute('low')),
                           int(forecast.getAttribute('high')),
                           forecast.getAttribute('text'),
                           'C',
                           )
