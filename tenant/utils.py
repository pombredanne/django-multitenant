from django.utils.functional import curry

from tenant.signals import tenant_provider

import threading
import os
import sys
import urlparse


def get_current_tenant(sender=None, **hints):
    if sender is None:
        sender = threading.current_thread()

    tenant = None
    responses = tenant_provider.send(sender=sender, **hints)
#    print tenant_provider.receivers, responses
    
    for resp in responses:
        if resp[1]:
            tenant = str(resp[1])
            break
    return tenant

def connect_tenant_provider(dispatch_uid, tenant):
    signal_function = curry(lambda sender, tenant=None, **kwargs: tenant, tenant=tenant)
    tenant_provider.connect(signal_function, weak=False, dispatch_uid=dispatch_uid, sender=threading.current_thread())

def disconnect_tenant_provider(dispatch_uid, sender=None):
    if sender is None:
        sender = threading.current_thread()
    tenant_provider.disconnect(weak=False, dispatch_uid=dispatch_uid, sender=sender)

def parse_connection_string(string):
    urlparse.uses_netloc.append('postgres')
    urlparse.uses_netloc.append('mysql')
    urlparse.uses_netloc.append('postgresql_psycopg2')

    url = urlparse.urlparse(string)
    settings = {
        'NAME':     url.path[1:],
        'USER':     url.username,
        'PASSWORD': url.password,
        'HOST':     url.hostname,
        'PORT':     url.port,
    }
    if url.scheme == 'postgres' or url.scheme == 'postgresql_psycopg2':
        settings['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
    if url.scheme == 'mysql':
        settings['ENGINE'] = 'django.db.backends.mysql'
    if not getattr(settings, 'ENGINE', None):
        raise Exception('DATABASE.ENGINE missing')
    return settings

def get_public_models():
    from django.db.models import get_models, get_app
    from tenant import settings
    
    models = []
    for app in settings.MULTITENANT_PUBLIC_APPS:
        app = app.split('.')[-1]
        models.extend(get_models(get_app(app)))
    return models

def get_private_models():
    from django.db.models import get_models, get_app
    from tenant import settings
    
    models = []
    for app in settings.MULTITENANT_PRIVATE_APPS:
        app = app.split('.')[-1]
        models.extend(get_models(get_app(app)))
    return models
