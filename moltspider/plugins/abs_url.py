"""plugin to make relative url path to absolute url path"""

from urllib.parse import urljoin


def perform(data, **kwargs):
    resp = kwargs.get('response')
    d = urljoin(resp.url, data)
    return d
