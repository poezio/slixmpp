# -*- coding: utf-8 -*-
#
# Copyright 2018 Philipp Hörist <philipp@hoerist.com>
#
# This file is part of Gajim-OMEMO plugin.
#
# The Gajim-OMEMO plugin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Gajim-OMEMO is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# the Gajim-OMEMO plugin.  If not, see <http://www.gnu.org/licenses/>.
#

import sqlite3
import pickle
import logging
from collections import namedtuple

from omemo import Storage
from omemo.x3dhdoubleratchet import X3DHDoubleRatchet
from omemo.signal.doubleratchet.doubleratchet import DoubleRatchet

from .db_helpers import user_version

log = logging.getLogger(__name__)


class SQLiteDatabase(Storage):
    """ SQLite Database """

    def __init__(self, db_path):
        sqlite3.register_adapter(X3DHDoubleRatchet, self._pickle_object)
        sqlite3.register_adapter(DoubleRatchet, self._pickle_object)

        sqlite3.register_converter("omemo_state", self._unpickle_object)
        sqlite3.register_converter("omemo_session", self._unpickle_object)
        self._con = sqlite3.connect(db_path,
                                    detect_types=sqlite3.PARSE_DECLTYPES)
        self._con.text_factory = bytes
        self._con.row_factory = self.namedtuple_factory
        self._create_database()
        self._migrate_database()
        self._con.execute("PRAGMA synchronous=FULL;")
        self._con.commit()
        self._own_device_id = None

    def _create_database(self):
        if user_version(self._con) == 0:
            create_tables = '''
                CREATE TABLE IF NOT EXISTS sessions (
                    _id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jid TEXT,
                    device_id INTEGER,
                    session omemo_session BLOB,
                    state omemo_state BLOB,
                    fingerprint TEXT,
                    active INTEGER DEFAULT 1,
                    trust INTEGER DEFAULT 1,
                    UNIQUE(jid, device_id));

                CREATE TABLE IF NOT EXISTS state (
                    _id INTEGER PRIMARY KEY,
                    device_id INTEGER,
                    state omemo_state BLOB
                    );
                '''

            create_db_sql = """
                BEGIN TRANSACTION;
                %s
                PRAGMA user_version=1;
                END TRANSACTION;
                """ % (create_tables)
            self._con.executescript(create_db_sql)

    def _migrate_database(self):
        """ Migrates the DB
        """
        pass

    @staticmethod
    def _pickle_object(session):
        return pickle.dumps(session, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def _unpickle_object(session):
        return pickle.loads(session)

    @staticmethod
    def namedtuple_factory(cursor, row):
        fields = [col[0] for col in cursor.description]
        Row = namedtuple("Row", fields)
        named_row = Row(*row)
        return named_row

    def loadState(self):
        log.info('Load State')
        q = 'SELECT device_id, state FROM state'
        result = self._con.execute(q).fetchone()
        if result is not None:
            self._own_device_id = result.device_id
            return {'state': result.state, 'device_id': result.device_id}

    def storeState(self, state, device_id):
        log.info('Store State')
        self._own_device_id = device_id
        q = 'INSERT OR REPLACE INTO state(device_id, state) VALUES(?, ?)'
        self._con.execute(q, (device_id, state))
        self._con.commit()

    def loadSession(self, jid, device_id):
        log.info('Load Session')
        q = 'SELECT session FROM sessions WHERE jid = ? AND device_id = ?'
        result = self._con.execute(q, (jid, device_id)).fetchone()
        if result is not None:
            return result.session

    def storeSession(self, jid, device_id, session):
        log.info('Store Session: %s, %s', jid, device_id)
        q = 'UPDATE sessions SET session = ? WHERE jid= ? AND device_id = ?'
        self._con.execute(q, (session, jid, device_id))
        self._con.commit()

    def createSession(self, jid, device_id, session):
        log.info('Create Session')
        q = '''INSERT INTO sessions(jid, device_id, session, trust, active)
               VALUES (?, ?, ?, 1, 1)'''
        self._con.execute(q, (jid, device_id, session))
        self._con.commit()

    def loadActiveDevices(self, jid):
        return self.loadDevices(jid, 1)

    def loadInactiveDevices(self, jid):
        return self.loadDevices(jid, 0)

    def loadDevices(self, jid, active):
        q = 'SELECT device_id FROM sessions WHERE jid = ? AND active = ?'
        result = self._con.execute(q, (jid, active)).fetchall()
        if result:
            devices = [row.device_id for row in result]
            state = 'Active' if active else 'Inactive'
            log.info('Load %s Devices: %s, %s', state, jid, devices)
            return devices
        return []

    def storeActiveDevices(self, jid, devices):
        if not devices:
            return
        # python-omemo returns own device as active,
        # dont store it in this table
        if self._own_device_id in devices:
            devices.remove(self._own_device_id)
        log.info('Store Active Devices: %s, %s', jid, devices)
        self.storeDevices(jid, devices, 1)

    def storeInactiveDevices(self, jid, devices):
        if not devices:
            return
        log.info('Store Inactive Devices: %s, %s', jid, devices)
        self.storeDevices(jid, devices, 0)

    def storeDevices(self, jid, devices, active):
        for device_id in devices:
            try:
                insert = '''INSERT INTO sessions(jid, device_id, active)
                            VALUES(?, ?, ?)'''
                self._con.execute(insert, (jid, device_id, active))
                self._con.commit()
            except sqlite3.IntegrityError:
                update = '''UPDATE sessions SET active = ?
                            WHERE jid = ? AND device_id = ?'''
                self._con.execute(update, (active, jid, device_id))
                self._con.commit()

    def getDevicesWithoutSession(self, jid):
        log.info('Get Devices without Session')
        q = '''SELECT device_id FROM sessions
               WHERE jid = ? AND (session IS NULL OR session = "")'''
        result = self._con.execute(q, (jid,)).fetchall()
        if result:
            devices = [row.device_id for row in result]
            log.info('Get Devices without Session: %s', devices)
            return devices
        log.info('Get Devices without Session: []')
        return []

    def getTrustedFingerprints(self, jid):
        return True

    def storeBundle(self, jid, device_id, fingerprint):
        log.info('Store Bundle')
        q = '''UPDATE sessions SET fingerprint = ?
                    WHERE jid = ? and device_id = ?'''
        self._con.execute(q, (fingerprint, jid, device_id))
        self._con.commit()

    def isTrusted(self, *args):
        return True
