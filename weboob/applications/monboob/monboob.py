# -*- coding: utf-8 -*-

# Copyright(C) 2009-2010  Romain Bignon, Christophe Benz
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


from email.mime.text import MIMEText
from smtplib import SMTP
from email.Header import Header, decode_header
from email.Utils import parseaddr, formataddr, formatdate
from email import message_from_file, message_from_string
from smtpd import SMTPServer
import time
import re
import sys
import logging
import asyncore
import subprocess

from weboob.core import Weboob, CallErrors
from weboob.core.scheduler import Scheduler
from weboob.capabilities.messages import ICapMessages, ICapMessagesPost, Thread, Message
from weboob.tools.application.repl import ReplApplication
from weboob.tools.misc import html2text, get_backtrace, utc2local


__all__ = ['Monboob']

class FakeSMTPD(SMTPServer):
    def __init__(self, app, bindaddr, port):
        SMTPServer.__init__(self, (bindaddr, port), None)
        self.app = app

    def process_message(self, peer, mailfrom, rcpttos, data):
        msg = message_from_string(data)
        self.app.process_incoming_mail(msg)

class MonboobScheduler(Scheduler):
    def __init__(self, app):
        Scheduler.__init__(self)
        self.app = app

    def run(self):
        if self.app.options.smtpd:
            if ':' in self.app.options.smtpd:
                host, port = self.app.options.smtpd.split(':', 1)
            else:
                host = '127.0.0.1'
                port = self.app.options.smtpd
            FakeSMTPD(self.app, host, int(port))

        # XXX Fuck, we shouldn't copy this piece of code from
        # weboob.scheduler.Scheduler.run().
        try:
            while 1:
                self.stop_event.wait(0.1)
                if self.app.options.smtpd:
                    asyncore.loop(timeout=0.1, count=1)
        except KeyboardInterrupt:
            self._wait_to_stop()
            raise
        else:
            self._wait_to_stop()
        return True


