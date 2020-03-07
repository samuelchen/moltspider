# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from datetime import timezone, datetime, date, timedelta
import os
import scrapy
from slugify import slugify
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline, FilesPipeline
from scrapy.utils.project import get_project_settings
from .db import Database, select
from .consts import Spiders, SiteSchemaKey as SSK, SchemaOtherKey as SOK
from .utils import gen_hash_file_path, gen_file_path

import logging

UTC = timezone.utc
CST = timezone(timedelta(hours=8))
MIN_DATE = datetime.min.replace(tzinfo=CST)

settings = get_project_settings()

ALBUMS_URL_FIELD = settings.get("IMAGES_URL_FIELD", 'album')
ALBUMS_RESULT_FIELD = settings.get("IMAGES_RESULT_FIELD", 'album_path')
ALBUMS_STORE = settings.get("IMAGES_STORE", 'albums')
FILES_URL_FIELD = settings.get("FILES_URL_FIELD", 'file')
FILES_RESULT_FIELD = settings.get("FILES_RESULT_FIELD", 'file_path')
FILES_STORE = settings.get("FILES_STORE", 'medias')

log = logging.getLogger(__name__)


class MoltPipelineBase(object):
    def __init__(self):
        self.db = Database.get_inst()
        # self.trans = None

    def open_spider(self, spider):
        log.debug('Database connected (%s).' % self.db.status)

    def close_spider(self, spider):
        log.debug('Database disconnected (%s).' % self.db.status)


