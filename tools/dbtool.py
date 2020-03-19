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
