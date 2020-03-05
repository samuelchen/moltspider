"""plugin to convert html data markdown text
doc: https://github.com/Alir3z4/html2text/blob/master/docs/usage.md"""

import html2text

MD_PREFIX = '<!--md-->'


def perform(data, add_prefix=True, **kwargs):
    h = html2text.HTML2Text()
    h.single_line_break = True
    h.images_as_html = True
    h.images_with_size = True
    h.protect_links = True
    h.inline_links = False

    if add_prefix:
        d = MD_PREFIX + '\r\n'
    else:
        d = ''
    d += h.handle(data)
    return d
