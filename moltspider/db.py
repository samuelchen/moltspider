#!/usr/bin/env python
# coding:utf-8

__author__ = 'samuel'
__date__ = '18/3/2'

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, SmallInteger, String, Boolean, Text, DateTime, BLOB
from sqlalchemy import MetaData, ForeignKey, Sequence, UniqueConstraint
from sqlalchemy.sql import select, update
from sqlalchemy.sql.expression import not_, and_, or_, true as true_
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from .consts import DB_T_DOT_ESCAPE, DB_T_NAME_SEP
import logging

UTC = timezone.utc
CST = timezone(timedelta(hours=8))
MIN_DATE = datetime.min.replace(tzinfo=CST)
CONFLICT_SUFFIX = '_conflict'

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARN)
log = logging.getLogger(__name__)


def get_timestamp():
    return datetime.now().replace(tzinfo=CST)


def mark_done(engine_or_conn, table, col_pk, pks, done=True):
    stmt = table.update().where(and_(col_pk.in_(pks), table.c.done is not done)).values(done=done)
    # if col_returns:
    #     stmt = stmt.returning(col_returns)
    return engine_or_conn.execute(stmt)


# get definition of chapter table to store chapters from one article (TABLE_ALONE is True)
# name is table name (may be name, name hash or etc.)
# def def_db_t_chapter(name, meta, schema=None):
#     return Table(name, meta,
#                  Column('id', Integer, primary_key=True, index=True),
#                  Column('name', String(100), unique=True, nullable=False),
#                  Column('is_section', Boolean, default=False),
#                  Column('url', Text, unique=True),
#                  Column('content', Text),
#                  Column('done', Boolean, default=False),        # TODO: remove this col ?
#                  Column('timestamp', DateTime(timezone=True), default=get_timestamp, onupdate=get_timestamp),
#                  schema=schema
#                  )


def def_db_t_chapter_base(name, meta, schema=None):
    return Table(name, meta,
                 Column('id', Integer, primary_key=True, index=True),
                 Column('name', String(100), nullable=False),
                 Column('is_section', Boolean, default=False),
                 Column('url', Text, unique=True),
                 Column('timestamp', DateTime(timezone=True), default=get_timestamp, onupdate=get_timestamp),
                 schema=schema
                 )


def def_db_t_chapter(name, meta, schema=None):
    t = def_db_t_chapter_base(name, meta, schema)
    t.append_column(Column('content', Text))
    return t


# conflict chapter for DB_t_chapter
def def_db_t_chapter_conflict(name, meta, schema=None):
    t = def_db_t_chapter_base(name, meta, schema)
    t.append_column(Column('conflict_cid', Integer))
    return t


# get definition of chapter table to store chapters from all sites (table_alone is False or not presents)
# name is table name (typically it's 's_' + site id)
# def def_db_t_site_chapter(name, meta, schema=None):
#     return Table(name, meta,
#                  Column('id', Integer, primary_key=True, index=True),
#                  Column('aid', Integer, ForeignKey(Database.DB_t_article.c.id, ondelete='CASCADE'), index=True),
#                  Column('name', String(100), index=True),
#                  Column('is_section', Boolean, default=False),
#                  Column('url', Text),
#                  Column('content', Text),
#                  Column('done', Boolean, default=False),
#                  Column('timestamp', DateTime(timezone=True), default=get_timestamp, onupdate=get_timestamp),
#                  UniqueConstraint('aid', 'url'),
#                  schema=schema
#                  )

def def_db_t_site_chapter(name, meta, schema=None):
    t = def_db_t_chapter_base(name, meta, schema)
    t.append_column(Column('aid', Text))
    t.append_column(Column('content', Text))
    t.append_constraint(UniqueConstraint('aid', 'url'))
    return t


# conflict chapter for DB_t_site_chapter
def def_db_t_site_chapter_conflict(name, meta, schema=None):
    t = def_db_t_site_chapter(name, meta, schema)
    t.append_column(Column('conflict_cid', Integer))
    return t


