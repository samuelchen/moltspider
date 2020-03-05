# -*- coding: utf-8 -*-
import scrapy
import logging
from datetime import timezone, timedelta, datetime
from ..consts import SiteSchemaKey as SSK, SchemaOtherKey as SOK, Spiders, Schemas, ArticleWeight, ArticleStatus
from ..db import select, and_
from ..parser import iter_items, urljoin
from .base import MoltSpiderBase

UTC = timezone.utc
CST = timezone(timedelta(hours=8))
MIN_DATE = datetime.min.replace(tzinfo=CST)

log = logging.getLogger(__name__)


class ChapterSpider(MoltSpiderBase):
    """To crawl index pages to parse all article list."""
    name = Spiders.CHAPTER

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.locked_articles = set()
        self.counters = {}

        ta = self.db.DB_t_article
        if not self.db.exist_table(ta.name):
            ta.create(self.db.conn, checkfirst=True)

    @property
    def spider_id(self):
        return self.settings.get('SPIDER_ID')

    def start_requests(self):

        ta = self.db.DB_t_article

        # select matched articles
        stmt = select([ta.c.id, ta.c.site, ta.c.name, ta.c.chapter_table, ta.c.update_on]).where(
            and_(ta.c.weight >= ArticleWeight.PREVIEW, ta.c.done == False, ta.c.status <= ArticleStatus.PROGRESS))
        if self.site_ids:
            stmt = stmt.where(ta.c.site.in_(self.site_ids))
        if self.article_ids:
            stmt = stmt.where(ta.c.id.in_(self.article_ids))
        if self.index_ids:
            stmt = stmt.where(ta.c.iid.in_(self.index_ids))
        stmt = stmt.order_by(ta.c.weight.desc(), ta.c.recommends.desc(), ta.c.id)
        LIMIT_ARTICLES = self.settings.get('LIMIT_ARTICLES', 0)
        if LIMIT_ARTICLES > 0:
            stmt = stmt.limit(LIMIT_ARTICLES)
            log.warning('Limit %s articles. Others wll be ignored.' % LIMIT_ARTICLES)

        rs = self.db.conn.execute(stmt)

        # loop articles
        for r in rs:
            site = r[ta.c.site]
            aid = r[ta.c.id]
            rc = self.db.lock_article(article_id=aid, locker=self.spider_id, name=r[ta.c.name])
            if rc >= 0:
                self.locked_articles.add(aid)

                chapter_table, tc, table_alone = self.db.get_chapter_table_name_def_alone(
                    r[ta.c.chapter_table], site)

                if not self.db.exist_table(chapter_table):
                    tc.create(self.db.conn, checkfirst=True)

                # select no content chapters
                site_url = self.site_schemas.get(site).get(SSK.URL.code)
                stmt = select([tc.c.id, tc.c.url, tc.c.name])
                if not table_alone:
                    stmt = stmt.where(tc.c.aid == aid)
                stmt = stmt.where(tc.c.content==None).order_by(tc.c.id)
                LIMIT_CHAPTERS = self.settings.get('LIMIT_CHAPTERS', 0)
                if LIMIT_CHAPTERS > 0:
                    stmt = stmt.limit(LIMIT_CHAPTERS)
                    log.warning('Limit %s chapters. Others wll be ignored.' % LIMIT_CHAPTERS)

                rs1 = self.db.conn.execute(stmt)

                # loop chapters
                self.counters[aid] = 0
                for r1 in rs1:
                    chapter_url = urljoin(site_url, r1[tc.c.url])
                    self.counters[aid] += 1
                    yield scrapy.Request(chapter_url, meta={'record': r1, 'chapter_table': chapter_table,
                                                            SOK.SITE.code: site, SSK.TABLE_ALONE.code: table_alone,
                                                            'aid': aid, 'aname': r[ta.c.name],
                                                            'dont_cache': self.nocache})

            else:
                log.warning('[%s] %s(id=%s) is locked by other spider.' % (site, r[ta.c.name], aid))

    def parse(self, response):
        r = response.meta['record']
        chapter_table = response.meta['chapter_table']
        table_alone = response.meta[SSK.TABLE_ALONE.code]
        site = response.meta[SOK.SITE.code]
        aid = response.meta['aid']
        aname = response.meta['aname']

        if table_alone:
            tc = self.db.get_db_t_chapter(chapter_table)
        else:
            tc = self.db.get_db_t_site_chapter(chapter_table)

        for item in iter_items(self, response, [site, ], Schemas.CHAPTER_PAGE):
            item[tc.c.id.name] = r[tc.c.id]
            item[tc.c.name.name] = r[tc.c.name]

            item['chapter_table'] = chapter_table
            item[SSK.TABLE_ALONE.code] = table_alone
            if not table_alone:
                item[tc.c.aid.name] = aid
            item[SOK.SITE.code] = site
            item['aname'] = aname

            yield item

    def spider_closed(self, spider, reason):
        ta = self.db.DB_t_article
        for aid in spider.locked_articles:
            self.db.unlock_article(article_id=aid, locker=self.spider_id)

        super().spider_closed(spider, reason)
