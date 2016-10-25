# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from django.conf import settings

from . import generate_request_id, local, release_local
from .conf import REQUEST_ID_HEADER


def get_request_id(request):
    if hasattr(request, 'request_id'):
        return request.request_id
    elif REQUEST_ID_HEADER:
        return request.META.get(REQUEST_ID_HEADER, '')
    else:
        return generate_request_id()


class RequestIdMiddleware(object):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        request_id = get_request_id(request)
        request.request_id = request_id
        self.set_application_name(request_id)
        local.request_id = request_id

        response = self.get_response(request)

        release_local(local)

        return response

    # Compatibility methods for Django <1.10
    def process_request(self, request):
        request_id = get_request_id(request)
        request.request_id = request_id
        self.set_application_name(request_id)
        local.request_id = request_id

    def process_response(self, request, response):
        release_local(local)
        return response

    def set_application_name(self, request_id):
        """Set the application_name on PostgreSQL connection to propagate request_id to postgresql

        http://www.postgresql.org/docs/9.4/static/libpq-connect.html#LIBPQ-PARAMKEYWORDS
        """
        supported_backends = ['django.db.backends.postgresql_psycopg2']

        dbs = getattr(settings, 'DATABASES', [])

        # lookup over all the databases entry
        for db in dbs.keys():
            if dbs[db]['ENGINE'] in supported_backends:
                try:
                    options = dbs[db]['OPTIONS']
                except KeyError:
                    options = {}

                dbs[db]['OPTIONS'].update({'application_name': request_id})
