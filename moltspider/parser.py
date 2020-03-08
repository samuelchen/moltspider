import logging
import os
import json
from optenum import Option
from .consts import Schemas, SiteSchemaKey as SSK, Args, SchemaOtherKey as SOK, ArticleWeight
from urllib.parse import urlparse, urljoin
from collections import OrderedDict
from scrapy.utils.project import get_project_settings
from pluginbase import PluginBase

settings = get_project_settings()
plugin_base = PluginBase(package='moltspider.plugins')
plugin_source = plugin_base.make_plugin_source(
    searchpath=[os.path.join(os.path.dirname(__file__), 'plugins'),
                *settings.get('PROCESS_PLUGINS_SEARCH_PATH', [])
                ]
)

log = logging.getLogger(__file__)


def load_site_schemas():

    search_path = [
        os.path.join(os.path.dirname(__file__), 'sites'),
        *settings.get('SUPPORTED_SITES_SEARCH_PATH', [])
    ]

    schemas = {}

    for path in search_path:
        for top, dirs, files in os.walk(path, followlinks=True):
            for fname in files:
                if fname.endswith('.json'):
                    path = os.path.join(top, fname)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            schema = json.load(f, object_pairs_hook=OrderedDict)
                            k = fname[:-5]
                            schemas[k] = schema
                        log.debug('Loaded site schema %s' % path)
                    except IOError as e:
                        log.exception("Fail to read %s" % path)
                else:
                    log.debug('Ignore site schema %s in %s' % (fname, top))

    return schemas


SiteSchemas = load_site_schemas()


def arg_get_site_ids(**kwargs):
    """obtain site ids from keyword arguments"""
    if Args.SITES.code in kwargs:
        sites = kwargs.get(Args.SITES.code)
        sites = sites.split(Args.SEP.code)
    else:
        sites = []

    site_ids = []
    for s in sites:
        s = s.strip()
        if s in SiteSchemas:
            if s not in site_ids:
                site_ids.append(s)
            else:
                log.info('Argument "%s" duplicated' % s)
        else:
            log.warning('"%s" is not a supported site.' % s)

    if site_ids:
        log.warning('Sites are limited in: %s' % site_ids)

    return site_ids


def args_get_article_ids(**kwargs):
    """obtain article ids from keyword arguments"""
    if Args.ARTICLES.code in kwargs:
        articles = kwargs.get(Args.ARTICLES.code)
        articles = articles.split(Args.SEP.code)
    else:
        articles = []

    if articles:
        log.warning('Articles are limited in: %s' % articles)

    return articles


def args_get_index_ids(**kwargs):
    """obtain article ids from keyword arguments"""
    if Args.INDEXES.code in kwargs:
        indexes = kwargs.get(Args.INDEXES.code)
        indexes = indexes.split(Args.SEP.code)
    else:
        indexes = []

    if indexes:
        log.warning('Indexes are limited in: %s' % indexes)

    return indexes


def args_get_chapter_from_to(**kwargs):
    """obtain chapter from (id) to (id) to be crawled"""
    cf = kwargs.get(Args.CHAPTER_FROM_ID.code)
    ct = kwargs.get(Args.CHAPTER_TO_ID.code)

    if cf:
        cf = int(cf)
        log.warning('Limit chapters from %s' % cf)
    if ct:
        ct = int(ct)
        log.warning('Limit chapters to %s' % ct)

    return cf, ct


def args_get_count(**kwargs):
    """obtain counts (pages, articles, chapters ..) from keyword arguments"""
    pages = int(kwargs.get(Args.PAGES.code, 0))
    if pages > 0:
        log.warning('Limit to %s pages' % pages)

    acount = int(kwargs.get(Args.ARTICLE_COUNT.code, 0))
    if acount > 0:
        log.warning('Limit to %s articles' % acount)

    ccount = int(kwargs.get(Args.CHAPTER_COUNT.code, 0))
    if acount > 0:
        log.warning('Limit to %s chapters' % ccount)

    return pages, acount, ccount


def args_get_nocache(*args, **kwargs):

    nocache = Args.NOCACHE.code in args
    if nocache:
        log.warning('Disable cache in this crawl.')
    return nocache


