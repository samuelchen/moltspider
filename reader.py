#!/usr/bin/python
# -*- coding=utf-8 -*-

__author__ = 'samuel'

import os
import sys
from flask import Flask, request, render_template_string, make_response, url_for, redirect

from moltspider.db import Database
from moltspider.parser import load_site_schemas
from moltspider.consts import SiteSchemaKey as SSK, ArticleStatus, ArticleWeight
from moltspider.utils import str_md5
from sqlalchemy import select, and_, not_, func
import markdown
import logging

log = logging.getLogger(__name__)
# logging.basicConfig({'level': logging.DEBUG})

HASH_SITE_IN_URL = True

base_path = os.path.dirname(__file__)
static_base_symbol_link = os.path.join(base_path, 'temp' if HASH_SITE_IN_URL else '', 'static')
images_store_symbol_link = os.path.join(static_base_symbol_link, 'album')
files_store_symbol_link = os.path.join(static_base_symbol_link, 'media')


def site_for_url(site):
    return str_md5(site) if HASH_SITE_IN_URL else site


static_url_path = '/s'
album_url_path = static_url_path + '/' + os.path.split(images_store_symbol_link)[-1]
file_url_path = static_url_path + '/' + os.path.split(files_store_symbol_link)[-1]

app = Flask(__name__, static_folder=static_base_symbol_link, static_url_path=static_url_path)

MD_PREFIX = '<!--md-->'

# IS_PREVIEW = bool(os.environ.get('MOLTSPIDER_READER_PREVIEW', False))


# font_em = 0.9
album_w = 80
album_h = 100

template_page = '''
<html>
<head>
<meta charset="{{ encoding }}" />
<meta http-equiv="content-type" content="text/html; charset={{ encoding }}" />
<style type="text/css">

  body, pre, p, div, input, h1,h2,h3,h4,h5 {
    font-family : MS Yahei, Consolas, Courier New;
  }

  body, pre, p, div, li, input, select {
      font-size: 0.9em;
  }
  
  table {
    font-family: SongTi;
    font-size: 1em;
  }
  
  .nav {
    font-size: 1em;
  }

  .article {
    font-family: KaiTi;
    // font-size: 26px;
    border: 0px;
    background-color: #eee;
    width: 90%;
    // max-width: 960px;
    min-width: 320px;
    margin: auto;
  }
  
  .article p {
    font-family: KaiTi;
  }
  
  .article img {
    max-width: 90%;
  }
  
  .error {
    color: red;
  }

  .notice {
    color: blue;
  }
</style>
</head>
<body>
    <div id="wrapper">
        {{ content | safe }}
    </div>
</body>'''


@app.route('/', methods=['GET'])
def index():
    context = {
        "encoding": "utf-8"
    }
    db = Database()

    colspan = request.args.get('col', default=6, type=int)
    i = 0
    odd = False
    sb = []

    site_schemas = load_site_schemas()
    try:
        sb.append('<h3 align="center">文库 - moltspider</h3>')

        ti = db.DB_t_index

        # sites list
        stmt = select([ti.c.site, func.max(ti.c.update_on).label(ti.c.update_on.name), func.count(1).label('count')]
                      ).group_by(ti.c.site)
        rs = db.conn.execute(stmt)
        sb.append('<h4 align="center">支持的网站</h4>')
        sb.append('<ul style="list-style:none" align="left" width="95%" cellpadding="5">')
        for r in rs:
            site = r[ti.c.site]
            site_name = site_schemas.get(site, {}).get(SSK.NAME, site)
            sb.append('<li style="display:inline;"><a href="#%s">%s</a> (%s类)' % (site, site_name, r['count']))
            sb.append(' %s</li> | ' % r[ti.c.update_on.name].strftime("%x"))
        sb.append('</ul>')

        # indexes per site
        stmt = select([ti.c.id, ti.c.site, ti.c.text, ti.c.update_on]).order_by(ti.c.site, ti.c.id)
        rs = db.conn.execute(stmt)

        sb.append('<table align="center" width="90%" cellpadding="5">')
        site = ''
        site_name = ''
        line_style = ''
        for r in rs:

            if r[ti.c.site] != site:
                line_style = 'background-color:#eee' if odd else ''
                odd = not odd
                i = 0

                site = r[ti.c.site]
                site_name = site_schemas.get(site, {}).get(SSK.NAME, site)
                sb.append('<tr style="%s">' % line_style)
                sb.append('<td id="%s" colspan="%s" align="center"><h4>%s</h4></td></tr>' % (site, colspan, site_name))

            if i % colspan == 0:
                sb.append('<tr style="%s;">' % 'background-color:#eee' if odd else '')
                line_style = 'background-color:#eee' if odd else ''
                odd = not odd

            sb.append('<td><a href="/i/%(id)s">%(text)s</a></td>' % r)
            sb.append('</td>')

            i += 1
            if i % colspan == 0:
                sb.append('</tr>')

        sb.append('</table>')

        content = '\n'.join(sb)
    except Exception as err:
        content = '<h2>Error</h2><br><p class="error">' + str(err) + '</p>'
        log.exception(err)

    context['content'] = content
    resp = make_response(render_template_string(template_page, **context))
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


