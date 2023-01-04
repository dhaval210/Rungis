import os
import sys
import ibm_db
import ibm_db_dbi

from decimal import *
from odoo.addons.component.core import AbstractComponent
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.connector.exception import NetworkRetryableError

import logging

_logger = logging.getLogger(__name__)

class DB2Connect(object):
    
    def __init__(self, database, hostname, port, uid, pwd):
        self.database = database
        self.hostname = hostname
        self.port = port
        self.uid = uid
        self.pwd = pwd
        self._api = None
        self.ibm_db_conn = None

    @property
    def api(self):
        if self._api is None:
            try:
                conn_str = "DATABASE=%(database)s;HOSTNAME=%(hostname)s;PORT=%(port)s;UID=%(uid)s;PWD=%(pwd)s;" % {
                    'database': self.database,
                    'hostname': self.hostname,
                    'port': self.port,
                    'uid': self.uid,
                    'pwd': self.pwd,
                }
                self.ibm_db_conn = ibm_db.connect(conn_str, '', '')
                self._api = ibm_db_dbi.Connection(self.ibm_db_conn)
            except Exception as e:
                _logger.info('failed to connect to db2')
                _logger.info(e)
                version = sys.version_info
                msg = str(e)
                if version is not None and version is not False:
                    msg = msg + "\n" + str(version) + "\n"
                msg = msg + os.getenv('DB2_CLI_DRIVER_INSTALL_PATH', 'DB2_CLI_DRIVER_INSTALL_PATH is not set') + "\n"
                msg = msg + os.getenv('LD_LIBRARY_PATH', 'LD_LIBRARY_PATH is not set') + "\n"
                msg = msg + os.getenv('DYLD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH is not set') + "\n"
                msg = msg + os.getenv('LIBPATH', 'LIBPATH is not set') + "\n"
                msg = msg + os.getenv('PATH', 'PATH is not set') + "\n"
                raise AttributeError(msg)                
        return self.ibm_db_conn

    def __enter__(self):
        # we do nothing, api is lazy
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._api is not None and hasattr(self._api, '__exit__'):
            self._api.__exit__(exc_type, exc_value, traceback)

    def api_call(self, method, arguments):
        """ Adjust available arguments per API """
        stmt_select = ibm_db.exec_immediate(self.api, method)
        results = []
        if arguments == 'read' or arguments == 'search':
            no_data = False
            while no_data is False:
                # Retrieve A Record And Store It In A Python Dictionary
                try:
                    data = ibm_db.fetch_assoc(stmt_select)
                    if data is not False:
                        results += [data]
                    else:
                        no_data = True
                except:
                    pass
        if arguments == 'write' or isinstance(arguments, list):
            return []

        # cols = ibm_db.fetch_both(stmt_select) 
        # cur = self.api.cursor()
        # cur.execute(method)
        # results = cur.fetchall()
        # clean_result = []
        # for res in results:
        #     clean_result += [list(res)]        
        return results

    def call(self, method, arguments):
        try:
            try:
                result = self.api_call(
                    method, arguments
                )
            except Exception:
                _logger.error("api.call('%s', %s) failed", method, arguments)
                raise
            else:
                _logger.debug("api.call('%s', %s) returned %s in %s seconds",
                              method, arguments, result,
                              1)
            # Uncomment to record requests/responses in ``recorder``
            # record(method, arguments, result)
            return result
        except Exception:
            pass


class DB2CRUDAdapter(AbstractComponent):
    """ External Records Adapter for DB2 """
    # pylint: disable=method-required-super

    _name = 'db2.crud.adapter'
    _inherit = ['base.backend.adapter', 'base.db2.connector']
    _usage = 'backend.adapter'

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def read(self, external_id, filters={}):
        """ Returns the information of a record """
        raise NotImplementedError

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, external_id, data, table):
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, external_id):
        """ Delete a record on the external system """
        raise NotImplementedError

    def _call(self, method, arguments=None):
        try:
            db2_api = getattr(self.work, 'db2_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a db2_api attribute with a '
                'DB2Connect instance to be able to use the '
                'Backend Adapter.'
            )
        return db2_api.call(method, arguments)


class GenericAdapter(AbstractComponent):
    _name = 'db2.adapter'
    _inherit = 'db2.crud.adapter'


    @staticmethod
    def get_searchCriteria(filters):
        return []

    @staticmethod
    def escape(term):
        return True

    def search(self, filters=None):
        if isinstance(filters, dict):
            if 'attributes' in filters:
                select_attributes = filters['attributes']
            else:
                select_attributes = self._db2_id
            if 'table' in filters:
                select_table = filters['table']
            else:
                raise Exception('No Table defined in Filter')
            if 'groupby' in filters:
                groupby = filters['groupby']
            else:
                groupby = False
            if 'where' in filters and len(filters['where']) > 0:
                where = ''
                first = True
                for w in filters['where']:
                    if first is True:
                        where += w[0] + ' ' + w[1] + " '" + w[2] + "'"
                        first = False
                    else:
                        where += 'AND ' +  w[0] + ' ' + w[1] + " '" + w[2] + "'"
            else:
                where = False
        else:
            select_attributes = '*'
        select_string = "SELECT %(attributes)s FROM %(table)s WHERE %(status)s != '1' AND %(status)s != '9'" % {
            'attributes': select_attributes,
            'table': select_table,
            'status': self._db2_status,
        }
        if where is not False:
            select_string += ' AND %(where)s' % {
                'where': where
            }
        if groupby is not False:
            select_string += ' GROUP BY %(groupby)s' % {
                'groupby': groupby
            }
        return self._call(select_string, 'search')

    def read(self, external_id, filters={}):
        # res = self.search()
        if 'db_id' in filters:
            db_id = filters['db_id']
        else:
            db_id = self._db2_id
        select_string = "SELECT * FROM %(table)s WHERE %(db_id)s = %(external)s AND %(status)s != '1' AND %(status)s != '9'" % {
            # 'attributes': select_attributes,
            'table': self.get_table_name(),
            'db_id': db_id,
            'external': external_id,
            'status': self._db2_status,
        }
        res = self._call(select_string, 'read')        
        return [record for record in res if record[db_id] == external_id]

    def search_read(self, filters=None):
        return self._call('select', [])

    def create(self, data):
        """ Create a record on the external system """
        return self._call('insert into', [])

    def write(self, external_id, data):
        """ Update records on the external system """
        update_string = "update %(table)s set %(something)s where %(db_id)s = '%(external)s'" % {
            'table': self.get_table_name(),
            'something': self.dict_to_valueset(data),
            'db_id': self._db2_id,
            'external': external_id,
        }
        return self._call(update_string, 'write')

    def delete(self, external_id):
        return self._call('delete from', [])
        
    def dict_to_valueset(self, data):
        set_string = ''
        first = True
        for key, value in data.items():
            if first is False:
                set_string += ', '
            first = False
            set_string += "%(k)s = '%(val)s'" % {
                'k': key,
                'val': value,
            }

        return set_string
