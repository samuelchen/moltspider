import scrapy
import logging
from ..db import Database

log = logging.getLogger(__name__)


class MoltSpiderBase(scrapy.Spider):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = Database.get_inst()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=scrapy.signals.spider_closed)
        return spider

    def spider_closed(self, spider, reason):
        log.info('[%s] Spider closed (%s).' % (spider.name, reason))
