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

from weboob.backend import Backend
from weboob.capabilities.travel import ICapTravel, Station, Departure

from .browser import CanalTP

class CanalTPBackend(Backend, ICapTravel):
    MAINTAINER = 'Romain Bignon'
    EMAIL = 'romain@peerfuse.org'
    VERSION = '1.0'

    def __init__(self, weboob):
        Backend.__init__(self, weboob)

    def iter_station_search(self, pattern):
        canaltp = CanalTP()
        for _id, name in canaltp.iter_station_search(pattern):
            yield Station(_id, name)

    def iter_station_departures(self, station_id, arrival_id=None):
        canaltp = CanalTP()
        for i, d in enumerate(canaltp.iter_station_departures(station_id, arrival_id)):
            departure = Departure(i, d['type'], d['time'])
            departure.departure_station = d['departure']
            departure.arrival_station = d['arrival']
            departure.late = d['late']
            departure.information = d['late_reason']
            yield departure