@app.route('/i/<int:iid>', methods=['GET', 'POST'])
def article_index(iid):
    is_preview = request.args.get('preview', default=False, type=bool)
    colspan = 6 if is_preview else 5
    colspan = request.args.get('col', default=colspan, type=int)
    if not 0 < colspan <= 8:
        colspan = 6 if is_preview else 5
    toc = request.args.get('toc', default=10, type=int)
    if not 0 < toc <= 30:
        toc = 10

    context = {
        "encoding": 'utf-8'
    }
    db = Database()

    updated_aid = handle_rate_form(request, db=db)

    try:
        ta = db.DB_t_article
        ti = db.DB_t_index
        stmt = select([ti.c.site + ' - ' + ti.c.text]).where(ti.c.id == iid)
        itext = db.conn.execute(stmt).scalar() or iid

        cellwidth = 100 / colspan
        i = 0
        odd = True
        sb = []

        sb.append('<h3 align="center">%s</h3>' % itext)
        sb.append('<p align="center"><a href="/">返回首页</a> <span>query: preview-预览, col-每列行数(1-8), toc-列章节数(1-30)<span></p>\n')
        sb.append('<table align="center" width="95%" cellpadding="5">')

        stmt = select([ta.c.id, ta.c.site, ta.c.name, ta.c.author, ta.c.category, ta.c.length, ta.c.status, ta.c.desc,
                       ta.c.cover, ta.c.recommends, ta.c.favorites, ta.c.recommends_month, ta.c.done, ta.c.update_on,
                       ta.c.chapter_table, ta.c.weight, ta.c.timestamp]
                      ).where(ta.c.iid == iid).order_by(ta.c.update_on.desc())
        rs = db.conn.execute(stmt)
        for r in rs:

            if is_preview:
                chapter_table, tc, table_alone = db.get_chapter_table_name_def_alone(r)

                if chapter_table and db.exist_table(chapter_table):
                    # get article toc
                    stmt = select([tc.c.id, tc.c.name, tc.c.is_section])  # .where(tc.c.content!=None)
                    if not table_alone:
                        stmt = stmt.where(tc.c.aid == r[ta.c.id])
                    stmt = stmt.order_by(tc.c.id).limit(toc)
                    rs1 = db.conn.execute(stmt)
                else:
                    rs1 = None

            if i % colspan == 0:
                sb.append('<tr style="%s;">' % 'background-color:#eee' if odd else '')
                odd = not odd

            if is_preview:
                pass
            else:
                sb.append('<td align="right"><img src="%s/%s/%s" width="%dpx" height="%dpx"></td>' % (
                    album_url_path, site_for_url(r[ta.c.site]), r[ta.c.cover] or '', album_w, album_h
                ))

            sb.append('<td id="a%s" width="%d%%">' % (r[ta.c.id], cellwidth))
            sb.append('<h4>%(id)s <a title="%(desc)s" href="/%(id)s/">%(name)s</a></h4>' % r)
            if is_preview:
                sb.append('<div style="word-wrap:break-word;">%s</div>' % (r[ta.c.desc] or ''))
                render_rate_form(sb, aweight=r[ta.c.weight], astatus=r[ta.c.status], aid=r[ta.c.id])
                if rs1:
                    for r1 in rs1:
                        sb.append('<li>%s</li>' % r1[tc.c.name])
                    rs1.close()
                    del rs1
            else:
                sb.append('<li>作者: <a href="/author/%(author)s/">%(author)s</a></li>' % r)
                sb.append('<li>类型: %(category)s</li><li>%(length)s 字</li><li>状态:%(status)s 完成:%(done)s</li>' % r)
                sb.append('<li>%s</li></td>' % r[ta.c.update_on].strftime('%x'))
            sb.append('</td>')
            i += 1
            if i % colspan == 0:
                sb.append('</tr>')

        if rs.rowcount == 0:
            sb.append('<tr style="background-color:#eee"><td> 还未上传 </td></tr>')

        sb.append('</table>')
        if updated_aid:
            sb.append('''
            <script>
                window.location = window.location.protocol + '//' + window.location.host + 
                    window.location.pathname + window.location.search + '#a%s';
            </script>
            ''' % updated_aid)

        content = '\n'.join(sb)
    except Exception as err:
        content = '<p class="error">' + str(err) + '</p>'
        log.exception(err)

    context['content'] = content
    resp = make_response(render_template_string(template_page, **context))
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


