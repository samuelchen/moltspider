"""plugin to extract data by given pattern with re.replace"""
import re


def perform(data, pattern, replacement, **kwargs):
    re_pattern = pattern
    if re_pattern:
        data = re.sub(re_pattern, replacement, data, flags=re.MULTILINE|re.UNICODE|re.IGNORECASE)
    return data


if __name__ == '__main__':
    s = """
<div id="content">    测试文字，测试文字测试文字测试文字；测试文字,测试文字.测试文字 328497uy932843275 。
<br>
<br>    测试文字测试文字测试文字，测试文字测试文字测试文字，测试文字测试文字，
<br>
<br>    “测试文字，测试文字测试文字。”
<br>
<br>    “测试文字， 测试文字。”测试文字。<br><br><p><a href="http://test.test.com/s/xbiquge.la" target="_blank">测试广告广告,测试广告广告，测试广告广告!</a><br>测试广告广告：http://m.xbiquge.la，测试广告广告  测试广告广告！</p></div>    
    """

    s = perform(s, r'\</?div.*?\>', '')
    s = perform(s, r'\<p.*?\>.*\</p\>', '')
    s = perform(s, r'\r|\n', '')
    s = perform(s, r'\<br\>', '\r\n')
    print(s)

    s = ' - 试文字测试文'
    s = perform(s, r'\s*-\s*', '')
    print(s)
