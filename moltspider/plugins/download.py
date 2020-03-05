"""Download all find links from html tag's attribute.
    !! NOTE: This is a special process plugin. It will return a tuple of 2 values.
            e.g. `return data_value, dict_fields_value`
    1st value (`data value`): the real converted data. it will be passed to next process plugin or return to spider.
    2st value (`fields value`): a dict represents new fields (to extend in spider `item`).
                dict key is field name, dict value is field value.
                Normally, if we want to extract file links to download, we could make `fields value` likes:
                {
                    "file": ["http://abc.com/file1.zip", "https://cde.com/file2.jpg"]
                }
                Off cause we could generate other fields values. e.g.
                {
                    "foo": 1,
                    "bar": "sample"
                }
                it will be updated to current spider `item`.
"""

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
import logging
from moltspider.utils import gen_file_path
from moltspider.consts import SchemaOtherKey as SOK, Spiders

log = logging.getLogger(__name__)


# TODO: 1. 下载到 site/article 目录 (album 下载到 site/)
# TODO: 2. content 内 链接 改为 ${F:hash}. 下载文件替换
# TODO: 3. 写个 replace_content_downloaded_file_link 之类的 函数，不要每个都 replace
# TODO: 4. 用的时候，自动创建 statc/[album|meida]/site 各个 site 的软连接， 软连接用 hash(site)
# TODO: 5. 有没有办法找出 所有内容的链接 与 所有的文件 之间的并集，用于清理


def perform(data, tag, attr, **kwargs):
    """
    Find all `tag`s, and replace the attribute `attr` to new name.
    If `name_attr`'s value is available, use it as file name. Otherwise, new name is prefix + auto-number

    tag: html tag to search
    attr: attribute in tag node to find download url
    name_attr: attribute in tag node to find name
    path: sub path of FILES_STORE where files are stored in
    name_prefix_if_gen_name: if name is not found in `name_attr`, use prefix + auto-number as name.
    """

    item = kwargs.get('item')
    assert item is not None, 'plugin keyword argument "item" can not be None'
    assert isinstance(item, dict), 'plugin keyword argument "item" must be a dict'

    links = set()
    soup = BeautifulSoup(data, features='lxml')
    url_scheme = ''
    i = 0
    for node in soup.find_all(tag):
        link = node.get(attr)
        if not link:
            continue

        if not link.startswith('http'):
            link = urlparse(link)
            link = urlunparse((url_scheme or 'http', *link[1:]))
        else:
            if not url_scheme:
                url_scheme = urlparse(link).scheme

        fpath = gen_file_path(url=link)
        node[attr] = '${STATIC}/' + fpath
        links.add(link)
        i += 1

    # copy download links from other fields
    origin_links = item.get(SOK.FILE_DL.code)
    if origin_links:
        if not isinstance(origin_links, (list, tuple, set)):
            origin_links = [origin_links, ]
        for l in origin_links:
            links.add(l)

    item[SOK.FILE_DL.code] = links
    return soup.prettify()  #, {'file': links}