@app.route('/<int:aid>/', methods=['GET', 'POST'])
def article_page(aid):

    colspan = request.args.get('col', default=5, type=int)


    context = {
        "encoding": 'utf-8'
    }
    db = Database()
    ta = db.DB_t_article

    # POST
    handle_rate_form(request, aid, db)

    #  GET
    try:

        # get article information
        stmt = select([ta.c.id, ta.c.site, ta.c.iid, ta.c.name, ta.c.author, ta.c.category, ta.c.length, ta.c.status,
                       ta.c.desc, ta.c.recommends, ta.c.favorites, ta.c.recommends_month, ta.c.update_on, ta.c.weight,
                       ta.c.chapter_table, ta.c.timestamp]
                      ).where(ta.c.id == aid).order_by(ta.c.id)
        rs = db.conn.execute(stmt)
        ra = rs.fetchone()

        chapter_table, tc, table_alone = db.get_chapter_table_name_def_alone(ra)

        if chapter_table and db.exist_table(chapter_table):
            # get article toc
            stmt = select([tc.c.id, tc.c.name, tc.c.is_section])#.where(tc.c.content!=None)
            if not table_alone:
                stmt = stmt.where(tc.c.aid == aid)
            stmt = stmt.order_by(tc.c.id)
            rs = db.conn.execute(stmt)
        else:
            rs = None

        i = 0
        odd = True
        sb = []

        sb.append('<h3 align="center">%(name)s</h3>' % ra)
        sb.append('<p align="center"><a href="/i/%(iid)s">返回索引</a></p>\n' % ra)
        render_rate_form(sb, aweight=ra[ta.c.weight], astatus=ra[ta.c.status])
        sb.append('<table align="center" width="95%">')
        if rs:
            for r in rs:
                if i % colspan == 0:
                    sb.append('<tr style="%s">' % 'background-color:#eee' if odd else '')
                    odd = not odd
                if r['is_section']:
                    sb.append('</tr><tr style="background-color:silver"><td colspan="%s" align="center">%s</td></tr>' % (colspan, r['name'] or ''))
                    i = 0
                else:
                    sb.append('<td><a href="/%s/%s/">%s</a></td>' % (aid, r['id'], r['name'] or '阅读'))
                    i += 1
                if i % colspan == 0:
                    sb.append('</tr>')

        if rs is None or rs.rowcount == 0:
            sb.append('<tr style="background-color:#eee"><td> 还未上传 </td></tr>')

        sb.append('</table>')

        content = '\n'.join(sb)
    except Exception as err:
        content = '<h1>Error</h1><p class="error">' + str(err) + '</p>'

    context['content'] = content
    resp = make_response(render_template_string(template_page, **context))
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


