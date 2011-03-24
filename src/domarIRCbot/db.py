#
#  Copyright (C) 2010 by Filip Brcic <brcha@gna.org>
#
#  Persistent object database support, based on shelve
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import shelve
import multiprocessing

import UserDict

class DB(UserDict.DictMixin):
    """ Wrapper over shelve that does auto-sync on every write
    and avoids throwing errors when keys don't exist, instead returning None.
    Made to be thread-safe.
    """
    def __init__(self, path):
        self.db = shelve.open(path)
        self.readLock  = multiprocessing.RLock()
        self.writeLock = multiprocessing.RLock()

    def keys(self):
        self.readLock.acquire()
        keys = self.db.keys()
        self.readLock.release()
        return keys

    def __len__(self):
        self.readLock.acquire()
        dblen = len(self.db)
        self.readLock.release()
        return dblen

    def has_key(self, key):
        self.readLock.acquire()
        result = key in self.db
        self.readLock.release()
        return result

    def __contains__(self, key):
        return self.has_key(key)

    def get(self, key, default=None):
        self.readLock.acquire()
        value = self.db.get(key, default)
        self.readLock.release()
        return value

    def __getitem__(self, key):
        return self.db.get(key)

    def __setitem__(self, key, value):
        self.readLock.acquire()
        self.writeLock.acquire()
        self.db[key] = value
        self.writeLock.release()
        self.readLock.release()
        self.db.sync()

    def __delitem__(self, key):
        self.readLock.acquire()
        if key in self.db:
            self.writeLock.acquire()
            del self.db[key]
            self.writeLock.release()
        self.readLock.release()

    def close(self):
        self.readLock.acquire()
        self.writeLock.acquire()
        self.db.close()
        self.writeLock.release()
        self.readLock.release()

    def __del__(self):
        self.readLock.acquire()
        self.writeLock.acquire()
        del self.db
        self.writeLock.release()
        self.readLock.release()

    def sync(self):
        self.readLock.acquire()
        self.writeLock.acquire()
        self.db.sync()
        self.writeLock.release()
        self.readLock.release()

class _PutData(object):
    def __init__(self, key, value):
        super(_PutData, self).__init__()
        self.key = key
        self.value = value

class _GetData(object):
    def __init__(self, key):
        super(_GetData, self).__init__()
        self.key = key

class _ReturnData(object):
    def __init__(self, value):
        super(_ReturnData, self).__init__()
        self.value = value

class _Keys(object):
    def __init__(self):
        super(_Keys, self).__init__()

class _Len(object):
    def __init__(self):
        super(_Len, self).__init__()

class _DelData(object):
    def __init__(self, key):
        super(_DelData, self).__init__()
        self.key = key

class _Die(object):
    def __init__(self):
        super(_Die, self).__init__()

class DBManagerProcess(multiprocessing.Process, UserDict.DictMixin):
    def __init__(self, db):
        super(DBManagerProcess, self).__init__()

        self._messages = multiprocessing.Queue()
        self._db = db

        self._retKey = multiprocessing.Queue()
        self._retLen = multiprocessing.Queue()
        self._retGet = multiprocessing.Queue()

        self._lckKey = multiprocessing.RLock()
        self._lckLen = multiprocessing.RLock()
        self._lckGet = multiprocessing.RLock()

    def keys(self):
        self._lckKey.acquire()
        self._messages.put(_Keys())
        val = self._retKey.get()
        self._lckKey.release()
        return val.value

    def __len__(self):
        self._lckLen.acquire()
        self._messages.put(_Len())
        val = self._retLen.get()
        self._lckLen.release()
        return val.value

    def has_key(self, key):
        return key in self.keys()

    def __contains__(self, key):
        return self.has_key(key)

    def get(self, key, default=None):
        self._lckGet.acquire()
        self._messages.put(_GetData(key))
        val = self._retGet.get()
        self._lckGet.release()
        return val.value or default

    def __getitem__(self, key):
        return self.get(key)

    def put(self, key, value):
        self._messages.put(_PutData(key, value))

    def __setitem__(self, key, value):
        self.put(key, value)

    def __delitem__(self, key):
        self._messages.put(_DelData(key))

    def __del__(self):
        if self.is_alive():
            self.terminate()

    def die(self):
        self._messages.put(_Die())

    def run(self):
        while True:
            job = self._messages.get()

            if type(job) is _PutData:
                self._db[job.key] = job.value
            elif type(job) is _GetData:
                self._retGet.put(
                    _ReturnData(self._db[job.key])
                    )
            elif type(job) is _Keys:
                self._retKey.put(
                    _ReturnData(self._db.keys())
                    )
            elif type(job) is _Len:
                self._retLen.put(
                    _ReturnData(len(self._db))
                    )
            elif type(job) is _DelData:
                key = job.key
                if key in self._db:
                    del self._db[key]
            elif type(job) is _Die:
                return
