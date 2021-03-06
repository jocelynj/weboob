#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from cStringIO import StringIO

selection = set()
dependencies = set()

for root, dirs, files in os.walk(sys.argv[1]):
    for f in files:
        if f.endswith('.py') and f != '__init__.py':
            s = "from %s import %s" % (root.strip('/').replace('/', '.'), f[:-3])
            try:
                exec s
            except ImportError, e:
                print >>sys.stderr, str(e)
            else:
                m = eval(f[:-3])
                for attrname in dir(m):
                    try:
                        attr = getattr(m, attrname)
                        selection.add(attr.__file__)
                    except AttributeError:
                        pass
for f in selection:
    f = f.replace('.pyc', '.py')
    try:
        f = os.path.abspath(os.path.join(os.path.split(f)[0], os.readlink(f)))
    except OSError:
        pass

    p = subprocess.Popen(['/usr/bin/dpkg', '-S', f], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.wait() == 0:
        for line in p.stdout.readlines():
            dependencies.add(line.strip().split(':')[0])
    else:
        print 'not found: %s' % f

for d in dependencies:
    print d
