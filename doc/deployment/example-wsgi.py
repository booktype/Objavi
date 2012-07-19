# Example WSGI script for Objavi.
#
# This file is referenced from the Apache site configuration file by the
# WSGIScriptAlias directive (from the mod_wsgi module).
#

import os, sys
import django.core.handlers.wsgi

# Name of the Django settings module (in Python syntax).
os.environ['DJANGO_SETTINGS_MODULE'] = 'objavi.settings'

# Add Objavi libraries to PYTHONPATH.
#
sys.path.insert(0, '/var/www/')
sys.path.insert(1, '/var/www/objavi/')

# If you are using some Python libraries which are not installed to a standard
# location, add path to them here, e.g.
#sys.path.append("/usr/local/share/somelib")

# The application object.
#
def application(environ, start_response):
    # transfer SERVER_NAME and SERVER_PORT to process environment
    os.environ["SERVER_NAME"] = environ["SERVER_NAME"]
    os.environ["SERVER_PORT"] = environ["SERVER_PORT"]
    # run the WSGI handler
    app = django.core.handlers.wsgi.WSGIHandler()
    return app(environ, start_response)
