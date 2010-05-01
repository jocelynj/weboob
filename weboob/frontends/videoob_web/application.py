# -*- coding: utf-8 -*-

"""
Copyright(C) 2010  Christophe Benz

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

import os

from mako.lookup import TemplateLookup
from mako.runtime import Context
from routes import Mapper
from StringIO import StringIO
from webob.dec import wsgify
from webob import exc
from wsgiref.simple_server import make_server

from weboob.capabilities.video import ICapVideoProvider
from weboob.tools.application import BaseApplication


__all__ = ['VideoobWeb']


template_lookup = TemplateLookup(directories=[os.path.join(os.path.dirname(__file__), 'templates')],
                                 output_encoding='utf-8', encoding_errors='replace')


class VideoobWeb(BaseApplication):
    APPNAME = 'videoob-web'
    CONFIG = dict(host='localhost', port=8080)

    @wsgify
    def make_app(self, req):
        map = Mapper()
        map.connect('index', '/', method='index')

        results = map.routematch(environ=req.environ)
        if results:
            match, route = results
            req.urlvars = ((), match)
            kwargs = match.copy()
            method = kwargs.pop('method')
            return getattr(self, method)(req, **kwargs)
        else:
            public_path = os.path.join(os.path.dirname(__file__), 'public')
            if not os.path.exists(public_path):
                return exc.HTTPNotFound()
            path = req.path
            if path.startswith('/'):
                path = path[1:]
            public_file_path = os.path.join(public_path, path)
            if os.path.exists(public_file_path):
                if path.endswith('.css'):
                    req.response.content_type = 'text/css'
                elif path.endswith('.js'):
                    req.response.content_type = 'text/javascript'
                return open(public_file_path, 'r').read().strip()
            else:
                return exc.HTTPNotFound()

    def main(self, argv):
        self.load_config()
        self.weboob.load_modules(ICapVideoProvider)
        print 'Web server created. Listening on http://%s:%s' % (
            self.config.get('host'), int(self.config.get('port')))
        srv = make_server(self.config.get('host'), int(self.config.get('port')), self.make_app)
        srv.serve_forever()

    def index(self, req):
        c = {}
        nsfw = req.params.get('nsfw')
        nsfw = False if not nsfw or nsfw == '0' else True
        q = req.params.get('q', u'')
        merge = req.params.get('merge')
        merge = False if not merge or merge == '0' else True
        c['merge'] = merge
        c['form_data'] = dict(q=q)
        c['results'] = [] if merge else {}
        if q:
            for backend in self.weboob.iter_backends():
                videos = [dict(title=video.title,
                               page_url=video.page_url,
                               url=video.url if video.url else '/download?id=%s' % video.id,
                               thumbnail_url=video.thumbnail_url,
                             ) \
                         for video in backend.iter_search_results(pattern=q, nsfw=nsfw)]
                if videos:
                    if merge:
                        c['results'].extend(videos)
                    else:
                        c['results'][backend.name] = videos
            if merge:
                c['results'] = sorted(c['results'], key=lambda video: video['title'].lower())
        template = template_lookup.get_template('index.mako')
        buf = StringIO()
        ctx = Context(buf, **c)
        template.render_context(ctx)
        return buf.getvalue().strip()