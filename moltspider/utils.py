import os
import hashlib
import mimetypes


def str_md5(s):
    assert s is not None
    assert isinstance(s, str)
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def gen_file_path(url):
    """generate file path from url, site, aid(article id) and cid (chapter id).
        if `name` specified, use it. otherwise, file name will be `url` **hash string**.
        if `site` not presents, use `_all` for level 1 folder name.
        if `aid` not presents, will use '_' + first 2 characters as level 2 folder names, 3-4 chars as lvl 3 folder.

        e.g.
        if all arguments presented, path will be `site/aid/cid-name.ext`
        if not presents, path will be `_all/_3c/21/name.ext`

    """
    ext = guess_file_ext(url) or ''
    name = str_md5(url)

    return '%s/%s/%s%s' % (name[0:2], name[2:4], name, ext)


def gen_hash_file_path(url):
    """ similar to gen_file_path. but do not use site, aid, name as folder/name.
        directly use url hash as name and folders.
    """
    ext = guess_file_ext(url)
    url_hash = str_md5(url)

    return '%s/%s/%s%s' % (url_hash[0:2], url_hash[2:4], url_hash, ext)


def guess_file_ext(url):
    """guess file extension from given url"""
    media_ext = os.path.splitext(url)[1]
    # Handles empty and wild extensions by trying to guess the
    # mime type then extension or default to empty string otherwise
    if media_ext not in mimetypes.types_map:
        media_ext = ''
        media_type = mimetypes.guess_type(url)[0]
        if media_type:
            media_ext = mimetypes.guess_extension(media_type)
    return media_ext