class DatabasePipeline(MoltPipelineBase):

    def __init__(self):
        super().__init__()

        # counter to calculate saved chapters count. {article_id: saved_count}
        self.counters = {}

        # chapters count to be crawled. { article_id: count }
        self.chapter_counter = {}

    def process_item(self, item, spider):
        tc = self.db.DB_t_index
        ta = self.db.DB_t_article

        if spider.name == Spiders.INDEX:
            url = item.get(tc.c.url.name)
            site = item.get(tc.c.site.name)
            if not (url and site):
                log.info('[%s][%s] Drop %s' % (site, spider.name, item))
                return item

            it = self.copy_items_for_db(item)
            stmt = tc.insert().values(**it)
            try:
                self.db.conn.execute(stmt)
            except Database.IntegrityError:
                log.warning('[%s][%s] conflict index: %s' % (site, spider.name, url))

        elif spider.name == Spiders.LIST:
            site = item.get(ta.c.site.name)
            name = item.get(ta.c.name.name)
            url = item.get(ta.c.url.name)
            if not (url and site):
                log.info('[%s][%s] Drop %s' % (site, spider.name, item))
                return item

            it = self.copy_items_for_db(item)
            stmt = ta.insert().values(**it)
            try:
                rs = self.db.conn.execute(stmt)
                aid = rs.inserted_primary_key[0]
                log.info('[%s][%s] New article %s (id=%s) added.' % (site, spider.name, name, aid))

            except Database.IntegrityError:
                log.warning('[%s][%s] conflict article: %s %s' % (site, spider.name, name, url))

        elif spider.name == Spiders.META:

            aid = item.get(ta.c.id.name)
            site = item.get(ta.c.site.name)
            name = item.get(ta.c.name.name)
            url = item.get(ta.c.url.name)

            it = self.copy_items_for_db(item)
            for c in [ta.c.id, ta.c.site, ta.c.url]:
                if c.name in it:
                    del it[c.name]
            stmt = ta.update().values(**it)
            stmt = stmt.where(ta.c.id == aid) #.returning(ta.c.id)

            try:
                rs = self.db.conn.execute(stmt)
                log.info('[%s][%s] Article "%s"(id=%s, url=%s) updated.' % (site, spider.name, name, aid, url))
            except Exception as err:
                log.exception('[%s][%s] Error for %s(id=%s) %s' % (site, spider.name, name, aid, url))

        elif spider.name == Spiders.TOC:

            chapter_table = item['chapter_table']
            table_alone = item[SSK.TABLE_ALONE.code]
            if table_alone:
                aid, site, aname = self.db.split_chapter_table_name(chapter_table)
            else:
                site = self.db.split_site_chapter_table_name(chapter_table)
                aid = item['aid']
                aname = ''

            it = self.copy_items_for_db(item)
            del it['chapter_table']
            del it[SSK.TABLE_ALONE.code]
            if ta.c.site.name in it:
                del it[ta.c.site.name]

            # get total count of chapters from spider
            # counter = spider.chapter_counters.get(aid)
            # local counter to count save chapters
            # if aid not in self.counters:
            #     self.counters[aid] = counter['existed']     # count number begin from saved count

            # log.debug('Chapters counts: total=%s(%s), existed=%s' % (
            #     counter['total'], 'done' if counter['done'] else 'counting', self.counters[article_id]))

            # get db table definition
            if table_alone:
                tc = self.db.get_db_t_chapter(chapter_table)
            else:
                tc = self.db.get_db_t_site_chapter(chapter_table)

            # insert chapter/section
            is_conflict = False
            stmt = tc.insert().values(**it)
            try:
                self.db.conn.execute(stmt)
                log.info('[%s][%s] %s(id=%s) Saved %s(id=%s), url=%s)' % (
                    site, spider.name, aname, aid,
                    it.get(tc.c.name.name), it.get(tc.c.id.name), it.get(tc.c.url.name)))
                # self.counters[aid] += 1
            except Database.IntegrityError as err:
                is_conflict = True
                log.warning('[%s][%s] %s(id=%s) conflict %s %s' % (site, spider.name,
                            aname, aid, it.get(tc.c.name.name), it.get(tc.c.url.name)))

            if is_conflict and settings.get('CHAPTER_KEEP_CONFLICT', False):
                # add conflict chapter to conflict table
                stmt = select([tc.c.id]).where(tc.c.name == it.get(tc.c.name.name))
                if not table_alone:
                    stmt = stmt.where(tc.c.aid == aid)
                cid = self.db.conn.execute(stmt).scalar()
                if cid:
                    # insert conflict chapter
                    if table_alone:
                        tcc = self.db.get_db_t_chapter_conflict(chapter_table)
                    else:
                        tcc = self.db.get_db_t_site_chapter_conflict(chapter_table)
                    if not self.db.exist_table(tcc.name):
                        tcc.create(self.db.engine, checkfirst=True)

                    it[tcc.c.conflict_cid.name] = cid
                    stmt = tcc.insert().values(**it)
                    try:
                        self.db.conn.execute(stmt)
                    except Database.IntegrityError:
                        pass

            # if self.counters[article_id] >= counter['total']:
            #     self.db.unlock_article(article_id=article_id, locker=spider.spider_id)
            #     log.info('[%s][%s] article %s(id=%s) TOC is finished downloading.' % (site, spider.name, article_name, article_id))

        elif spider.name == Spiders.CHAPTER:

            chapter_table = item['chapter_table']
            table_alone = item[SSK.TABLE_ALONE.code]
            if table_alone:
                tc = self.db.get_db_t_chapter(chapter_table)
                aid, site, aname = self.db.split_chapter_table_name(chapter_table)
            else:
                tc = self.db.get_db_t_site_chapter(chapter_table)
                site = self.db.split_site_chapter_table_name(chapter_table)
                aid = item[tc.c.aid.name]
                aname = ''

            cid = item[tc.c.id.name]
            cname = item[tc.c.name.name]

            if aid not in self.chapter_counter:
                self.chapter_counter[aid] = 0       # counter for current article

            # update chapter content
            stmt = tc.update().values(content=item.get(tc.c.content.name)).where(tc.c.id==cid)
            try:
                self.db.conn.execute(stmt)
                self.chapter_counter[aid] += 1
                log.info('[%s][%s] Article %s(id=%s) saved content %s(id=%s)' % (
                    site, spider.name, aname, aid, cname, cid))
            except Exception:
                log.exception('[%s][%s] %s(id=%s) error saving content %s %s' % (
                    site, spider.name, aname, aid, cname, item.get(tc.c.url.name)))

            # check count and mark article done
            count = spider.counters.get(aid)
            if count is None:
                log.error('[%s][%s] Article %s(id=%s) has no counter.' % (site, spider.name, aname, aid))
                count = 0
            if count == self.chapter_counter[aid]:
                self.db.mark_article_done([aid, ], True)
                log.info('[%s][%s] Article %s(id=%s) all chapters captured.' % (site, spider.name, aname, aid))

        else:
            log.error('Unknown spider <%s>' % spider.name)

        return item

    def copy_items_for_db(self, item):
        it = item.copy()
        for k in [SSK.ACTION.code, ALBUMS_URL_FIELD, ALBUMS_RESULT_FIELD, FILES_URL_FIELD, FILES_RESULT_FIELD]:
            if k in it:
                del it[k]

        return it


