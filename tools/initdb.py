"""init database
    arg: "drop" to drop all database
"""
import sys
from moltspider.db import Database

if __name__ == '__main__':

    db = Database()
    db.meta.bind = db.engine

    if len(sys.argv) > 1 and sys.argv[1] == 'drop':
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
    else:
        db.meta.create_all()