class Database(object):

    IntegrityError = IntegrityError
    meta = MetaData()
    schema = None
    __inst = None

    DB_t_index = Table('index', meta,
                       Column('id', Integer, primary_key=True, autoincrement=True),
                       Column('site', String(50), index=True),  # site id, supported sites schema file name.
                       Column('text', String(100)),         # display text of the index link
                       Column('url', Text, index=True),  # index url path (no http schema and domain)
                       Column('update_on', DateTime(timezone=True)),  # when the articles on this index last updated

                       UniqueConstraint('site', 'url'),

                       schema=schema
                       )

    DB_t_article = Table('article', meta,
                         Column('id', Integer, primary_key=True, autoincrement=True),
                         Column('iid', Integer, ForeignKey(DB_t_index.c.id, ondelete='SET NULL'), index=True,
                                nullable=True),      # foreign key, index.id
                         Column('name', String(100), index=True),  # article name
                         Column('site', String(50), index=True),  # site id, supported sites schema file name.
                         Column('url', Text),  # article cover/meta page url
                         Column('weight', SmallInteger, index=True),   # weight level (choice, list, normal ..), see consts.ArticleWeight
                         Column('done', Boolean, default=False),  # whether listed chapters are all downloaded.

                         # TODO: split some fields into a new table 'article_meta'
                         Column('author', String(50), index=True),  # article author name
                         Column('category', String(50), index=True),  # article type
                         Column('length', Integer, default=0),  # article length in words
                         Column('status', Integer, index=True),  # completed or to be continued
                         Column('desc', Text),
                         Column('license', String(50)),  # which site has the license
                         Column('favorites', Integer, default=0),  # favorite count
                         Column('recommends', Integer, default=0),  # recommendation count
                         Column('recommends_month', Integer, default=0),  # recommendation count of this month
                         Column('update_on', DateTime(timezone=True)),  # last updated datetime by the author
                         Column('url_toc', Text),  # url of toc page

                         Column('cover', String(100)),  # cover img file name with relative path, ext

                         # chapter table name in DB for this article
                         # if None, means do not create standalone table (use site chapter table)
                         # set "table_alone" to "true" to enable it.
                         # most for novel, comic sites (many chapters per article)
                         # not for news site (1 or several chapters per article)
                         Column('chapter_table', String(100), unique=True),

                         # last modified datetime of record
                         Column('timestamp', DateTime(timezone=True), default=get_timestamp, onupdate=get_timestamp),

                         UniqueConstraint('site', 'name'),
                         UniqueConstraint('site', 'url'),

                         schema=schema
                         )

    DB_t_article_lock = Table('article_lock', meta,
                              Column('id', Integer, primary_key=True, autoincrement=True),
                              Column('aid', Integer, ForeignKey(DB_t_article.c.id, ondelete='CASCADE'), unique=True),
                              Column('name', String(100)),
                              Column('locker', String(100), index=True),
                              Column('timestamp', DateTime(timezone=True), default=get_timestamp,
                                     onupdate=get_timestamp),

                              schema=schema
                              )

    # extra meta information of article
    # do not process directly on this table
    # Better create your own tables and copy data in you business.
    DB_t_article_ex_meta = Table('article_ex_meta', meta,
                                 Column('id', Integer, primary_key=True, autoincrement=True),
                                 Column('aid', Integer, ForeignKey(DB_t_article.c.id, ondelete='CASCADE'), index=True),
                                 Column('key', String(20), index=True),
                                 Column('value', String(50)),

                                 UniqueConstraint('aid', 'key'),

                                 schema=schema
                                 )

    # article tags
    # Do not process directly on this table.
    # Better create tagmap and tags tables and copy data in you own business.
    DB_t_article_tag = Table('article_tag', meta,
                             Column('id', Integer, primary_key=True, autoincrement=True),
                             Column('aid', Integer, ForeignKey(DB_t_article.c.id, ondelete='CASCADE'), index=True),
                             Column('tag', String(20), index=True),

                             UniqueConstraint('aid', 'tag'),
                             schema=schema
                             )

    def __init__(self, conn_str='', schema=None):
        self.schema = schema
        self.__engine = None
        self.__conn = None
        self.__conn_str = conn_str

    @classmethod
    def get_inst(cls, conn_str='', schema=None):
        if not cls.__inst:
            cls.__inst = Database(conn_str=conn_str, schema=schema)
        return cls.__inst

    @staticmethod
    def __internal_settings():
        from scrapy.utils.project import get_project_settings
        return get_project_settings()

    @property
    def conn_str(self):
        if not self.__conn_str:
            settings = Database.__internal_settings()
            self.__conn_str = settings['DB_CONNECTION_STRING']
        return self.__conn_str

    @conn_str.setter
    def conn_str(self, value):
        self.__conn_str = value

    @property
    def engine(self):
        if not self.__engine:
            conn_str = self.conn_str
            if conn_str.startswith('sqlite'):
                self.__engine = create_engine(conn_str)
            else:
                self.__engine = create_engine(conn_str, pool_size=20, max_overflow=1)
        return self.__engine

    def exist_table(self, name):
        # return name in Database.meta.tables
        # sql = '''select tablename from pg_catalog.pg_tables where tablename='%s';''' % name
        # tname = self.engine.execute(sql).scalar()
        # return tname == name
        return self.engine.has_table(name, schema=self.schema)

    def create_connection(self, **kwargs):
        return self.engine.connect(**kwargs)

    @property
    def conn(self):
        if not self.__conn:
            self.__conn = self.create_connection()
        return self.__conn

    @property
    def status(self):
        return self.engine.url

    def execute(self, *args, **kwargs):
        return self.conn.execute(*args, **kwargs)

    def get_chapter_table_name_def_alone(self, chapter_table, site):
        table_alone = True if chapter_table else False
        if table_alone:
            tc = self.get_db_t_chapter(chapter_table)
        else:
            chapter_table = self.gen_site_chapter_table_name(site)
            tc = self.get_db_t_site_chapter(chapter_table)

        return chapter_table, tc, table_alone

    @staticmethod
    def get_db_t_site_chapter(name):
        """get the table definition of chapter for site (one table per site)"""
        table = Database.meta.tables.get(name, None)
        if table is None:
            table = def_db_t_site_chapter(name, Database.meta, Database.schema)
        return table

    @staticmethod
    def get_db_t_site_chapter_conflict(name):
        """get the table definition of chapter for site (one table per site)"""
        name = name + CONFLICT_SUFFIX
        table = Database.meta.tables.get(name, None)
        if table is None:
            table = def_db_t_site_chapter_conflict(name, Database.meta, Database.schema)
        return table

    @staticmethod
    def get_db_t_chapter(name):
        """get the table definition of chapter for article (one table per article)"""
        table = Database.meta.tables.get(name, None)
        if table is None:
            table = def_db_t_chapter(name, meta=Database.meta, schema=Database.schema)
        return table

    @staticmethod
    def get_db_t_chapter_conflict(name):
        """get conflict table definition of chapter for article (one table per article)"""
        # arg "name" is chapter table name.
        # conflict table will be name + CONFLICT_SUFFIX
        tname = name + CONFLICT_SUFFIX
        table = Database.meta.tables.get(tname, None)
        if table is None:
            table = def_db_t_chapter_conflict(tname, meta=Database.meta, schema=Database.schema)
        return table

    @staticmethod
    def gen_site_chapter_table_name(site):
        site = site.replace(DB_T_DOT_ESCAPE[0], DB_T_DOT_ESCAPE[1])
        return DB_T_NAME_SEP.join(['s', site])

    @staticmethod
    def gen_chapter_table_name(aid, site, name):
        site = site.replace(DB_T_DOT_ESCAPE[0], DB_T_DOT_ESCAPE[1])
        return DB_T_NAME_SEP.join(['a', str(aid), site, name])

    @staticmethod
    def split_chapter_table_name(chapter_table):
        assert chapter_table is not None
        x = chapter_table.split(DB_T_NAME_SEP)
        assert len(x) == 4
        aid = int(x[1])
        site = x[2].replace(DB_T_DOT_ESCAPE[1], DB_T_DOT_ESCAPE[0])
        name = x[3]
        return aid, site, name

    @staticmethod
    def split_site_chapter_table_name(chapter_table):
        assert chapter_table is not None
        x = chapter_table.split(DB_T_NAME_SEP)
        assert len(x) == 2
        site = x[1].replace(DB_T_DOT_ESCAPE[1], DB_T_DOT_ESCAPE[0])
        return site

    def lock_article(self, article_id, locker, name=None):
        rc = 0      # succeed (unlocked the article)
        tl = self.DB_t_article_lock
        stmt = tl.insert().values(aid=article_id, name=name, locker=locker, timestamp=datetime.now().replace(tzinfo=CST))
        conn = self.conn
        try:
            conn.execute(stmt)
            log.info('Locked article %s(id=%s).' % (name or '', article_id))
        except IntegrityError as err:
            try:
                stmt = select([tl.c.locker]).where(tl.c.aid == article_id)
                lckr = conn.execute(stmt).scalar()
                if lckr == locker:
                    rc = 1      # unlocked. the article was locked by self
                    log.debug('article %s(id=%s) is locked by self' % (name or '', article_id))
                else:
                    rc = -1     # fail to unlock. the article was locked by other
                    log.info('article %s(id=%s) was locked by other.' % (name or '', article_id))
            except Exception as err:
                log.error('Fail to lock article %s(id=%s). %s.' % (name or '', article_id, str(err)))

        return rc

    def unlock_article(self, article_id, locker):
        tl = self.DB_t_article_lock
        stmt = tl.delete().where(and_(tl.c.aid == article_id, tl.c.locker == locker))
        count = 0
        conn = self.conn
        try:
            rs = conn.execute(stmt)
            count = rs.rowcount
        except Exception as err:
            log.exception(err)

        if count == 0:
            log.info('article (id=%s) was not locked by %s so cannot unlock.' % (article_id, locker))
        elif count > 1:
            log.warning('Unlocked %s articles which has id=%s locker=%s' % (count, article_id, locker))
        else:
            log.info('Unlocked article (id=%s, locker=%s).' % (article_id, locker))

        return count

    def __del__(self):
        if self.__conn:
            self.__conn.close()
            self.__conn = None
