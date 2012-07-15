# Example configuration for Objavi's WSGI interface.

import os, sys

sys.path.insert(0, '/var/www/')
sys.path.insert(1, '/var/www/objavi/')
sys.path.insert(1, '/var/www/objavi/lib/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'objavi.settings'

def application(environ, start_response):
	os.environ["SERVER_NAME"] = environ["SERVER_NAME"]
	os.environ["SERVER_PORT"] = environ["SERVER_PORT"]
	import django.core.handlers.wsgi
	app = django.core.handlers.wsgi.WSGIHandler()
	return app(environ, start_response)