@app.route('/<int:aid>/<int:cid>/', methods=['GET', 'POST'])
def chapter(aid, cid):
    context = {
        "encoding": 'utf-8'
    }
    db = Database()
    ta = db.DB_t_article

    handle_rate_form(request, aid, db)

    try:
        # load article information
        stmt = select([ta.c.site, ta.c.name, ta.c.weight, ta.c.status, ta.c.chapter_table]).where(ta.c.id == aid)
        ra = db.conn.execute(stmt).fetchone()
        aname = ra[ta.c.name]

        chapter_table, tc, table_alone = db.get_chapter_table_name_def_alone(ra)

        # load article chapter
        stmt = select([tc.c.id, tc.c.name, tc.c.content, tc.c.is_section]).where(tc.c.id == cid)
        if not table_alone:
            stmt = stmt.where(tc.c.aid == aid)
        stmt = stmt.order_by(tc.c.id)
        r = db.conn.execute(stmt).fetchone()

        stmt = select([tc.c.id]).where(and_(tc.c.id < cid, tc.c.is_section == False)).order_by(tc.c.id.desc()).limit(1)
        prev = db.conn.execute(stmt).scalar()

        stmt = select([tc.c.id]).where(and_(tc.c.id > cid, tc.c.is_section == False)).order_by(tc.c.id).limit(1)
        nxt = db.conn.execute(stmt).scalar()

        prev = '/%s/%s/' % (aid, prev) if prev else '#'
        nxt = '/%s/%s/' % (aid, nxt) if nxt else '#'
        # nav = '<div align="center"><a href="{1}">上一章</a>  <a href="/{0}">返回书页</a>  <a href="{2}">下一章</a></div>'.format(aid, prev, nxt)
        nav = '  <a href="/{0}">返回书页</a>  '.format(aid)
        if prev != '#':
            nav = '<div align="center"><a href="{0}">上一章</a>'.format(prev) + nav
        if nxt != '#':
            nav += '<a href="{0}">下一章</a></div>'.format(nxt)
        nav = '<div class="nav" align="center">%s</div>' % nav

        chapter_content = r[tc.c.content]
        if chapter_content:
            chapter_content = chapter_content.replace('${STATIC}', '%s/%s' % (
                file_url_path, site_for_url(ra[ta.c.site]) or '_all'))
            if chapter_content.startswith(MD_PREFIX):
                chapter_content = markdown.markdown(chapter_content)
            else:
                chapter_content = chapter_content.replace('\r\n', '<br>')
        else:
            chapter_content = '还未上传'

        sb = []
        sb.append('<h3 align="center">%s</h3>' % (r[tc.c.name] or aname))
        sb.append('<center><p>快捷键：左、右键 翻页，-、=(+)键 字体大小</p></center>')
        sb.append(nav)
        render_rate_form(sb, aweight=ra[ta.c.weight], astatus=ra[ta.c.status])
        sb.append('<div style="width:100%;background-color:#eee;">')
        sb.append('<hr />')
        sb.append('<div id="content" class="article" style="font-size:22px">%s</div>\n' % chapter_content)
        sb.append('<hr />')
        sb.append('</div>')
        sb.append(nav)
        sb.append('''
        <script language="javascript">
        document.onkeydown = key_pressed;
        var prev_page="{0}";
        var next_page="{1}";
        var size = document.cookie ? document.cookie.split('=')[1] : document.all["content"].style['font-size'];
        size = parseInt(size);
        document.all["content"].style['font-size'] = size + 'px'; 
        function key_pressed(event) {{
          if (event.keyCode==37) location=prev_page;
          if (event.keyCode==39) location=next_page;

          if (event.keyCode==189 || event.keyCode == 109) {{
            // size = parseInt(document.all["content"].style['font-size']);
            size -= 2;
            if (size <= 8) size = 8;
          }}
          if (event.keyCode==187 || event.keyCode == 107) {{
            // size = parseInt(document.all["content"].style['font-size']);;
            size += 2;
            if (size >= 48) size = 68;
          }}
          if (event.keyCode==48) {{
            size = 22;
          }}
          document.all["content"].style['font-size'] = size + 'px';
          document.cookie = "size=" + size + "; path=/";
        }}

        </script>
        '''.format(prev, nxt))

        content = '\n'.join(sb)
    except Exception as err:
        log.exception(err)
        content = '<h1>Error</h1><p class="error">' + str(err) + '</p>'

    context['content'] = content
    resp = make_response(render_template_string(template_page, **context))
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


@app.route('/rate/<int:aid>/', methods=['POST'])
def rate_article(aid):
    db = Database()
    ta = db.DB_t_article

    # POST
    handle_rate_form(request, aid, db)

    return None


def render_rate_form(string_builder_list, aweight, astatus, aid=''):
    sb = string_builder_list
    # rate it.
    sb.append('<center><form id="rate%s" method="post">' % aid)
    if aid:
        sb.append('<input type="hidden" name="aid" value="%s">' % aid)
    sb.append('<select name="aweight" style="width:100px" onchange="form.submit()">')
    for o in ArticleWeight.all:
        sb.append('<option value={0} {2}>{0} - {1}</option>'.format(
            o.code, o.get_text(), 'selected' if o == aweight else ''))
    sb.append('</select>')
    sb.append('<select name="astatus" style="width:100px" onchange="form.submit()">')
    for o in ArticleStatus.all:
        sb.append('<option value={0} {2}>{0} - {1}</option>'.format(
            o.code, o.get_text(), 'selected' if o == astatus else ''))
    sb.append('</select>')
    sb.append('</form></center>')


def handle_rate_form(request, aid='', db=None):
    if db is None:
        db = Database.get_inst()

    ta = Database.DB_t_article
    if request.method == 'POST':
        fields = {}

        if not aid:
            aid = request.form.get('aid')
            if not aid:
                raise Exception('aid not provided.')

        aweight = request.form.get('aweight')
        if aweight:
            fields[ta.c.weight.name] = int(aweight)
        astatus = request.form.get('astatus')
        if astatus:
            fields[ta.c.status.name] = int(astatus)

        if fields:
            stmt = ta.update().values(**fields).where(ta.c.id == aid)
            db.execute(stmt)

        return aid


if __name__ == "__main__":

    try:
        port = sys.argv[1]
        port = port.split(':')
        host = port[0]
        port = int(port[1])
        if port <= 0 or port > 65535:
            port = 8080
    except:
        host = '127.0.0.1'
        port = 8080
    app.run(host=host, port=port, debug=True)
