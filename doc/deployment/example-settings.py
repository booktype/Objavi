
import os
import objavi
import djcelery

djcelery.setup_loader()


# Django debug
#
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Django admin
#
ADMINS = (
    #('Your Name', 'your_email@domain.com')
)

MANAGERS = ADMINS

DEFAULT_NOTIFICATION_FILTER = u"#* !* ~* \u212c*"

SERVER_NAME = os.environ.get('SERVER_NAME', 'localhost')
SERVER_PORT = os.environ.get('SERVER_PORT', '80')


##
# Directories
#

# Objavi
#
OBJAVI_URL  = "http://%s:%s" % (SERVER_NAME, SERVER_PORT)
OBJAVI_DIR  = '##DESTINATION##'
OBJAVI_SOURCE_DIR = '##SOURCE_PATH##'

# static
#
STATIC_ROOT = '%s/static' % OBJAVI_DIR
STATIC_URL  = '%s/static' % OBJAVI_URL

# data
#
DATA_ROOT = '%s/data' % OBJAVI_DIR
DATA_URL  = '%s/data' % OBJAVI_URL


##
# Database
# https://docs.djangoproject.com/en/1.3/ref/settings/#databases
#

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = '%s/objavi.db' % OBJAVI_DIR
DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = ''


##
# Celery
#

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis'


##
# Django
#

AUTH_PROFILE_MODULE = 'account.UserProfile'

TIME_ZONE     = 'Europe/Berlin'
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True
USE_L10N = True

LOCALE_PATHS = (
    '%s/locale' % OBJAVI_DIR,
    '%s/locale' % os.path.dirname(objavi.__file__),
)

STATICFILES_DIRS = (
    os.path.join(OBJAVI_SOURCE_DIR, 'static'),
)

TEMPLATE_DIRS = (
    os.path.join(OBJAVI_DIR, 'templates'),
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware'
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.staticfiles',

    'djcelery',

    'objavi',
)


ROOT_URLCONF = 'objavi.urls'


##
# Logging
#

def init_logging():
    import logging
    import logging.handlers

    logger = logging.getLogger("objavi")
    logger.setLevel(logging.DEBUG)
    ch = logging.handlers.RotatingFileHandler('%s/logs/objavi.log' % OBJAVI_DIR, maxBytes=100000, backupCount=5)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(ch)

logInitDone = False
if not logInitDone:
    logInitDone = True
    init_logging()
