moltspider usage
===========

broad spider for all kinds of site

## Command line actions 

* crawl all `index` from `home`

`$ scrapy crawl index -a sites=a.com,b.com -a no_cache`

* crawl all `article` from an `index` list

`$ scrapy crawl list`

* crawl `meta` information of an `article`

`$ scrapy crawl meta`

* crawl `toc` from an `article`

`$ scrapy crawl toc`

* crawl `chapter` from `meta` of an `article`

`$ scrapy crawl chapter`

## Arguments for action commands

* argument `-a value1`

    * `nocache`: do not use cached web pages for current command.

* keyword argument `-a key=value1,value2`

    multi-values are separated by comma(`,`).
    
    * `s`: crawl in list `site` ids only. e.g `-a s=a.com,b.net,c.org`
        
        If no sites specified, will crawl **all** supported sites.
        
    * `i`: crawl in list `index` ids. e.g. `-a i=1,3`
        
        If not specified, will crawl **all** indexes in DB. 
    
    * `a`: crawl only specified `article` ids. e.g. `-a a=3,8,23`
        if not specified, will crawl all articles that match `article weight`
        
        * weight = LISTED: only listed in DB (meta, toc, chapter will no be crawled)
        * weight = META: only crawl meta (toc, chapter will not be crawled)
        * weight = TOC_PREVIEW: crawl n entries in TOC. (n == ARTICLE_PREVIEW_CHAPTER_COUNT)
        * weight = TOC: only crawl toc (chapter content will not be crawled)
        * weight = PREVIEW: crawl n chapters content. (n == ARTICLE_PREVIEW_CHAPTER_COUNT)
        * weight = NORMAL: crawl all chapter content
        * weight = CHOICE: editor choice. crawl first. Good articles.
        * weight = CLASSIC: classic articles. crawl first. 
        * weight = PREMIUM: premium articles. crawl first.
    
    * `cf`: chapter from id. `chapter` spider only. id must in downloaded TOC.
    * `ct`: chapter to id. `chapter` spider only. id must in downloaded TOC.
    * `p`: pages to crawl if there is `next` page. e.g. `-a p=2` means crawl only 2 pages.
    * `ac`: count of articles will be crawled.
    * `cc`: chapters of articles will be crawled.

    * remember last crawled. use `scrap states` 
    
        `scrapy crawl list -s JOBDIR=./path/to/state/list-1`
        
        `scrapy crawl meta -s JOBDIR=./path/to/state/novel-1`
        
        `scrapy crawl chapter -s JOBDIR=./path/to/state/novel-1`

## To simply read the articles (test purpose) 

* run `python reader.py 8080`
* browse http://localhost:8080
* if port is not specified, 8080 will be default.

## To debug in IDE

* add file `debug.py` with content
```python
from scrapy.cmdline import execute
import sys

execute(['scrapy', 'crawl', *sys.argv[1:]])
```
* In IDE, set start script as `debug.py`
  
