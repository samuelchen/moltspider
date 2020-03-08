# -*- coding: utf-8 -*-
import scrapy
import logging
from ..consts import (
    SiteSchemaKey as SSK, Spiders, Schemas, ArticleWeight,
    ARTICLE_PREVIEW_CHAPTER_COUNT
)
from ..db import select, and_, not_, func
from ..parser import iter_items, urljoin, url_to_relative
from .base import MoltSpiderBase

log = logging.getLogger(__name__)


class TocSpider(MoltSpiderBase):
    """To get article TOC from toc page (or meta page)"""
    name = Spiders.TOC

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pages = 0
        self.chapter_counters = {}
        self.locked_articles = set()

    @property
    def spider_id(self):
        return self.settings.get('SPIDER_ID')

    def start_requests(self):

        ta = self.db.DB_t_article
        tl = self.db.DB_t_article_lock

        # locked article ids by other spider
        stmt_lock = select([tl.c.aid]).where(tl.c.locker!=self.spider_id)
        # articles to be downloaded. Conditions:
        #   * weight >= TOC
        #   * not locked by other spider
        #   * status <= PROGRESS
        stmt = select([ta.c.id, ta.c.site, ta.c.url, ta.c.name, ta.c.weight, ta.c.status,
                       ta.c.url_toc, ta.c.chapter_table, ta.c.update_on])
        if self.article_ids:
            stmt = stmt.where(ta.c.id.in_(self.article_ids))
        elif self.site_ids:
            stmt = stmt.where(ta.c.site.in_(self.site_ids))
        stmt = stmt.where(and_(ta.c.weight >= ArticleWeight.TOC_PREVIEW, not_(ta.c.id.in_(stmt_lock))))
        stmt = stmt.order_by(ta.c.weight.desc(), ta.c.recommends.desc(), ta.c.id)
        if self.limit_articles > 0:
            stmt = stmt.limit(self.limit_articles)
            # log.warning('Limit %s articles. Others wll be ignored.' % self.limit_articles)

        rs = self.db.conn.execute(stmt)
        rs = rs.fetchall()

        # loop unlock articles
        for r in rs:
            rc = self.db.lock_article(article_id=r[ta.c.id], locker=self.spider_id, name=r[ta.c.name])
            if rc >= 0:
                # only yield unlocked or locked-by-self articles

                chapter_table, tc, table_alone = self.db.get_chapter_table_name_def_alone(r)

                if not self.db.exist_table(chapter_table):
                    tc.create(self.db.conn, checkfirst=True)

                self.chapter_counters[r[ta.c.id]] = {'total': 0, 'existed': 0}
                self.locked_articles.add(r[ta.c.id])

                schema = self.site_schemas.get(r[ta.c.site])
                url_toc = r[ta.c.url_toc]
                url_toc = urljoin(schema.get(SSK.URL.code), r[ta.c.url] if url_toc is None else url_toc)
                yield scrapy.Request(url_toc, meta={'record': r, 'dont_cache': self.nocache})

            else:
                log.warning('[%s] %s(id=%s) was locked by other spider.' % (r[ta.c.site], r[ta.c.name], r[ta.c.id]))


    def parse(self, response):

        # if 'Bandwidth exceeded' in response.body:
        #     raise scrapy.exceptions.CloseSpider('bandwidth_exceeded')

        def is_reached_preview_count():
            if aweight == ArticleWeight.TOC_PREVIEW and \
                    self.chapter_counters[aid]['total'] >= ARTICLE_PREVIEW_CHAPTER_COUNT:
                log.warning('[%s] %s(id=%s) reaches %s limit(%s).' % (
                    site, aname, aid, ArticleWeight.TOC_PREVIEW.name, ARTICLE_PREVIEW_CHAPTER_COUNT))
                return True
            return False

        ta = self.db.DB_t_article
        r = response.meta['record']
        conn = self.db.connect()

        # whether standalone table
        chapter_table, tc, table_alone = self.db.get_chapter_table_name_def_alone(r)

        aid = r[ta.c.id]
        aname = r[ta.c.name]
        site = r[ta.c.site]
        aweight = r[ta.c.weight]

        # chapter id, ordered. maybe multiple pages.
        stmt = select([func.max(tc.c.id)])
        cid = conn.execute(stmt).scalar()

        if table_alone:
            cid = cid + 10 if cid else 10
        else:
            cid = cid + 10 if cid else 10   # TODO: +1 or +10 ?

        # finished chapters including chapter, section and conflicts
        existed_sections, existed_chapters = self.cache_existed_chapters(chapter_table=chapter_table, table_def=tc,
                                                                         table_alone=table_alone, aid=aid)
        # keep count of saved chapters. calculate from this number.
        self.chapter_counters[aid]['existed'] = len(existed_chapters) + len(existed_sections)
        log.info('[%s] %s(id=%s) will skip %s chapters which were existed.' % (
            site, aname, aid, self.chapter_counters[aid]['existed']))
        self.chapter_counters[aid]['total'] = self.chapter_counters[aid]['existed']

        if is_reached_preview_count():
            return

        # loop all chapter links in current page
        is_article_marked_not_done = False
        for item in iter_items(self, response, [site, ], Schemas.TOC_PAGE):

            if is_reached_preview_count():
                return

            name = item.get(tc.c.name.name)
            url = item.get(tc.c.url.name)
            item[tc.c.url.name] = url_to_relative(url)
            section = item.get('section')   # db has no "section" column, only "is_section" column
            if section:
                item[tc.c.name.name] = section
                item[tc.c.is_section.name] = True
                del item['section']
                del item[tc.c.url.name]
                item_is_new = section not in existed_sections
            else:
                item_is_new = url not in existed_chapters

            if item_is_new:
                # item[tc.c.done.name] = False
                item['chapter_table'] = chapter_table
                item[SSK.TABLE_ALONE.code] = table_alone
                if not table_alone:
                    item[tc.c.aid.name] = aid
                item[ta.c.id.name] = cid
                self.chapter_counters[aid]['total'] += 1  # total count + 1
                if not is_article_marked_not_done:
                    self.db.mark_article_done([aid, ], done=False)
                    is_article_marked_not_done = True
                yield item
            else:
                log.debug('[%s] Skipped existed chapter(section) %s' % (site, name))

            cid += 10 if table_alone else 1

        # none standalone table no TOC
        if (not table_alone) and self.chapter_counters[aid]['total'] == self.chapter_counters[aid]['existed']:
            url = url_to_relative(response.url)
            if url not in existed_chapters:
                yield {
                    tc.c.aid.name: aid,
                    tc.c.url.name: url,
                    tc.c.name.name: '',
                    'chapter_table': chapter_table,
                    SSK.TABLE_ALONE.code: table_alone
                }
                self.chapter_counters[aid]['total'] += 1
                if not is_article_marked_not_done:
                    self.db.mark_article_done([aid, ], done=False)
            else:
                log.debug('[%s] Skipped existed chapter(section) %s' % (site, url))

        # self.chapter_counters[article_id]['done'] = True
        log.info('[%s] %s(id=%s) chapters counts: total=%s, existed=%s (including duplicates)' % (
            site, aname, aid, self.chapter_counters[aid]['total'],
            self.chapter_counters[aid]['existed']))

    # def log_articles(self, articles):
    #
    #     base_dir = self.settings.get('BASE_DIR', '../')
    #     fname = os.path.join(base_dir, 'log', 'chapter_articles.log')
    #     os.makedirs(os.path.dirname(fname), exist_ok=True)
    #     with open(fname, 'w') as f:
    #         f.write('article')
    #         for r in articles:
    #             f.write('+')
    #             f.write('%s_%s' % (r['id'], r['name']))
    #         f.write('.log')

    def cache_existed_chapters(self, chapter_table, table_def, table_alone, aid):
        existed_chapters = set()
        existed_sections = set()

        conn = self.db.connect()

        # finished chapters
        tc = table_def
        stmt = select([tc.c.id, tc.c.name, tc.c.is_section, tc.c.url])
        if not table_alone:
            stmt = stmt.where(tc.c.aid == aid)
        rs = conn.execute(stmt)

        # cache finished urls
        for r in rs:
            if r[tc.c.is_section]:
                existed_sections.add(r[tc.c.name])
            else:
                existed_chapters.add(r[tc.c.url])
        rs.close()

        # conflict chapters
        if table_alone:
            tcc = self.db.get_db_t_chapter_conflict(chapter_table)
        else:
            tcc = self.db.get_db_t_site_chapter_conflict(chapter_table)
        if self.db.exist_table(tcc.name):
            stmt = select([tcc.c.id, tcc.c.name, tcc.c.is_section, tcc.c.url])
            if not table_alone:
                stmt = stmt.where(tc.c.aid == aid)
            rs = self.db.conn.execute(stmt)

            # cache conflict urls
            for r in rs:
                if r[tcc.c.is_section]:
                    if r[tcc.c.name] in existed_sections:
                        # do not miss duplicated section, otherwise, will miss a saved count.
                        existed_sections.add('%s_%s' % (r[tcc.c.name], r[tcc.c.id]))
                    else:
                        existed_sections.add(r[tcc.c.name])
                else:
                    existed_chapters.add(r[tcc.c.url])
            rs.close()

        return existed_sections, existed_chapters

    def spider_closed(self, spider, reason):

        for aid in spider.locked_articles:
            self.db.unlock_article(article_id=aid, locker=self.spider_id)

        super().spider_closed(spider, reason)
