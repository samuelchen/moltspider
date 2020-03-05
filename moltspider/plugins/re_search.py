"""plugin to extract data by given pattern with re.search"""
import re


def perform(data, pattern, **kwargs):
    re_pattern = pattern
    if re_pattern:
        m = re.search(re_pattern, data)
        if m:
            data = m.group(0)
    return data
