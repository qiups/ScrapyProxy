# -*- coding: utf-8 -*-

import sys
import os
import scrapy
import json
import time
import math
from proxy.log import logging


# 设置默认 encode 编码为 'utf-8'
reload(sys) # reload 才能调用 setdefaultencoding 方法
sys.setdefaultencoding('utf-8')


class TestProxySpider(scrapy.Spider):
    name = 'testproxy'
    allowed_domains = []
    # 在正常的爬取过程中可能会出现的状态码，配合代理中间件使用，
    # 若response.status不等于200且不在此列表中，将视为代理出错，会重发请求
    website_possible_httpstatus_list = []
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'proxy.middlewares.RandomUserAgentMiddleware.RandomUserAgentMiddleware': 1, # 动态设置User-Agent
            'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 80, # 下载超时
            #'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90, # 不retry了
            # put this middleware after RetryMiddleware
            'proxy.middlewares.ProxyMiddleware.ProxyMiddleware': 100 # 使用代理
        },
        'DOWNLOAD_TIMEOUT': 10, # 10-15秒是合理范围
        'LOG_LEVEL': 'INFO',
        #'RETRY_TIMES': 1,
        #'RETRY_HTTP_CODES': [500, 503, 504, 400, 403, 404, 408],
        'COOKIES_ENABLED': False, # 禁用cookies
        'DOWNLOAD_DELAY': 0.1 # 延迟下载
    }
    request_headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Connection': 'keep-alive'
    }

    test_count = 500
    total_page = 150
    def start_requests(self):
        for i in range(self.test_count):
            yield scrapy.Request(
                self.get_test_url( i % self.total_page + 1 ),
                callback = self.parse,
                #headers = self.request_headers,
                meta = {
                        'count': i
                    },
                dont_filter = True
                )

    scu_count = 0
    is_end = False
    def parse(self, response):
        flag = self.check_response_valid(response)
        if flag:
            self.scu_count += 1
        else:
            req = response.request
            req.meta['change_proxy'] = True
            yield req
        if response.meta['count'] == self.test_count - 1:
            self.is_end = True
        if not flag or (response.meta['count'] + 1) % 100 == 0 or self.is_end:
            self.logger.info('normal response(%s %s %s) proxy: %s' % (\
                response.meta['count'], flag, self.scu_count, response.meta['proxy'] if 'proxy' in response.meta.keys() else ''))

    def get_test_url(self, page):
        return 'http://hotels.ctrip.com/hotel/dianping/%s_p%dt0.html?_=%d' % (434128, page, math.floor(time.time() * 1000))

    def check_response_valid(self, response):
        try:
            # if response.xpath('//h2/@id="newsH2"'): # http://www.qq.com
            # ip = response.xpath('//body/center/text()').extract()[0].decode('utf8') # http://1212.ip138.com/ic.asp
            if response.xpath('//p/@class="J_commentDetail"').extract()[0] != '0':
                return True
            else:
                #with open('_error.html', 'w') as f:
                #    f.write(response.body)
                return False
        except BaseException:
            return False