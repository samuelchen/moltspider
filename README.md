# moltspider
MoltSpider is a broad spider to crawl all kinds of articles, books, novels, comis and so on.

## Background

* Why this project?

This project is based on another spider project to crawl internet novels for a specified website.
Later the website was dead. So I want to extend the spider to make it be able to crawl
all kinds of websites based on schema definitions.

* Why this name?

The spider likes to molt so that it can crawl on another web.


## Technology and component

This spider is built base on `python` and `scrapy`.
The crawled data is stored in database like `postgresql`
A simple reader `readnovel.py` is built on `flask` so that you can quick view crawled article.

## Definition

How spiders are defined, how web pages are crawled.

### Component

* Article

Base component to represent a (serials) of book, novel, art, comic, video and so on.

* META

Meta information of an `article` such as `authoer`, `date`, `category`, `description` 
and so on

* TOC

Table of content of the `article`. Such as chapters list of a book, episodes list
of a tv serials.

* Chapter

A chapter of a book, one epsidoe of a tv serial. Basically its has **link** and **text**
on `TOC`.

* Content

The real data of a `chapter` such as text, video data.

* Index

A list to show all `article`s such as books, comics and so on.

* Home

Where we can found all the `index` lists

### Web pages

I defined 4-5 levels web pages for a website.

* Home 

Home page of a website.
For example, `https://lifehacker.com/` is the home page of `LifeHacker`.

Sometimes, it's not the common meaning of a website home page.
It should be the catalog page of the website which list all index page.
But its `home` is not this.
For example, `https://www.msn.com/en-us` is home page of `MSN` English language.
But we can not grab index page from it. So we treat `https://www.msn.com/en-us/sports`
as the `home` of `msn-sports` website. "NFL NBA MLB NHL NCAA FB NCAA BK Golf Tennis" 
listed at top of the page will be link of `index` page of each kind of sport.

* index

### Spiders

* Home
* Index
* Meta
* TOC
* Chapter
