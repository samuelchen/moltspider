# -*- coding: utf-8 -*-
import scrapy
import logging
from ..consts import Spiders

log = logging.getLogger(__name__)


class FileDownloadSpider(scrapy.Spider):
    """To download file"""
    name = Spiders.FILE
    allowed_domains = []
    start_urls = []

    def __init__(self, links):
        super().__init__()
        self.start_urls = links


