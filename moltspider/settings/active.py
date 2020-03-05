from .base import *
import logging

# DB_CONNECTION_STRING = 'postgresql://article:123456@localhost/article'
DB_CONNECTION_STRING = 'sqlite:///' + os.path.join(BASE_DIR, 'ynovel.sqlite3')

LIMIT_INDEX_PAGES = 1
LIMIT_ARTICLES = 0
LIMIT_CHAPTERS = 0

LOG_ENABLED = True
LOG_LEVEL = logging.INFO

SUPPORTED_SITES_SEARCH_PATH.extend([
    os.path.join(BASE_DIR, 'supported_sites'),
])

PROCESS_PLUGINS_SEARCH_PATH.extend([
    os.path.join(BASE_DIR, 'process_plugins'),
])

MEDIA_ALLOW_REDIRECTS = True
# REDIRECT_ENABLED = False

