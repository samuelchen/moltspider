from abc import ABC
import scrapy
import logging
from ..db import Database
from ..parser import SiteSchemas, arg_get_site_ids, args_get_index_ids, args_get_article_ids
from ..consts import SiteSchemaKey as SSK
from urllib.parse import urlparse
log = logging.getLogger(__name__)


class MoltSpiderBase(scrapy.Spider, ABC):

    # allowed_domains = [urlparse(s.get(SSK.URL.code))[1].lstrip('www.') for s in SiteSchemas.values()]
    allowed_domains = []
    start_urls = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site_schemas = SiteSchemas
        self.db = Database.get_inst()
        self.site_ids = arg_get_site_ids(**kwargs)
        self.index_ids = args_get_index_ids(**kwargs)
        self.article_ids = args_get_article_ids(**kwargs)
        self.nocache = 'nocache' in args
        # self.allowed_domains = [urlparse(SiteSchemas[s].get(SSK.URL.code))[1].lstrip('www.') for s in self.site_ids]

    def __init_db(self):
        t = self.db.DB_t_index
        if not self.db.exist_table(t.name):
            t.create(self.db.conn, checkfirst=True)
        ta = self.db.DB_t_article
        if not self.db.exist_table(ta.name):
            ta.create(self.db.conn, checkfirst=True)
        tl = self.db.DB_t_article_lock
        if not self.db.exist_table(tl.name):
            tl.create(self.db.conn, checkfirst=True)
        txm = self.db.DB_t_article_ex_meta
        if not self.db.exist_table(txm.name):
            txm.create(self.db.engine)
        tt = self.db.DB_t_article_tag
        if not self.db.exist_table(tt.name):
            tt.create(self.db.engine)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=scrapy.signals.spider_closed)
        return spider

    def spider_closed(self, spider, reason):
        log.info('[%s] Spider closed (%s).' % (spider.name, reason))
