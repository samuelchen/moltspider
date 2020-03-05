# -*- coding: utf-8 -*-
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse as dt_parse
import scrapy
import logging
from ..consts import (
    SiteSchemaKey as SSK, SchemaOtherKey as SOK,
    Spiders, Schemas,
    ArticleWeight, ArticleStatus,
)
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


class ListSpider(MoltSpiderBase):
    """To get article list from index page"""
    name = Spiders.LIST

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ta = self.db.DB_t_article
        tl = self.db.DB_t_article_lock
        if not self.db.exist_table(ta.name):
            ta.create(self.db.conn, checkfirst=True)
        if not self.db.exist_table(tl.name):
            tl.create(self.db.conn, checkfirst=True)
        self.pages = 0

        # cache all saved articles (site, name)
        stmt = select([ta.c.site, ta.c.name])
        if self.site_ids:
            stmt = stmt.where(ta.c.site.in_(self.site_ids))
        if self.index_ids:
            stmt = stmt.where(ta.c.iid.in_(self.index_ids))
        rs = self.db.conn.execute(stmt)
        self.saved_articles = {(r[ta.c.site], r[ta.c.name]) for r in rs}
        log.info('Cached %s articles' % len(self.saved_articles))

    def start_requests(self):

        t = self.db.DB_t_index

        stmt = select([t.c.id, t.c.site, t.c.url, t.c.update_on])
        if self.site_ids:
            stmt = stmt.where(t.c.site.in_(self.site_ids))
        if self.index_ids:
            stmt = stmt.where(t.c.id.in_(self.index_ids))
        rs = self.db.conn.execute(stmt)
        for r in rs:
            schema = self.site_schemas.get(r[t.c.site])
            index_url = urljoin(schema.get(SSK.URL.code), r[t.c.url])
            yield scrapy.Request(index_url, meta={'record': r, 'dont_cache': self.nocache})

    def parse(self, response):
        r = response.meta['record']
        t = self.db.DB_t_index
        ta = self.db.DB_t_article

        resp_path = url_to_relative(response.url)
        site = r[t.c.site]

        # handle new update time
        last_update_on = r[t.c.update_on]
        last_update_on = last_update_on.replace(tzinfo=CST)
        new_update_on = last_update_on

        log.info('[%s] Parsing %s' % (site, resp_path))

        # if 'Bandwidth exceeded' in response.body:
        #     raise scrapy.exceptions.CloseSpider('bandwidth_exceeded')

        is_empty_page = True
        is_all_duplicated = True
        for item in iter_items(self, response, [site, ], Schemas.INDEX_PAGE):
            if item.get(SSK.ACTION.code) == SOK.ACTION_NEXT.code:
                self.pages += 1
                if self.pages > LIMIT_INDEX_PAGES > 0:
                    log.info('[%s] Quit from %s. Reach LIMIT_INDEX_PAGES(%s)' % (site, resp_path, LIMIT_INDEX_PAGES))
                    break
                elif is_empty_page:
                    log.info('[%s] Quit from %s due to empty page' % (site, resp_path))
                    break
                elif is_all_duplicated:
                    log.info('[%s] Quit from %s due to all duplicated' % (site, resp_path))
                    break
                else:
                    log.info('[%s] Capturing %s pages' % (site, self.pages))
                    next_page = item.get(SSK.URL.code)
                    if next_page is not None:
                        log.debug('[%s] next page: %s' % (site, next_page))
                        yield response.follow(next_page, callback=self.parse, meta=response.meta)
                    else:
                        log.info('[%s] Quit from %s due to next page link not captured' % (site, resp_path))
                        break
            else:
                full_url = item.get(ta.c.url.name)
                url = url_to_relative(full_url)

                # site = item.get(SOK.SITE.name)     # parser.iter_item added
                name = item.get(ta.c.name.name)

                update_on = item.get(ta.c.update_on.name)
                update_on = dt_parse(update_on) if update_on else MIN_DATE
                update_on = update_on.replace(tzinfo=CST)
                if update_on > last_update_on and update_on > new_update_on:
                    new_update_on = update_on

                if not site or not url:
                    continue

                is_empty_page = False
                item.update({
                        ta.c.iid.name: r[t.c.id],
                        ta.c.url.name: url,
                        ta.c.status.name: ArticleStatus.INCLUDED,
                        ta.c.update_on.name: update_on
                    })
                if ta.c.weight.name not in item:
                    item[ta.c.weight.name] = ArticleWeight.LISTED

                if not (site, name) in self.saved_articles:
                    log.debug('[%s] captured: %s %s' % (site, url, name))
                    is_all_duplicated = False
                    yield item
                else:
                    log.debug('[%s] duplicate: %s %s' % (site, url, name))

        if new_update_on > last_update_on:
            # update latest update_on date to home
            t = self.db.DB_t_index
            log.info('[%s] Update index %s last updated to %s.' % (site, resp_path, new_update_on))
            stmt = t.update().values(update_on=new_update_on).where(t.c.url == resp_path)
            try:
                self.db.conn.execute(stmt)
            except Exception:
                log.exception('Error when update update_on for %s.' % t.name)

        return
