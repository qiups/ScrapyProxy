# -*- coding: utf-8 -*-
''' util tools 公用方法 '''

import urllib2
import sys

def check_proxy(proxy, timeout=3):
    url = 'http://ip.chinaz.com/getip.aspx'
    proxy_handler = urllib2.ProxyHandler({'http': 'http://%s:%s' % (proxy['ip'], proxy['port'])})
    opener = urllib2.build_opener(proxy_handler, urllib2.HTTPHandler)
    try:
        response = opener.open(url, timeout=timeout)
        print response.read().decode('utf8')
        return response.code == 200
    except Exception:
        return False