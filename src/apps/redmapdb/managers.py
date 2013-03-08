'''
Created on 10/09/2012

@author: thomas
'''
'''
Created on 21/08/2012

@author: thomas
'''

from django.db import models, connection, connections
from django.db.models.query import QuerySet
from django.db.models import Min
from django.conf import settings

from pyodbc import ProgrammingError

import logging
logger = logging.getLogger()
logger = logging.getLogger("django.request")


class RedmapManager(models.Manager):

    def __init__(self, *args, **kwargs):
        self.connection_name = kwargs.pop('connection_name', None)
        super(RedmapManager, self).__init__(*args, **kwargs)

    def _get_cursor(self):
        if self.connection_name:
            return connections[self.connection_name].cursor()
        return connection.cursor()

    def execute_call(self, call, params=None):
        try:
            cursor = self._get_cursor()
            if params:
                cursor_result = cursor.execute(call, params)
            else:
                cursor_result = cursor.execute(call)

            return cursor_result, cursor
        except Exception as ex:
            logger.exception(
                'Exception thrown while running execute_call {0} with {1})'
                .format(call, params))
            raise ex

    def function_species_in_range(self, species_id, latitude, longitude):
        call = """
SELECT [dbo].[RM_SPECIES_IN_RANGE] (
 {species_id}
,CAST({latitude} as numeric(18,9))
,CAST({longitude} as numeric(18,9)))""".format(species_id=species_id, latitude=latitude, longitude=longitude)

        try:
            result, cursor = self.execute_call(call)
            return bool(result.fetchone()[0])
        except ProgrammingError:
            return False

    def function_get_sighting_region(self, latitude, longitude):
        call = """SELECT [dbo].[RM_GET_SIGHTING_REGION] (
CAST({latitude} as numeric(18,9))
,CAST({longitude} as numeric(18,9)))""".format(latitude=latitude, longitude=longitude)

        result, cursor = self.execute_call(call)
        region_id = result.fetchone()[0]
        return region_id


class StoredProcedureMetaOptions(object):
    """
    This class' purpose is to provide a configuration container for models
    in the application which interact with the MSSQL database through stored 
    procedures and table views
    """

    name = NotImplementedError("A stored procedure name has not been set on your model.")
    overridden_field_names = dict()
    excluded_fields = list()
    param_prefix = 'p'

    def __init__(self, opts):
        if opts:
            for key, value in opts.__dict__.iteritems():
                setattr(self, key, value)


class RedmapModelbase(models.base.ModelBase):
    def __new__(self, name, bases, attrs):
        new = super(RedmapModelbase, self).__new__(self, name, bases, attrs)
        sp_meta_options = attrs.pop('StoredProcedureMeta', None)
        setattr(new, '_stored_procedure_meta', StoredProcedureMetaOptions(sp_meta_options))
        return new


class RedmapModel(models.Model):

    """
    Abstract meta base class for store proc classes
    """
    __metaclass__ = RedmapModelbase

    objects = RedmapManager()

    def __init__(self, *args, **kwargs):
        self.modify_sp = '{0}_MAINT'.format(self._meta.db_table)
        self.select_sp = '{0}_SEL'.format(self._meta.db_table)
        super(RedmapModel, self).__init__(*args, **kwargs)

    def _dictfetchall(self, cursor):
        "Returns all rows from a cursor as a dict"
        desc = cursor.description
        return [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
        ]

    def save(self, *args, **kwargs):
        if not settings.REDMAP_MODELS_USE_MSSQL:
            super(RedmapModel, self).save(*args, **kwargs)

        if hasattr(self, self._meta.pk.attname) and getattr(self, self._meta.pk.attname) is not None:
            self.save_by_update_stored_procedure()
        else:
            _results, model_id = self.save_by_insert_stored_procedure()
            setattr(self, self._meta.pk.attname, model_id)

    def delete(self):
        self.delete_by_stored_procedure()

    def save_by_insert_stored_procedure(self):
        return self.modify_stored_procedure(1)

    def save_by_update_stored_procedure(self):
        return self.modify_stored_procedure(2)

    def delete_by_stored_procedure(self):
        self.modify_stored_procedure(3)

    def modify_stored_procedure(self, mode):
        return_code = None
        error = None
        scope_identity = None

        try:
            cursor = connection.cursor()
            call, vals = self._get_sp_call(self.modify_sp, mode)
            cursor_result = cursor.execute(call, vals)

            row = cursor_result.fetchone()
            return_code = row[0]
            error = row[1]
            scope_identity = row[2]

            cursor.close()
            return return_code, error, scope_identity

        except:
            raise

        return return_code, error, scope_identity

    def _get_sp_parameters(self):
        from django.db.models.fields.related import ForeignKey
        d = {}
        for field in self._meta.fields:
            attr = field.name

            if attr in self._stored_procedure_meta.excluded_fields:
                continue

            if attr in self._stored_procedure_meta.overridden_field_names:
                param_name = self._stored_procedure_meta.overridden_field_names.get(attr)
            else:
                param_name = "{0}{1}".format(self._stored_procedure_meta.param_prefix, field.column)

            value = getattr(self, attr)

            if value is not None and isinstance(field, ForeignKey):
                value = value._get_pk_val()

            d[param_name] = value
        for field in self._meta.many_to_many:
            d[param_name] = [obj._get_pk_val() for obj in getattr(self, field.attname).all()]
        return d

    def _get_sp_call(self, sp_name, mode, params=None):
        params = params or self._get_sp_parameters()

        odbc_names = []
        odbc_vals = []

        for key, val in params.items():
            odbc_names.append("@{0} = %s".format(key))
            odbc_vals.append(val)

        odbc_names.append("@pMODE = %s".format(key))
        odbc_vals.append(mode)

        final_odbc_names = ', '.join(odbc_names)

        return "exec {0} {1};".format(sp_name, final_odbc_names), odbc_vals

    class Meta:
        abstract = True
