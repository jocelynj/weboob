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

from weboob.tools.browser import BrowserUnavailable
from weboob.capabilities.dating import Optimization
from weboob.tools.log import getLogger


__all__ = ['QueriesQueue']


class QueriesQueue(Optimization):
    def __init__(self, sched, storage, browser):
        self.sched = sched
        self.storage = storage
        self.browser = browser
        self.logger = getLogger('queriesqueue', browser.logger)

        self.queue = storage.get('queries_queue', 'queue', default=[])

        self.check_cron = None

    def save(self):
        self.storage.set('queries_queue', 'queue', self.queue)
        self.storage.save()

    def start(self):
        self.check_cron = self.sched.repeat(3600, self.flush_queue)
        return True

    def stop(self):
        self.sched.cancel(self.check_cron)
        self.check_cron = None
        return True

    def is_running(self):
        return self.check_cron is not None

    def enqueue_query(self, id, priority=999):
        self.queue.append((int(priority), int(id)))
        self.save()
        # Try to flush queue to send it now.
        self.flush_queue()

        # Check if the enqueued query has been sent
        for p, i in self.queue:
            if i == int(id):
                return False
        return True

    def flush_queue(self):
        self.queue.sort()

        priority = 0
        id = None

        try:
            try:
                while len(self.queue) > 0:
                    priority, id = self.queue.pop()

                    if not id:
                        continue

                    with self.browser:
                        if self.browser.send_charm(id):
                            self.logger.info('Charm sent to %s' % id)
                        else:
                            self.queue.append((priority, id))
                            self.logger.info("Charm can't be send to %s" % id)
                            break

                    # As the charm has been correctly sent (no exception raised),
                    # we don't store anymore ID, because if nbAvailableCharms()
                    # fails, we don't want to re-queue this ID.
                    id = None
                    priority = 0

            except BrowserUnavailable:
                # We consider this profil hasn't been [correctly] analysed
                if not id is None:
                    self.queue.append((priority, id))
        finally:
            self.save()