def iter_items(spider, response, site_ids, schema_name):
    """
    populate items defined in schema
    fields must follow DB schema
    Add additional 'site'  field to identify which site (SchemaOtherKey.SITE.code)
    """

    assert schema_name in Schemas
    if isinstance(schema_name, Option):
        schema_name = schema_name.code

    resp_path = url_to_relative(response.url)
    site_schemas = SiteSchemas
    if not site_ids:
        site_ids = SiteSchemas.keys()

    for site in site_ids:
        schema_s = site_schemas[site]
        schema_items = schema_s.get(schema_name, {}).get(SSK.ITEMS.code, {})
        if not schema_items:
            log.warning('[%s] schema "%s" has no "%s" defined.' % (site, schema_name, SSK.ITEMS))
            continue

        encoding = schema_s.get(SSK.ENCODING.code)
        if encoding:
            response = response.replace(encoding=encoding)

        i = 0
        for schema in schema_items:
            i += 1
            fields_is_list = True
            action = schema.get(SSK.ACTION.code)

            # handle item selector. see whether list or single
            # if no item level selector specified, it's not list.
            item_selector, item_selector_is_css = get_selector(schema)
            if item_selector is None:
                # no item selector specified. so it's not list. use field selectors directly
                fields_is_list = False

            if fields_is_list:
                # get item list by given item selector
                nodes = response.css(item_selector) if item_selector_is_css else response.xpath(item_selector)
            else:
                nodes = [response, ]

            if not nodes:
                log.error('[%s][%s][schema:%s] has no node captured on %s.' % (site, schema_name, i, resp_path))
                continue

            log.debug('[%s][%s][schema:%s] Populating %s, %s=%s' % (
                site, schema_name, i, resp_path, SSK.ACTION.code, action))

            # populate fields from item nodes
            j = 0
            for node in nodes:
                j += 1
                item = {
                    SOK.SITE.code: site,  # add addition field to identify site
                }
                if action:
                    item[SSK.ACTION.code] = action

                # loop all fields schema in this item
                field_schemas = schema.get(SSK.FIELDS.code, {})
                is_field_schemas_specified = False  # assume field schemas are specified at least one.
                for name, schema_f in field_schemas.items():
                    if name.startswith(SSK.COMMENT.code):
                        continue

                    if not schema_f:
                        log.warning('[%s][%s][schema:%s] has no schema specified.' % (site, schema_name, i))
                        continue

                    # field has "value", directly set.
                    val = schema_f.get(SSK.VALUE.code)
                    if val is not None:
                        is_field_schemas_specified = True
                        item[name] = val
                        log.debug('[%s][%s][schema:%s] field "%s" has %s specified. Ignore selector.' % (
                            site, schema_name, i, name, SSK.VALUE))
                        continue

                    field_selector, field_selector_is_css = get_selector(schema_f)
                    if field_selector is None:
                        log.warning('[%s][%s][schema:%s] field "%s" has no selector specified.' % (
                            site, schema_name, i, name))
                        continue

                    is_field_schemas_specified = True
                    field = node.css(field_selector) if field_selector_is_css else node.xpath(field_selector)
                    if field:
                        if name.startswith(SSK.TAG_PREFIX.code):
                            # tags probably are list
                            data = field.getall()
                        else:
                            data = field.get().strip()
                        # process to call plugin
                        data = process_field_with_plugin(data, schema_f, site, schema_name, i,
                                                         spider=spider, item=item, response=response)
                        item[name] = data
                    else:
                        log.info('[%s][%s][schema:%s] field "%s" has no data captured for record #%s on %s.' % (
                            site, schema_name, i, name, j, resp_path))

                if not is_field_schemas_specified:
                    # no field schemas found
                    log.error('[%s][%s][schema:%s] has no fields schema specified.' % (site, schema_name, i))
                    break

                yield item


def get_selector(schema):
    selector_is_css = False
    selector = schema.get(SSK.XPATH.code, {})
    if not selector:
        selector_is_css = True
        selector = schema.get(SSK.CSS.code, {})
        if not selector:
            selector = None
    return selector, selector_is_css


def url_to_relative(url):
    u = urlparse(url)
    return urljoin(u.path, u.query)


def process_field_with_plugin(data, schema_field, site, schema_name, schema_item_num,
                              spider=None, item={}, response=None):
    """process data by given plugins in order.
        Plugins are defined in field schema `processor`.
        e.g.
        ```
            "processor": {
                "plugin1": ["arg1", "arg2", ...]
                "plugin2": [...]
            }
        ```
    """
    processors = schema_field.get(SSK.PROCESS, {})
    d = data
    for args in processors:
        assert isinstance(args, list), 'process item must be list'
        if len(args) < 1:
            log.warning('[%s][%s] Item #%s process is empty.' % (site, schema_name, schema_item_num))
            continue

        name = args[0]
        if name == SSK.COMMENT.code:
            log.debug('[%s][%s] Ignore plugin comment %s' % (site, schema_name, args))
            continue

        try:
            plugin = plugin_source.load_plugin(name)
            d = plugin.perform(d, *args[1:], site=site, spider=spider, item=item, response=response)
            if isinstance(d, (list, tuple)):
                extra_fields = d[1]
                d = d[0]
                item.update(extra_fields)
        except ModuleNotFoundError:
            log.error('[%s][%s] Item #%s process plugin "%s" not found.' % (site, schema_name, schema_item_num, name))
        except Exception:
            log.exception('[%s][%s] Error item #%s process plugin "%s" on "%s"' % (
                site, schema_name, schema_item_num, name, item))
            raise
    return d

