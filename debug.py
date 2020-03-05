from scrapy.cmdline import execute
import sys
# import os
import logging
import json

# with open('log_config.json') as f:
#     conf = json.load(f)
#     logging.config.dictConfig(conf)

# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# name = sys.argv[1]
execute(['scrapy', 'crawl', *sys.argv[1:]])