class Monboob(ReplApplication):
    APPNAME = 'monboob'
    VERSION = '0.4'
    COPYRIGHT = 'Copyright(C) 2010 Romain Bignon'
    CONFIG = {'interval':  300,
              'domain':    'weboob.example.org',
              'recipient': 'weboob@example.org',
              'smtp':      'localhost',
              'pipe':      '',
              'html':      0}
    CAPS = ICapMessages
    DISABLE_REPL = True

    def add_application_options(self, group):
        group.add_option('-S', '--smtpd', help='run a fake smtpd server and set the port')

    def create_weboob(self):
        return Weboob(scheduler=MonboobScheduler(self))

    def load_default_backends(self):
        self.load_backends(ICapMessages, storage=self.create_storage())

    def main(self, argv):
        self.load_config()

        return ReplApplication.main(self, argv)

    def get_email_address_ident(self, msg, header):
        s = msg.get(header)
        m = re.match('.*<([^@]*)@(.*)>', s)
        if m:
            return m.group(1)
        else:
            try:
                return s.split('@')[0]
            except IndexError:
                return s

    def do_post(self, line):
        """
        post

        Pipe with a mail to post message.
        """
        msg = message_from_file(sys.stdin)
        return self.process_incoming_mail(msg)

    def process_incoming_mail(self, msg):
        to = self.get_email_address_ident(msg, 'To')
        reply_to = self.get_email_address_ident(msg, 'In-Reply-To')
        if not reply_to:
            print >>sys.stderr, 'This is not a reply (no Reply-To field)'
            return 1

        title = msg.get('Subject')
        if title:
            new_title = u''
            for part in decode_header(title):
                if part[1]:
                    new_title += unicode(part[0], part[1])
                else:
                    new_title += unicode(part[0])
            title = new_title

        content = u''
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                s = part.get_payload(decode=True)
                charsets = part.get_charsets() + msg.get_charsets()
                for charset in charsets:
                    try:
                        if charset is not None:
                            content += unicode(s, charset)
                        else:
                            content += unicode(s)
                    except UnicodeError, e:
                        self.logger.warning('Unicode error: %s' % e)
                        continue
                    except Exception, e:
                        self.logger.exception(e)
                        continue
                    else:
                        break

        if len(content) == 0:
            print >>sys.stderr, 'Unable to send an empty message'
            return 1

        # remove signature
        content = content.split(u'\n-- \n')[0]

        bname, id = reply_to.split('.', 1)

        # Default use the To header field to know the backend to use.
        if to and bname != to:
            bname = to

        try:
            backend = self.weboob.backend_instances[bname]
        except KeyError:
            print >>sys.stderr, 'Backend %s not found' % bname
            return 1

        if not backend.has_caps(ICapMessagesPost):
            print >>sys.stderr, 'The backend %s does not implement ICapMessagesPost' % bname
            return 1

        thread_id, msg_id = id.rsplit('.', 1)
        thread = Thread(thread_id)
        message = Message(thread,
                          0,
                          title=title,
                          sender=None,
                          receivers=None,
                          parent=Message(thread, msg_id),
                          content=content)
        try:
            backend.post_message(message)
        except Exception, e:
            content = u'Unable to send message to %s:\n' % thread_id
            content += u'\n\t%s\n' % e
            if logging.root.level == logging.DEBUG:
                content += u'\n%s\n' % get_backtrace(e)
            self.send_email(backend, Message(thread,
                                             0,
                                             title='Unable to send message',
                                             sender='Monboob',
                                             parent=Message(thread, msg_id),
                                             content=content))

    def do_run(self, line):
        """
        run

        Run the fetching daemon.
        """
        self.weboob.repeat(int(self.config.get('interval')), self.process)
        self.weboob.loop()

    def process(self):
        try:
            for backend, message in self.weboob.do('iter_unread_messages'):
                if self.send_email(backend, message):
                    backend.set_message_read(message)
        except CallErrors, e:
            self.bcall_errors_handler(e)

    def send_email(self, backend, mail):
        domain = self.config.get('domain')
        recipient = self.config.get('recipient')

        reply_id = ''
        if mail.parent:
            reply_id = u'<%s.%s@%s>' % (backend.name, mail.parent.full_id, domain)
        subject = mail.title
        sender = u'"%s" <%s@%s>' % (mail.sender.replace('"', '""'), backend.name, domain)

        # assume that .date is an UTC datetime
        date = formatdate(time.mktime(utc2local(mail.date).timetuple()), localtime=True)
        msg_id = u'<%s.%s@%s>' % (backend.name, mail.full_id, domain)

        if int(self.config.get('html')) and mail.flags & mail.IS_HTML:
            body = mail.content
            content_type = 'html'
        else:
            if mail.flags & mail.IS_HTML:
                body = html2text(mail.content)
            else:
                body = mail.content
            content_type = 'plain'

        if mail.signature:
            if int(self.config.get('html')) and mail.flags & mail.IS_HTML:
                body += u'<p>-- <br />%s</p>' % mail.signature
            else:
                body += u'\n\n-- \n'
                if mail.flags & mail.IS_HTML:
                    body += html2text(mail.signature)
                else:
                    body += mail.signature

        # Header class is smart enough to try US-ASCII, then the charset we
        # provide, then fall back to UTF-8.
        header_charset = 'ISO-8859-1'

        # We must choose the body charset manually
        for body_charset in 'US-ASCII', 'ISO-8859-1', 'UTF-8':
            try:
                body.encode(body_charset)
            except UnicodeError:
                pass
            else:
                break

        # Split real name (which is optional) and email address parts
        sender_name, sender_addr = parseaddr(sender)
        recipient_name, recipient_addr = parseaddr(recipient)

        # We must always pass Unicode strings to Header, otherwise it will
        # use RFC 2047 encoding even on plain ASCII strings.
        sender_name = str(Header(unicode(sender_name), header_charset))
        recipient_name = str(Header(unicode(recipient_name), header_charset))

        # Make sure email addresses do not contain non-ASCII characters
        sender_addr = sender_addr.encode('ascii')
        recipient_addr = recipient_addr.encode('ascii')

        # Create the message ('plain' stands for Content-Type: text/plain)
        msg = MIMEText(body.encode(body_charset), content_type, body_charset)
        msg['From'] = formataddr((sender_name, sender_addr))
        msg['To'] = formataddr((recipient_name, recipient_addr))
        msg['Subject'] = Header(unicode(subject), header_charset)
        msg['Message-Id'] = msg_id
        msg['Date'] = date
        if reply_id:
            msg['In-Reply-To'] = reply_id

        self.logger.info('Send mail from <%s> to <%s>' % (sender, recipient))
        if len(self.config.get('pipe')) > 0:
            p = subprocess.Popen(self.config.get('pipe'),
                                 shell=True,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
            p.stdin.write(msg.as_string())
            p.stdin.close()
            if p.wait() != 0:
                self.logger.error('Unable to deliver mail: %s' % p.stdout.read().strip())
                return False
        else:
            # Send the message via SMTP to localhost:25
            try:
                smtp = SMTP(self.config.get('smtp'))
                smtp.sendmail(sender, recipient, msg.as_string())
            except Exception, e:
                self.logger.error('Unable to deliver mail: %s' % e)
                return False
            else:
                smtp.quit()

        return True
