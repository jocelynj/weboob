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


from __future__ import with_statement

from copy import copy
from threading import Thread, Event, RLock, Timer

from weboob.capabilities.base import CapBaseObject
from weboob.tools.misc import get_backtrace
from weboob.tools.log import getLogger


__all__ = ['BackendsCall', 'CallErrors', 'IResultsCondition', 'ResultsConditionError']


class CallErrors(Exception):
    def __init__(self, errors):
        Exception.__init__(self, 'Errors during backend calls')
        self.errors = copy(errors)

    def __iter__(self):
        return self.errors.__iter__()

class IResultsCondition(object):
    def is_valid(self, obj):
        raise NotImplementedError()

class ResultsConditionError(Exception):
    pass

class BackendsCall(object):
    def __init__(self, backends, condition, function, *args, **kwargs):
        """
        @param backends  list of backends to call.
        @param condition  a IResultsCondition object. Can be None.
        @param function  backends' method name, or callable object.
        @param args, kwargs  arguments given to called functions.
        """
        self.logger = getLogger('bcall')
        # Store if a backend is finished
        self.backends = {}
        for backend in backends:
            self.backends[backend.name] = False
        # Condition
        self.condition = condition
        # Global mutex on object
        self.mutex = RLock()
        # Event set when every backends have give their data
        self.finish_event = Event()
        # Event set when there are new responses
        self.response_event = Event()
        # Waiting responses
        self.responses = []
        # Errors
        self.errors = []
        # Threads
        self.threads = []

        # Create jobs for each backend
        with self.mutex:
            for backend in backends:
                self.logger.debug('Creating a new thread for %s' % backend)
                self.threads.append(Timer(0, self._caller, (backend, function, args, kwargs)).start())
            if not backends:
                self.finish_event.set()

    def _store_error(self, backend, error):
        with self.mutex:
            backtrace = get_backtrace(error)
            self.errors.append((backend, error, backtrace))

    def _store_result(self, backend, result):
        with self.mutex:
            if isinstance(result, CapBaseObject):
                if self.condition and not self.condition.is_valid(result):
                    return
                result.backend = backend.name
            self.responses.append((backend, result))
            self.response_event.set()

    def _caller(self, backend, function, args, kwargs):
        self.logger.debug('%s: Thread created successfully' % backend)
        with backend:
            try:
                # Call method on backend
                try:
                    self.logger.debug('%s: Calling function %s' % (backend, function))
                    if callable(function):
                        result = function(backend, *args, **kwargs)
                    else:
                        result = getattr(backend, function)(*args, **kwargs)
                except Exception, error:
                    self.logger.debug('%s: Called function %s raised an error: %r' % (backend, function, error))
                    self._store_error(backend, error)
                else:
                    self.logger.debug('%s: Called function %s returned: %r' % (backend, function, result))

                    if hasattr(result, '__iter__') and not isinstance(result, basestring):
                        # Loop on iterator
                        try:
                            for subresult in result:
                                # Lock mutex only in loop in case the iterator is slow
                                # (for example if backend do some parsing operations)
                                self._store_result(backend, subresult)
                        except Exception, error:
                            self._store_error(backend, error)
                    else:
                        self._store_result(backend, result)
            finally:
                with self.mutex:
                    # This backend is now finished
                    self.backends[backend.name] = True
                    for finished in self.backends.itervalues():
                        if not finished:
                            return
                    self.response_event.set()
                    self.finish_event.set()

    def _callback_thread_run(self, callback, errback):
        responses = []
        while not self.finish_event.isSet() or self.response_event.isSet():
            self.response_event.wait()
            with self.mutex:
                responses = self.responses
                self.responses = []

                # Reset event
                self.response_event.clear()

            # Consume responses
            while responses:
                callback(*responses.pop(0))

        if errback:
            with self.mutex:
                while self.errors:
                    errback(*self.errors.pop(0))

        callback(None, None)

    def callback_thread(self, callback, errback=None):
        """
        Call this method to create a thread which will callback a
        specified function everytimes a new result comes.

        When the process is over, the function will be called with
        both arguments set to None.

        The functions prototypes:
            def callback(backend, result)
            def errback(backend, error)

        """
        thread = Thread(target=self._callback_thread_run, args=(callback, errback))
        thread.start()
        return thread

    def wait(self):
        self.finish_event.wait()

        with self.mutex:
            if self.errors:
                raise CallErrors(self.errors)

    def __iter__(self):
        # Don't know how to factorize with _callback_thread_run
        responses = []
        while not self.finish_event.isSet() or self.response_event.isSet():
            self.response_event.wait()
            with self.mutex:
                responses = self.responses
                self.responses = []

                # Reset event
                self.response_event.clear()

            # Consume responses
            while responses:
                yield responses.pop(0)

        # Raise errors
        with self.mutex:
            if self.errors:
                raise CallErrors(self.errors)
