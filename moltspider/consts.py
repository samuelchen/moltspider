from optenum import Options, OptionGroup as G

DB_T_DOT_ESCAPE = ('.', '!')    # escape '.'(dot) for creating table name in DB
DB_T_NAME_SEP = '#'             # separator for creating table name in DB


class Args(Options):
    SEP = ','
    SITES = 'sites', '$SEP (comma,) separated list or site domains (site ids). from `supported_sites` folder.'
    ARTICLES = 'articles', '$SEP (comma,) separated list of articles id(s). from DB article table'
    INDEXES = 'indexes', '$SEP (comma,) separated list of index id(s). from DB index table'
    CHAPTER_FROM_ID = 'chapter_from_id', 'chapter id which will be crawled start from. from DB article table'
    CHAPTER_TO_ID = 'chapter_to_id', 'chapter id which will be crawled end to. from DB article table'


class Spiders(Options):
    INDEX = 'index', 'index spider to get url of article list index from home page'
    LIST = 'list', 'list spider to get urls of article list from index page'
    META = 'meta', 'meta spider to get article meta from article meta page'
    TOC = 'toc', 'toc spider to get article TOC (chapter list) from toc page'
    CHAPTER = 'chapter', 'chapter spider to get chapter content from chapter page'
    FILE = '_file_', 'file spider'


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
    IS_UPDATING = 'is_updating'     # flag whether the page is updating

    ALBUM_DL = 'album'                 # album link to be downloaded
    ALBUM_DL_PATH = 'album_path'    # album downloaded path
    FILE_DL = 'file'                # file link to be downloaded
    FILE_DL_PATH = 'file_path'      # file downloaded path

    ACTION_NEXT = 'next'            # action: next page
    ACTION_GLOBAL = 'global'        # action: this item applies to all other item


# how many chapters will be downloaded if weight is PREVIEW
ARTICLE_PREVIEW_CHAPTER_COUNT = 20


class ArticleWeight(Options):
    PREMIUM = 140, 'Premium article'
    CLASSIC = 120, 'Classic article'
    CHOICE = 100, 'Editor choice'
    NORMAL = 80, 'Normal article, need download'
    PREVIEW = 60, 'Preview article, only download %d chapters' % ARTICLE_PREVIEW_CHAPTER_COUNT
    TOC = 40, 'Listed article with TOC captured'
    META = 20, 'Listed article with meta'
    LISTED = 0, 'Only added to db with url (and name)'
    ACHIEVED = -20, 'Achieved article. hide'


class ArticleStatus(Options):
    COMPLETE = 100, 'completely written by author.'
    ABANDON = 80, 'abandoned by author (no updates for 180 days)'
    TERMINATED = 50, 'mark done by editor'
    PROGRESS = 20, 'keep updating in progress'
    INCLUDED = 0, 'added to database'
    DELETED = -100, 'deleted.'
