# -*- coding: utf-8 -*-
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse as dt_parse
import scrapy
import logging
from ..consts import SiteSchemaKey as SSK, Spiders, Schemas, ArticleWeight
from ..db import select
from ..parser import iter_items, urljoin, url_to_relative
from scrapy.utils.project import get_project_settings
from .base import MoltSpiderBase

UTC = timezone.utc
CST = timezone(timedelta(hours=8))
MIN_DATE = datetime.min.replace(tzinfo=CST)

settings = get_project_settings()
LIMIT_INDEX_PAGES = settings['LIMIT_INDEX_PAGES']
log = logging.getLogger(__name__)


class MetaSpider(MoltSpiderBase):
    name = Spiders.META

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.index_last_update_on = {}
        self.index_new_update_on = {}

        t = self.db.DB_t_index
        ta = self.db.DB_t_article
        tl = self.db.DB_t_article_lock
        if not self.db.exist_table(t.name):
            t.create(self.db.conn, checkfirst=True)
        if not self.db.exist_table(ta.name):
            ta.create(self.db.conn, checkfirst=True)
        if not self.db.exist_table(tl.name):
            tl.create(self.db.conn, checkfirst=True)

        stmt = select([t.c.id, t.c.update_on])
        if self.site_ids:
            stmt = stmt.where(t.c.site.in_(self.site_ids))
        try:
            rs = self.db.conn.execute(stmt)
            for r in rs:
                index = r[t.c.id]
                self.index_last_update_on[index] = r[t.c.update_on].replace(tzinfo=CST)
            rs.close()
        except Exception as err:
            log.exception(err)

    def start_requests(self):

        ta = self.db.DB_t_article

        stmt = select([ta.c.id, ta.c.site, ta.c.iid, ta.c.name, ta.c.url, ta.c.weight, ta.c.update_on]
                      ).where(ta.c.weight >= ArticleWeight.META)
        if self.site_ids:
            stmt = stmt.where(ta.c.site.in_(self.site_ids))
        if self.article_ids:
            stmt = stmt.where(ta.c.id.in_(self.article_ids))
        LIMIT_ARTICLES = self.settings.get('LIMIT_ARTICLES', 0)
        if LIMIT_ARTICLES > 0:
            stmt = stmt.limit(LIMIT_ARTICLES)
            log.warning('Limit %s articles. Others wll be ignored.' % LIMIT_ARTICLES)
        rs = self.db.conn.execute(stmt)
        for r in rs:
            schema = self.site_schemas.get(r[ta.c.site])
            index_url = urljoin(schema.get(SSK.URL), r[ta.c.url])
            yield scrapy.Request(index_url, meta={'record': r, 'dont_cache': self.nocache})
        rs.close()

    def parse(self, response):
        ta = self.db.DB_t_article

        r = response.meta['record']
        site = r[ta.c.site]
        iid = r[ta.c.iid]
        aid = r[ta.c.id]
        aname = r[ta.c.name]
        last_update_on = r[ta.c.update_on].replace(tzinfo=CST)
        url = url_to_relative(response.url)

        log.debug('[%s] Parsing %s' % (site, url))

        # if 'Bandwidth exceeded' in response.body:
        #     raise scrapy.exceptions.CloseSpider('bandwidth_exceeded')

        it = {}
        for item in iter_items(self, response, [site, ], Schemas.META_PAGE):
            it.update(item)

        it[ta.c.id.name] = aid
        it[ta.c.url.name] = url

        # url_toc = it.get(ta.c.url_toc.name)
        # if not url_toc:
        #     url_toc = it[ta.c.url.name]
        #     it[ta.c.url_toc.name] = url_toc

        update_on = it.get(ta.c.update_on.name)
        update_on = dt_parse(update_on) if update_on else MIN_DATE
        update_on = update_on.replace(tzinfo=CST)
        it[ta.c.update_on.name] = update_on

        # in case weight not set
        # weight = it.get(ta.c.weight.name)
        # if r[ta.c.weight] < ArticleWeight.META and (weight is None or weight < ArticleWeight.META):
        #     it[ta.c.weight.name] = ArticleWeight.META
        # it[ta.c.status.name] = ArticleStatus.INCLUDED

        if ta.c.name.name not in it:
            it[ta.c.name.name] = aname
        name = it.get(ta.c.name.name)

        log.debug('[%s] captured: %s %s' % (site, url, name))

        table_alone = self.site_schemas.get(site, {}).get(Schemas.META_PAGE, {}).get(SSK.TABLE_ALONE, False)
        if table_alone:
            it[ta.c.chapter_table.name] = self.db.gen_chapter_table_name(aid, site, name)

        # only yield item which is later than the date last updated or no date.
        if update_on == MIN_DATE or update_on > last_update_on:
            yield it
        else:
            log.info('[%s] Skip %s %s due to update time not change' % (site, url, name))
        # handle index last update on
        if update_on > self.index_new_update_on.get(iid, MIN_DATE):
            self.index_new_update_on[iid] = update_on

    def spider_closed(self, spider, reason):

        for index, index_new_update_on in self.index_new_update_on.items():
            if index_new_update_on > self.index_last_update_on.get(index, MIN_DATE):
                # update latest update_on date to home
                t = self.db.DB_t_index
                log.info('Update index (id=%s) last updated to %s.' % (index, index_new_update_on))
                stmt = t.update().values(update_on=index_new_update_on).where(t.c.id == index)
                try:
                    self.db.conn.execute(stmt)
                except Exception:
                    log.exception('Error when update update_on for %s.' % t.name)

        super().spider_closed(spider, reason)