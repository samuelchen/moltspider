import os
import sys
import json
from datetime import datetime
import logging
from moltspider.db import Database
from moltspider.parser import SiteSchemas, plugin_source
from sqlalchemy import select
from sqlalchemy.exc import ArgumentError

log = logging.getLogger(__name__)


class CopyDB(object):
    base_path = os.path.dirname(os.path.dirname(__file__))
    state_file_path = os.path.join(base_path, 'log', 'copy_db_state.json')

    def __init__(self, src_conn_str, target_conn_str):
        self.src_conn_str = src_conn_str
        self.target_conn_str = target_conn_str
        self.src_db = Database(conn_str=src_conn_str)
        self.target_db = Database(conn_str=target_conn_str)
        self.state = None

        log.info('Copying data from "%s" to "%s" ...' % (src_conn, target_conn))

        self._re_search = plugin_source.load_plugin('re_search')
        self._re_replace = plugin_source.load_plugin('re_replace')
        self._html2md = plugin_source.load_plugin('html2md')

    def _fix_author(self, author):
        val = author
        if not val:
            return val

        if self._re_search:
            val = self._re_search.perform(val, "([^&]*)")

        # print(author, '==>>', val)
        return val

    def _fix_desc(self, val):
        if not val:
            return val

        if self._html2md:
            if not val.startswith(self._html2md.MD_PREFIX):
                if self._re_replace:
                    val = self._re_replace.perform(val, "\\</?div.*?\\>", "")
                    val = self._re_replace.perform(val, "\\<p.*?\\>.*\\</p\\>", "")
                    val = self._re_replace.perform(val, "\\<a.*?\\>.*\\</a\\>", "")
                    val = self._re_replace.perform(val, "[\\r|\\n]", "")
                    val = self._re_replace.perform(val, "\\<br\\>", "\r\n")
        return val

    def _fix_content(self, val):
        if not val:
            return val

        if self._html2md:
            if not val.startswith(self._html2md.MD_PREFIX):
                if self._re_replace:
                    val = self._re_replace.perform(val, "\\</?div.*?\\>", "")
                    val = self._re_replace.perform(val, "\\<p.*?\\>.*\\</p\\>", "")
                    val = self._re_replace.perform(val, "\\<a.*?\\>.*\\</a\\>", "")
                    val = self._re_replace.perform(val, "[\\r|\\n]", "")
                    val = self._re_replace.perform(val, "\\<br\\>", "\r\n")
        return val

    def _copy_table(self, t):
        assert self.state is not None, 'Must load state before start coping.'

        limit = 1000
        if t.name not in self.state:
            self.state[t.name] = {'offset': 0}
            self.save_state()

        stat = self.state[t.name]
        offset = stat.get('offset', 0)
        done = stat.get('done', False)
        if done:
            log.info('Skip %s due to its done already (records:%d).' % (t.name, offset))
            return

        while True:
            stmt = select(t.c).offset(offset).limit(limit)
            rs = self.src_db.execute(stmt)

            records = []
            for r in rs:
                record = {c.name: r[c] for c in t.c}
                if 'author' in record:
                    record['author'] = self._fix_author(record['author'])
                if 'desc' in record:
                    record['desc'] = self._fix_desc(record['desc'])
                if 'content' in record:
                    record['content'] = self._fix_content(record['content'])
                records.append(record)

            if records:
                self.target_db.conn.execute(t.insert(), records)

            offset += len(records)
            stat['offset'] = offset
            self.save_state()

            if len(records) < limit:
                break

        stat['done'] = True
        self.save_state()

    def copy_major_tables(self):
        self.target_db.meta.bind = self.target_db.engine
        self.target_db.meta.create_all()
        for t in self.target_db.meta.tables.values():
            self._copy_table(t)

    def copy_site_chapter_tables(self):
        assert self.state is not None, 'Must load state before start coping.'
        stat_key = '_site_chapter_tables_'

        if stat_key not in self.state:
            self.state[stat_key] = {'offset': 0}
            self.save_state()

        stat = self.state[stat_key]
        offset = stat.get('offset', 0)
        done = stat.get('done', False)
        if done:
            log.info('Skip %s due to its done already (records:%d).' % (stat_key, offset))
            return

        sites = sorted(SiteSchemas.keys())
        i = 0
        for site in sites:
            if i < offset:
                i += 1
                continue

            tname = self.src_db.gen_site_chapter_table_name(site)
            t = self.src_db.get_db_t_site_chapter(tname)

            if self.src_db.exist_table(tname):
                if not self.target_db.exist_table(tname):
                    t.create(bind=self.target_db.conn)
                self._copy_table(t)

            offset += 1
            stat['offset'] = offset
            self.save_state()

        stat['done'] = True
        self.save_state()

    def copy_individual_chapter_tables(self):
        assert self.state is not None, 'Must load state before start coping.'

        ta = Database.DB_t_article
        chapter_tables_state_key = '_individual_chapter_tables_'
        if chapter_tables_state_key not in self.state:
            self.state[chapter_tables_state_key] = {'offset': 0}
            self.save_state()

        limit = 10
        stat = self.state[chapter_tables_state_key]
        offset = stat.get('offset', 0)
        done = stat.get('done', False)
        if done:
            log.info('Skip %s due to its done already (records:%d).' % (chapter_tables_state_key, offset))
            return

        self.src_db.meta.bind = self.target_db.engine

        while True:
            stmt = select([ta.c.id, ta.c.chapter_table]).where(ta.c.chapter_table != None)
            stmt = stmt.order_by(ta.c.id).offset(offset).limit(limit)
            rs = self.src_db.execute(stmt)
            count = 0
            for r in rs:
                tname = r[ta.c.chapter_table]
                t = self.src_db.get_db_t_chapter(tname)
                if self.src_db.exist_table(tname):
                    if not self.target_db.exist_table(tname):
                        t.create(bind=self.target_db.conn)
                    self._copy_table(t)

                count += 1
                offset += 1
                stat['offset'] = offset
                self.save_state()

            if count < limit:
                break

        stat['done'] = True
        self.save_state()

    def save_state(self):
        with open(self.state_file_path, 'wt', encoding='utf-8') as fp:
            json.dump(self.state, fp, indent=2, ensure_ascii=False)

    def read_state(self):
        try:
            with open(self.state_file_path, 'rt', encoding='utf-8') as fp:
                self.state = json.load(fp)
            log.info('State file found. Continue last copying.')
        except FileNotFoundError:
            log.info('No state file found. Start new copying.')
            self.state = {}
            self.save_state()

    def finish_state(self):
        suffix = datetime.now().strftime('%Y-%m-%d-%H-%M')

        fpath = os.path.split(self.state_file_path)
        fname = os.path.splitext(fpath[-1])
        fname = fname[0] + '-' + suffix + fname[-1]
        fpath = os.path.join(fpath[0], fname)

        self.save_state()
        try:
            os.rename(self.state_file_path, fpath)
        except FileNotFoundError:
            pass


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, format='%(message)s')

    src_conn = 'sqlite:///' + os.path.join(r'C:\data', 'article.sqlite3')
    target_conn = 'postgresql://article:123456@localhost/article'
    if len(sys.argv) <= 1:
        sys.stderr.writelines([
            'Please specify source and target connection string. For example:', '\r\n',
            '\t', src_conn, '\r\n',
            '\t', target_conn, '\r\n',
        ])
        exit(1)
    if len(sys.argv) > 1:
        src_conn = sys.argv[1]
    if len(sys.argv) > 2:
        target_conn = sys.argv[2]

    cpdb = CopyDB(src_conn_str=src_conn, target_conn_str=target_conn)
    cpdb.read_state()

    try:
        cpdb.copy_major_tables()
        cpdb.copy_site_chapter_tables()
        cpdb.copy_individual_chapter_tables()
        cpdb.finish_state()             # if exception, do not finish it.
        print("** DB copying finished. Do NOT run again. **")
    except ArgumentError as err:
        sys.stderr.write('ERROR: Connection string incorrect. %s\r\n' % err)

