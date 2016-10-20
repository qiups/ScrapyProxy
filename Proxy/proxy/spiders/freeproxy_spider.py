# -*- coding: utf-8 -*-

import sys
import os
import scrapy
import json 
from proxy.log import logging
from proxy.items.ProxyItem import ProxyItem


# 设置默认 encode 编码为 'utf-8'
reload(sys) # reload 才能调用 setdefaultencoding 方法
sys.setdefaultencoding('utf-8')


class FreeProxySpider(scrapy.Spider):
    name = 'freeproxy'
    allowed_domains = []
    custom_settings = {
        'ITEM_PIPELINES': {
            'proxy.pipelines.proxy_pipeline.ProxyPipeline': 100
        },
        'DOWNLOAD_TIMEOUT': 10,
        'LOG_LEVEL': 'INFO'
    }
    request_headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.108 Safari/537.36',
        'X-Requested-With':'XMLHttpRequest'
    }

    def start_requests(self):
        requests = []
        requests += self.request_xicidaili()
        requests += self.request_kxdaili()
        requests += self.request_mimvp()
        requests += self.request_ip181()
        requests += self.request_httpdaili()
        requests += self.request_66ip()
        for req in requests:
            yield req


    def request_kxdaili(self):
        '''
        爬取www.kxdaili.com大陆高匿代理，共有10页
        '''
        url_tpl = 'http://www.kxdaili.com/dailiip/1/%d.html'
        requests = []
        for page in range(1, 11):
            url = url_tpl % page
            requests.append(scrapy.Request(url, callback = self.parse_kxdaili, headers = self.request_headers))
        return requests

    def parse_kxdaili(self, response):
        self.logger.info('##### response url: %s' % response.url)
        for tr in response.xpath('//table[@class="ui table segment"]/tbody/tr'):
            response_time = tr.xpath('td[5]/text()').extract()[0][:-2]
            if float(response_time) < 1:
                proxyitem = ProxyItem()
                proxyitem['ip'] = tr.xpath('td[1]/text()').extract()[0]
                proxyitem['port'] = tr.xpath('td[2]/text()').extract()[0]
                yield proxyitem
    

    def request_mimvp(self):
        '''
        爬取proxy.mimvp.com Http国内高匿，有多页，游客只能看到第一页的ip
        端口列是以图片形式展示
        '''
        url = 'http://proxy.mimvp.com/free.php?proxy=in_hp'
        requests = []
        requests.append(scrapy.Request(url, callback = self.parse_mimvp, headers = self.request_headers))
        return requests

    def parse_mimvp(self, response):
        self.logger.info('##### response url: %s' % response.url)
        for tr in response.xpath('//div[@id="list"]/table/tbody/tr'):
            response_time = tr.xpath('td[8]/@title').extract()[0][:-1]
            transport_time = tr.xpath('td[9]/@title').extract()[0][:-1]
            if float(response_time) < 1:
                # 端口号这列实际内容为一张图片，先不解析
                port_img_src = 'http://proxy.mimvp.com/' + tr.xpath('td[3]/img/@src').extract()[0]

                proxyitem = ProxyItem()
                proxyitem['ip'] = tr.xpath('td[2]/text()').extract()[0]
                #yield proxyitem


    def request_xicidaili(self):
        '''
        爬取www.xicidaili.com国内高匿代理，有多页，每页100个代理（有效的基本在第一页）
        '''
        url_tpl = 'http://www.xicidaili.com/nn/%d'
        requests = []
        requests.append(scrapy.Request(url_tpl % 1, callback = self.parse_xicidaili, headers = self.request_headers))
        return requests

    def parse_xicidaili(self, response):
        self.logger.info('##### response url: %s' % response.url)
        for tr in response.xpath('//table[@id="ip_list"]//tr[@class="odd" or @class=""]'):
            speed = tr.xpath('td[7]/div/@title').extract()[0][:-1]
            latency = tr.xpath('td[7]/div/@title').extract()[0][:-1]
            if float(speed) < 3 and float(latency) < 1:
                proxyitem = ProxyItem()
                proxyitem['ip'] = tr.xpath('td[2]/text()').extract()[0]
                proxyitem['port'] = tr.xpath('td[3]/text()').extract()[0]
                yield proxyitem


    def request_ip181(self):
        '''
        爬取www.ip181.com 每页100个各类型代理
        '''
        url_tpl = 'http://ip181.com/daili/%d.html'
        requests = []
        for page in range(1, 11):
            url = url_tpl % page
            requests.append(scrapy.Request(url, callback = self.parse_ip181, headers = self.request_headers))
        return requests

    def parse_ip181(self, response):
        self.logger.info('##### response url: %s' % response.url)
        trs = response.xpath('//table/tbody/tr')
        for i in range(1, len(trs)):
            tr = trs[i]
            proxy_type = tr.xpath('td[3]/text()').extract()[0]
            response_time = tr.xpath('td[5]/text()').extract()[0][:-2]
            if proxy_type == u'高匿' and float(response_time) < 1:
                proxyitem = ProxyItem()
                proxyitem['ip'] = tr.xpath('td[1]/text()').extract()[0]
                proxyitem['port'] = tr.xpath('td[2]/text()').extract()[0]
                yield proxyitem

    
    def request_httpdaili(self):
        '''
        爬取http://www.httpdaili.com/mfdl国内http代理，只有10个免费
        '''
        url = 'http://www.httpdaili.com/mfdl'
        requests = []
        requests.append(scrapy.Request(url, callback = self.parse_httpdaili, headers = self.request_headers))
        return requests

    def parse_httpdaili(self, response):
        self.logger.info('##### response url: %s' % response.url)
        trs = response.xpath('(//div[@class="kb-item-wrap11"])[1]/table/tr')
        for i in range(1, len(trs)):
            if i == 6:
                continue
            tr = trs[i]
            proxy_type = tr.xpath('td[3]/text()').extract()[0]
            if proxy_type == u'匿名':
                proxyitem = ProxyItem()
                proxyitem['ip'] = tr.xpath('td[1]/text()').extract()[0]
                proxyitem['port'] = tr.xpath('td[2]/text()').extract()[0]
                yield proxyitem


    def request_66ip(self):
        '''
        爬取http://www.66ip.com代理，不稳定
        getnum 数量
        isp 运营商（0全部，1电信，2联通，3移动，4铁通）
        anonymoustype 匿名性（0不限，1透明，2普匿，3高匿，4超匿）
        start 指定ip段
        ports 指定端口
        export 排除端口
        ipaddress 指定地区
        area 过滤条件（0国内外，1国内，2国外）
        proxytype 代理类型（0 http，1 https，2全部）
        '''
        url = 'http://www.66ip.cn/nmtq.php?getnum=50&isp=0&anonymoustype=3&start=&ports=&export=&ipaddress=&area=1&proxytype=0&api=66ip'
        requests = []
        requests.append(scrapy.Request(url, callback = self.parse_66ip, headers = self.request_headers))
        return requests

    def parse_66ip(self, response):
        self.logger.info('##### response url: %s' % response.url)
        rows = response.body.split('</script>')[-2].split('<br/>')
        for i in range(len(rows) - 1):
            proxy = rows[i].strip()
            if proxy:
                proxyitem = ProxyItem()
                proxyitem['ip'] = proxy.split(':')[0]
                proxyitem['port'] = proxy.split(':')[1]
                yield proxyitem