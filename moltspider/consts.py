from optenum import Options, OptionGroup as G
from gettext import gettext as _
from datetime import timezone, timedelta, datetime

DB_T_DOT_ESCAPE = ('.', '!')    # escape '.'(dot) for creating table name in DB
DB_T_NAME_SEP = '#'             # separator for creating table name in DB

UTC = timezone.utc
CST = timezone(timedelta(hours=8))
MIN_DATE = datetime.min.replace(tzinfo=CST)


# TODO: change all options texts and i18n


class Args(Options):
    SEP = ','
    SITES = 's', '"%s" separated list or site domains (site ids). from `supported_sites` folder.' % SEP
    ARTICLES = 'a', '"%s" separated list of articles id(s). from DB article table' % SEP
    ARTICLE_COUNT = 'ac', 'how many articles will be crawled'
    INDEXES = 'i', '"%s" separated list of index id(s). from DB index table' % SEP
    CHAPTER_FROM_ID = 'cf', 'chapter id which will be crawled start from. from DB article table'
    CHAPTER_TO_ID = 'ct', 'chapter id which will be crawled end to. from DB article table'
    CHAPTER_COUNT = 'cc', 'how many chapters will be crawled'
    PAGES = 'p', 'how many pages will be crawled if there is next link'

    NOCACHE = 'nocache', 'do not use cache in this crawling'


class Spiders(Options):
    INDEX = 'index', 'index spider to get url of article list index from home page'
    LIST = 'list', 'list spider to get urls of article list from index page'
    META = 'meta', 'meta spider to get article meta from article meta page'
    TOC = 'toc', 'toc spider to get article TOC (chapter list) from toc page'
    CHAPTER = 'chapter', 'chapter spider to get chapter content from chapter page'


class Schemas(Options):
    HOME_PAGE = 'home', 'home page schema, where to grab index'
    INDEX_PAGE = 'index', 'index list page schema, where to list articles'
    META_PAGE = 'meta', 'meta page schema, where to get meta'
    TOC_PAGE = 'toc', 'toc page schema, sometimes it is the same page as meta page'
    CHAPTER_PAGE = 'chapter', 'chapter page schema, where to get chapter content'


class SiteSchemaKey(Options):

    # whether create standalone DB table to store chapters. default False.
    # only available in META_PAGE schema
    TABLE_ALONE = 'table_alone'

    NAME = 'name'           # site name
    URL = 'url'             # site url
    ENCODING = 'encoding'   # site encoding
    ITEMS = 'items'         # item schema list
    FIELDS = 'fields'       # field schema list (of an item)
    XPATH = 'xpath'         # xpath selector expression
    CSS = 'css'             # css selector expression
    ACTION = 'action'       # the item triggers an action
    PROCESS = 'process'     # regular expression to process captured data
    VALUE = 'value'         # directly set this value, ignore CSS/XPATH selector
    COMMENT = '//'          # comments. e.g. {..., "//": "this field used to capture description", ...}

    TAG_PREFIX = '#'        # prefix to identify this field to capture tags. e.g. '#', or '#1'
    META_PREFIX = '@'       # prefix to identify extra meta field name. e.g. { '@org': {...} }. captured field name is 'org'.


class SchemaOtherKey(Options):
    SITE = 'site'                   # site id (added)

    ALBUM_DL = 'album'                 # album link to be downloaded
    ALBUM_DL_PATH = 'album_path'    # album downloaded path
    FILE_DL = 'file'                # file link to be downloaded
    FILE_DL_PATH = 'file_path'      # file downloaded path

    ACTION_NEXT = 'next'            # action: next page


# how many chapters will be downloaded if weight is PREVIEW
ARTICLE_PREVIEW_CHAPTER_COUNT = 30


class ArticleWeight(Options):
    PREMIUM = 140, _('Premium article, VIP access')
    CLASSIC = 120, _('Classic article')
    CHOICE = 100, _('Editor choice, promoted')
    NORMAL = 80, _('Normal article, download all chapters')
    PREVIEW = 60, _('Preview article, download first %d chapters') % ARTICLE_PREVIEW_CHAPTER_COUNT
    TOC = 40, _('Listed article with TOC captured')
    TOC_PREVIEW = 35, _('Preview TOC, download first %d entries of TOC' % ARTICLE_PREVIEW_CHAPTER_COUNT)
    META = 20, _('Listed article with meta captured')
    LISTED = 0, _('Added to db with url and name')
    ACHIEVED = -20, _('Achieved article. Hidden.')


class ArticleStatus(Options):
    DELETED = 200, _('Deleted.')
    COMPLETE = 100, _('Completed article.')
    TERMINATED = 80, _('Mark done by editor')
    ABANDON = 60, _('Abandoned by author (no updates for 180 days)')
    PENDING = 40, _('Pending to be finished/abandoned (no updates for 30 days)')
    SLOW = 30, _('Slow updating (no updates for 7 days)')
    PROGRESS = 20, _('Keep updating in progress')
    INCLUDED = 0, _('Added to database')

