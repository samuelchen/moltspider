""" database tool
    arg: command (lowercase)
        * "init" to initialize database
        * "drop" to drop all database
        * "reset" to reset cursor

"""
import sys
from moltspider.db import Database, select, and_, not_
from moltspider.settings.base import SPIDER_ID


def usage():
    print("""
    usage: %s %s command
    arg: command
        * "init" to initialize database 
        * "drop" to drop all database
        * "reset" to reset cursor
    
    """ % (sys.executable, sys.argv[0]))


def init(db):
    db.meta.create_all()


def drop(db):
    print("*" * 40)
    print('* DANGER!  DANGER!  DANGER !')
    print("* You are deleting ALL your database !!!")
    print('* All your data will be deleted and can NOT be recovered !!!')
    print("*" * 40)

    x = input('DANGER: Sure to delete all database !!! (y/n)')
    if x in ['y', 'Y']:
        db.meta.drop_all()
        print('Your database is dropped.')
    else:
        print('Cancelled.')


def reset(db):

    ta = db.DB_t_article
    tl = db.DB_t_article_lock
    spider_id = SPIDER_ID
    article_ids = []
    site_ids = []
    weight = 35
    LIMIT_ARTICLES = 10

    # locked article ids by other spider
    stmt_lock = select([tl.c.aid]).where(tl.c.locker != spider_id)
    # articles to be downloaded. Conditions:
    #   * weight >= TOC
    #   * not locked by other spider
    #   * status <= PROGRESS
    stmt = select([ta.c.id, ta.c.site, ta.c.url, ta.c.name, ta.c.weight, ta.c.status,
                   ta.c.url_toc, ta.c.chapter_table, ta.c.update_on])
    if article_ids:
        stmt = stmt.where(ta.c.id.in_(article_ids))
    elif site_ids:
        stmt = stmt.where(ta.c.site.in_(site_ids))
    stmt = stmt.where(and_(ta.c.weight >= weight, not_(ta.c.id.in_(stmt_lock))))
    stmt = stmt.order_by(ta.c.weight.desc(), ta.c.recommends.desc(), ta.c.id)
    if LIMIT_ARTICLES > 0:
        stmt = stmt.limit(LIMIT_ARTICLES)
        print('Limit %s articles. Others wll be ignored.' % LIMIT_ARTICLES)

    rs = db.conn.execute(stmt)

    # loop unlock articles
    for r in rs:
        print(r[ta.c.id], r[ta.c.name])
    rs.close()


if __name__ == '__main__':

    db = Database()
    db.meta.bind = db.engine

    if len(sys.argv) < 2:
        usage()
        exit(-1)

    command = sys.argv[1]
    if command == 'init':
        init(db)
    elif command == 'drop':
        drop(db)
    else:
        usage()
        exit(-1)

    exit(0)
