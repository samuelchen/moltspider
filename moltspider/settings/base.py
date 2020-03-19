# -*- coding: utf-8 -*-

# Scrapy settings for moltspider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html


##########################################
#
#  copy to setting.py for local use.
#
##########################################

import os
import socket
from ..consts import SchemaOtherKey as SOK

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# BOT_NAME = 'moltspider'

SPIDER_MODULES = ['moltspider.spiders']
# NEWSPIDER_MODULE = 'moltspider.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'moltspider (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 1
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    # "User-Agent": random.choice(USER_AGENTS),
    "Accept-Encoding": "gzip,deflate,sdch",
    "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2",
    }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
#    'moltspider.middlewares.MoltSpiderMiddleware': 543,

    # ----- defaults -----
    # 'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': 50,
    # 'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': 500,
    # 'scrapy.spidermiddlewares.referer.RefererMiddleware': 700,
    # 'scrapy.spidermiddlewares.urllength.UrlLengthMiddleware': 800,
    # 'scrapy.spidermiddlewares.depth.DepthMiddleware': 900,
}

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'moltspider.middlewares.RotateUserAgentDownloadMiddleware': 500,
    # 'moltspider.middlewares.EncodingDownloaderMiddleware': 589

    # ----- defaults -----
    # 'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': 100,
    # 'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware': 300,
    # 'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
    # 'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': 400,
    # 'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 500,
    # 'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    # 'scrapy.downloadermiddlewares.ajaxcrawl.AjaxCrawlMiddleware': 560,
    # 'scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware': 580,
    # 'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 590,
    # 'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 600,
    # 'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700,
    # 'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
    # 'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
    # 'scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware': 900,
}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'moltspider.pipelines.AlbumPipeline': 100,
    'moltspider.pipelines.FilePipeline': 200,
    'moltspider.pipelines.TagsPipeline': 300,
    'moltspider.pipelines.ExtraMetaPipeline': 400,
    'moltspider.pipelines.DatabasePipeline': 500,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
HTTPCACHE_GZIP = True


# --------- customized settings ----------

# DB connection string
# http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls
# format: driver://user:pass@host:port/database
# e.g.
# SQLITE3: sqlite:///path/to/database.db
# SQLITE3 in memory: sqlite://  (with nothing) or sqlite:///memory:
# MYSQL: mysql://scott:tiger@localhost/test
# MYSQL with driver and charset: mysql+pymysql://scott:tiger@localhost/test?charset=utf8mb4
# MYSQL with driver and charset: mysql+mysqldb://scott:tiger@localhost/test?charset=utf8&use_unicode=0
# POSTGRESQL: postgresql://scott:tiger@localhost/test
# POSTGRESQL with driver and domain: postgresql+psycopg2://user:password@/dbname
# POSTGRESQL with driver and domain: postgresql+psycopg2://user:password@/dbname?host=/var/lib/postgresql
# DB_CONNECTION_STRING='postgresql://scott:tiger@localhost/test'
DB_CONNECTION_STRING = 'sqlite:///' + os.path.join(BASE_DIR, 'article.sqlite3')
# DB_CONNECTION_STRING='postgresql://localhost/'

# host name & IP. for distributed spiders
HOSTNAME = socket.gethostname()
SPIDER_ID = HOSTNAME

# how many chapters will be crawled (article chapters). 0 = no limitation
LIMIT_CHAPTERS = 2

# paths to search customized supported sites schema definitions
# built-in schemas in BASE_PATH/moltspider/sites
SUPPORTED_SITES_SEARCH_PATH = [
    # os.path.join(BASE_DIR, 'supported_sites'),
]

# paths to search customized plugins used in PROCESS field of site schema
# built-in plugins are placed in BASE_PATH/moltspider/plugins
PROCESS_PLUGINS_SEARCH_PATH = [
    # os.path.join(BASE_DIR, 'process_plugins'),
]

STATIC_BASE = os.path.join(BASE_DIR, 'static')      # added.

# scrapy origin settings
IMAGES_STORE = os.path.join(STATIC_BASE, 'album')
IMAGES_URLS_FIELD = SOK.ALBUM_DL.code
IMAGES_RESULT_FIELD = SOK.ALBUM_DL_PATH.code
IMAGES_EXPIRES = 365 * 10

FILES_STORE = os.path.join(STATIC_BASE, 'media')
FILES_URLS_FIELD = SOK.FILE_DL.code
FILES_RESULT_FIELD = SOK.FILE_DL_PATH.code
FILES_EXPIRES = 365 * 10

# allow file downloads redirect (HTTP 302)
MEDIA_ALLOW_REDIRECTS = False

# keep conflict/duplicate chapters
CHAPTER_KEEP_CONFLICT = False
