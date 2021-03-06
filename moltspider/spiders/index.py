# -*- coding: utf-8 -*-
import scrapy
import logging
from dateutil.parser import parse as dt_parse
from ..consts import (
    SiteSchemaKey as SSK, Spiders, Schemas, SchemaOtherKey as SOK,
    MIN_DATE
)
from ..db import select
from ..parser import iter_items, url_to_relative
from .base import MoltSpiderBase

log = logging.getLogger(__name__)


class IndexSpider(MoltSpiderBase):
    """To crawl index pages to parse all article list."""
    name = Spiders.INDEX

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def start_requests(self):
        for site in self.site_ids or self.site_schemas.keys():
            schema = self.site_schemas.get(site)
            url = schema.get(SSK.URL.code)
            yield scrapy.Request(url, meta={SOK.SITE.code: site, 'dont_cache': self.nocache})

    def parse(self, response):
        site = response.meta[SOK.SITE.code]
        cached_indexes = self.get_cached_indexes(site)
        t = self.db.DB_t_index
        skip_count = 0
        for item in iter_items(self, response, [site, ], Schemas.HOME_PAGE):
            url = url_to_relative(item.get(t.c.url.name, ''))
            if url and url not in cached_indexes:
                item[t.c.url.name] = url
                update_on = item.get(t.c.update_on.name)
                item[t.c.update_on.name] = dt_parse(update_on) if update_on else MIN_DATE
                yield item
            else:
                log.debug('[%s] Skip existing index %s' % (site, url))
                skip_count += 1

        if skip_count > 0:
            log.warning('[%s] Skipped %s indexes' % (site, skip_count))

    def get_cached_indexes(self, site):
        t = self.db.DB_t_index
        stmt = select([t.c.url]).where(t.c.site==site)
        rs = self.db.conn.execute(stmt)
        cached = {r[t.c.url] for r in rs}
        return cached
