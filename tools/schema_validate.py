# from jsonschema import validate
import json
from moltspider.parser import SiteSchemas


"""
Variable validator. To validate variable, parameters, arguments and so by defined variable schemas.
"""
from abc import ABCMeta, abstractmethod
from jsonschema import Draft7Validator as JsonSchemaValidator, RefResolver
from jsonschema.exceptions import SchemaError, ValidationError
# import jsonref
# import os
# import re
# from .consts import SOSKeys, SchemaKeys, SchemaTypes, SchemaOverSchema
import logging

NON_FIELD_ERRORS = '__all__'
log = logging.getLogger(__name__)


class Validator(metaclass=ABCMeta):

    def __init__(self, schema, name_field='name', only_error=True):
        self._schema = schema
        self._errors = []

    @abstractmethod
    def validate(self, data):
        raise NotImplementedError

    @property
    def is_succeed(self):
        return len(self.errors) == 0

    @property
    def errors(self):
        return self._errors

    def clear(self):
        self._errors = []


class SchemaValidator(Validator):

    def __init__(self, schema, only_error=True):
        super(SchemaValidator, self).__init__(schema, only_error=only_error)

    def validate(self, schema):
        pass


class DataValidator(Validator):

    def __init__(self, schema, only_error=True):
        super(DataValidator, self).__init__(schema, name_field='name', only_error=only_error)
        self._v = JsonSchemaValidator(self._schema)

    def validate(self, data):
        try:
            errors = sorted(self._v.iter_errors(data), key=lambda e: e.path)
            print(errors)
            for error in errors:
                self.errors.append(error.message)
                # for suberror in sorted(error.context, key=lambda e: e.schema_path):
                    # print(list(suberror.schema_path), suberror.message, sep=", ")
        except SchemaError as e:
            raise


__all__ = [
    SchemaValidator.__class__.__name__,
    DataValidator.__class__.__name__,
]

if __name__ == '__main__':
    with open('../moltspider/site-schema.json') as fp:
        schema = json.load(fp)

    data_validator = DataValidator(schema)

    for site, schema_s in SiteSchemas.items():
        data_validator.validate(schema_s)
        print('-' * 30, site, '-' * 30)
        for e in data_validator.errors:
            print(e)
        break

    # schema = {
    #     "items": {
    #         "anyOf": [
    #             {"type": "string", "maxLength": 2},
    #             {"type": "integer", "minimum": 5}
    #         ]
    #     }
    # }
    # instance = [{}, 3, "foo"]
    # v = JsonSchemaValidator(schema)
    # errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
    # for e in errors:
    #     print(e)
    #     print('-'* 40)