class TagsPipeline(MoltPipelineBase):

    def __init__(self):
        super().__init__()

    def process_item(self, item, spider):
        ta = self.db.DB_t_article
        tt = self.db.DB_t_article_tag

        if spider.name in [Spiders.LIST, Spiders.META]:
            aid = item.get(ta.c.id.name)
            aname = item.get(ta.c.name.name)
            if aid:
                tags = set()
                removed_keys = set()

                for k in item.keys():
                    if k.startswith(SSK.TAG_PREFIX.code):
                        tag = item.get(k)
                        if isinstance(tag, str):
                            tags.add(tag)
                        elif isinstance(tag, (list, tuple, set)):
                            tags.update(tag)
                        else:
                            log.error('Article %s(id=%s) captured tag(%s) "%s" is not str, list, tuple or set.',
                                      aname, aid, k, tag)

                        removed_keys.add(k)

                try:
                    if tags:
                        records = []
                        for tag in tags:
                            records.append({
                                tt.c.aid.name: aid,
                                tt.c.tag.name: tag
                            })
                        self.db.conn.execute(tt.insert(), records)
                except Database.IntegrityError as err:
                    pass
                except Exception as err:
                    log.exception('Fail to insert tags %s for article %s(id=%s)' % (tags, aname, aid))

                for k in removed_keys:
                    del item[k]

        return item


class ExtraMetaPipeline(MoltPipelineBase):

    def __init__(self):
        super().__init__()

    def process_item(self, item, spider):
        ta = self.db.DB_t_article
        txm = self.db.DB_t_article_ex_meta

        if spider.name in [Spiders.LIST, Spiders.META]:
            aid = item.get(ta.c.id.name)
            aname = item.get(ta.c.name.name)
            if aid:
                metas = {}
                removed_keys = set()

                for k in item.keys():
                    if k.startswith(SSK.META_PREFIX.code):
                        if len(k) > 1:
                            meta = item.get(k)
                            metas[k[1:]] = meta.strip()
                        else:
                            log.error('Article %s(id=%s) meta key "%s" is empty', aname, aid, k)

                        removed_keys.add(k)

                try:
                    if metas:
                        records = []
                        for k, meta in metas.items():
                            records.append({
                                txm.c.aid.name: aid,
                                txm.c.key.name: k,
                                txm.c.value.name: meta
                            })
                        rs = self.db.conn.execute(txm.insert(), records)
                        rs.close()
                except Database.IntegrityError as err:
                    log.warning('Duplicate extra meta %s for article %s(id=%s)' % (metas, aname, aid))
                    log.warning(str(err))
                except Exception as err:
                    log.exception('Fail to insert metas %s for article %s(id=%s)' % (metas, aname, aid))

                for k in removed_keys:
                    del item[k]

        return item


class AlbumPipeline(ImagesPipeline):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_media_requests(self, item, info):
        if info.spider.name in [Spiders.LIST, Spiders.META]:
            urls = item.get(ALBUMS_URL_FIELD, [])
            if not isinstance(urls, (list, tuple, set)):
                urls = [urls, ]
            site = item.get(SOK.SITE.code, '')
            aid = item.get('aid', '')
            cid = item.get('id', '')
            name = item.get('name', '')
            for url in urls:
                if url:
                    fpath = gen_file_path(url=url)
                    item[Database.DB_t_article.c.cover.name] = fpath        # add path to 'cover' field (will save)

                    full_path = os.path.join(ALBUMS_STORE, site, fpath)
                    if os.path.exists(full_path):
                        log.info('Cover %s on %s (aid=%s, cid=%s) already exists. Skip.' % (fpath, site, aid, cid))
                    else:
                        log.info('Download %s(id=%s) album cover to %s' % (name, aid, full_path))
                        yield scrapy.Request(url, meta={'item': item})

    def file_path(self, request, response=None, info=None):
        item = request.meta.get('item', {})
        site = item.get(SOK.SITE.code, '_all')
        return '%s/%s' % (site, gen_file_path(url=request.url))

    def media_failed(self, failure, request, info):
        item = request.meta.get('item', {})

        # remove 'cover' field if failed
        if Database.DB_t_article.c.cover.name in item:
            del item[Database.DB_t_article.c.cover.name]

        super().media_failed(failure, request, info)


class FilePipeline(FilesPipeline):

    def get_media_requests(self, item, info):
        urls = item.get(FILES_URL_FIELD, [])
        if not isinstance(urls, (list, tuple, set)):
            urls = [urls, ]
        site = item.get(SOK.SITE.code, '')
        aid = item.get('aid', '')
        if not aid and info.spider.name in [Spiders.LIST, Spiders.TOC, Spiders.META]:
            aid = item.get('id', '')
        name = item.get('name', '')
        for url in urls:
            if url:
                fpath = gen_file_path(url=url)
                fpath = os.path.join(FILES_STORE, site, fpath)
                if os.path.exists(fpath):
                    log.info('File %s on %s (aid=%s) already exists. Skip.' % (name, site, aid))
                else:
                    yield scrapy.Request(url, meta={'item': item})
                    log.info('Download %s(id=%s) album cover to %s' % (name, aid, fpath))

    def file_path(self, request, response=None, info=None):
        item = request.meta.get('item', {})
        site = item.get(SOK.SITE.code, '_all')
        return '%s/%s' % (site, gen_file_path(url=request.url))
