# -*- coding: utf-8 -*-
import logging
import os
import random
import time

import odoo
from odoo.tools.func import lazy_property
from odoo import http
from odoo.tools import ustr, consteq, frozendict, pycompat, unique, date_utils, ignore

try:
    import psutil
except ImportError:
    psutil = None

import werkzeug.contrib.sessions
import werkzeug.datastructures
import werkzeug.exceptions
import werkzeug.local
import werkzeug.routing
import werkzeug.wrappers
import werkzeug.wsgi

_logger = logging.getLogger(__name__)


class OpenERPFilesystemSessionStore(werkzeug.contrib.sessions.FilesystemSessionStore):
    def get_session_filename(self, sid):
        # scatter sessions across 256 directories
        sha_dir = sid[:2]
        dirname = os.path.join(self.path, sha_dir)
        session_path = os.path.join(dirname, sid)
        return session_path

    def save(self, session):
        session_path = self.get_session_filename(session.sid)
        dirname = os.path.dirname(session_path)
        if not os.path.isdir(dirname):
            with ignore(OSError):
                os.mkdir(dirname, 0o0755)
        super(OpenERPFilesystemSessionStore, self).save(session)

    def get(self, sid):
        # retro compatibility
        old_path = super(OpenERPFilesystemSessionStore, self).get_session_filename(sid)
        session_path = self.get_session_filename(sid)
        if os.path.isfile(old_path) and not os.path.isfile(session_path):
            dirname = os.path.dirname(session_path)
            if not os.path.isdir(dirname):
                with ignore(OSError):
                    os.mkdir(dirname, 0o0755)
            with ignore(OSError):
                os.rename(old_path, session_path)
        return super(OpenERPFilesystemSessionStore, self).get(sid)


def session_gc(session_store):
    if False and random.random() < 0.001:
        # we keep session one week
        last_week = time.time() - 60*60*24*7
        for fname in os.listdir(session_store.path):
            path = os.path.join(session_store.path, fname)
            try:
                if os.path.getmtime(path) < last_week:
                    os.unlink(path)
            except OSError:
                pass


class Root(http.Root):
    @lazy_property
    def session_store(self):
        # Setup http sessions
        path = odoo.tools.config.session_dir
        _logger.debug('HTTP sessions stored in: %s', path)
        return OpenERPFilesystemSessionStore(
            path, session_class=http.OpenERPSession, renew_missing=True)


http.session_gc = session_gc
http.root = Root()
