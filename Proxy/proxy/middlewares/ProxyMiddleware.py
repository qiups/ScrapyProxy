# -*- coding: utf-8 -*-

#import base64
import os
import json
from proxy.log import logging
from scrapy import signals
from twisted.web._newclient import ResponseNeverReceived
from twisted.internet.error import TimeoutError, ConnectionRefusedError, ConnectError


class ProxyMiddleware(object):
    # 遇到这些类型的错误直接当做代理不可用处理掉, 不再传给retrymiddleware
    DONT_RETRY_ERRORS = (TimeoutError, ConnectionRefusedError, ResponseNeverReceived, ConnectError, ValueError)

    def __init__(self, crawler):
        self.logger = logging.getLogger('ProxyMiddleware')
        # 记录免费代理的文件
        self.proxy_file = 'freeproxy.json'
        # 记录上次爬虫过后可用代理使用情况
        self.valid_proxy_file = 'validproxy.json'
        # 当前使用的代理列表，默认有不使用代理一项，以及其他认为一定可信的代理
        self.proxy_list = [{'proxy': None, 'use_count': 0, 'fail_count': 0, 'valid': True}]
        # 可信代理的数量，包含不用代理
        self.fixed_proxy_count = len(self.proxy_list)
        # 当前使用的代理下标
        self.proxy_index = 0
        # 是否平均使用每个valid的proxy
        self.use_proxy_averagely = True
        # 当代理的use_count小于此值时不判断其valid值
        self.use_count_to_check_valid = 10
        # fail_count/use_count大于此值时将置valid为False
        self.invalid_rate = 0.2

        self.is_test_valid = crawler.spider.name == 'testproxy'
        # connect the extension object to signals
        crawler.signals.connect(self.spider_closed, signal=signals.spider_closed)

        # 使用上次爬虫过后保留的可用代理
        if os.path.exists(self.valid_proxy_file):
            with open(self.valid_proxy_file, 'r') as fr:
                try:
                    proxies = json.load(fr)
                    for proxy in proxies:
                        # 可能之前的代理现在不好用了，将这些使用情况“清零”，避免误判影响使用
                        if proxy['use_count'] >= 15:
                            proxy['use_count'] = 5
                            proxy['fail_count'] = 0
                        self.proxy_list.append(proxy)
                except:
                    pass

        # 测试新爬取的免费代理
        if self.is_test_valid:
            if os.path.exists(self.proxy_file):
                with open(self.proxy_file, 'r') as fr:
                    try:
                        proxies = json.load(fr)
                        for proxy in proxies:
                            url = 'http://%s:%s' % (proxy['ip'], proxy['port'])
                            if self.url_in_proxies(url) < 0:
                                self.proxy_list.append({'proxy': url,
                                    'use_count': 0,
                                    'fail_count': 0,
                                    'valid': True})
                    except:
                        pass

        if len(self.proxy_list) == self.fixed_proxy_count:
            self.logger.info('!!!!! No proxies provided')

        # psdebug：全部使用代理，不直连
        #if len(self.proxy_list) > self.fixed_proxy_count:
        #    self.proxy_index = self.fixed_proxy_count

    @classmethod
    def from_crawler(cls, crawler):
        '''
        从crawler构造本类实例，挂上spider_closed钩子
        '''
        proxy_middleware = cls(crawler) # 本类的实例

        return proxy_middleware

    def spider_closed(self, spider):
        '''
        爬虫结束后记录可用代理
        '''
        self.dump_valid_proxy()

    def url_in_proxies(self, url):
        '''
        判断proxy在不在列表里，避免重复
        '''
        index = 0
        for proxy in self.proxy_list:
            if proxy['proxy'] == url:
                return index
            index += 1

        return -1

    def inc_proxy_index(self):
        '''
        使用下一个可用代理
        '''
        assert self.proxy_list[0]['valid']
        check_fixed = True # psdebug
        while True:
            self.proxy_index = (self.proxy_index + 1) % len(self.proxy_list)
            if self.proxy_list[self.proxy_index]['valid']:
                # psdebug：第一轮检查先跳过默认代理
                if self.proxy_index < self.fixed_proxy_count and not check_fixed:
                    check_fixed = True
                else:
                    break
        #self.logger.info('use new proxy: %s' % self.proxy_list[self.proxy_index]['proxy'])

    def set_proxy(self, request):
        '''
        给request设置代理，要记录proxy_index值
        '''
        proxy = self.proxy_list[self.proxy_index]
        # 如果不是默认代理，且其未确认为valid（使用数量达到use_count_to_check_valid）时，
        # 暂不连续使用该代理，以使新的代理能尽量平均被使用，避免一个不可用代理被一直使用
        if (not proxy['valid']) or \
                ((self.is_test_valid or self.proxy_index >= self.fixed_proxy_count) and \
                        (self.use_proxy_averagely or \
                        (proxy['use_count'] > 0 and proxy['use_count'] < self.use_count_to_check_valid))):
            self.inc_proxy_index()
            proxy = self.proxy_list[self.proxy_index]

        # 直连，删除proxy的key
        if proxy['proxy']:
            request.meta['proxy'] = proxy['proxy']
        # 使用代理，赋值proxy
        elif 'proxy' in request.meta.keys():
            del request.meta['proxy']
        # 记录proxy_index
        request.meta['proxy_index'] = self.proxy_index
        proxy['use_count'] += 1

    def get_proxy(self, will_use=True):
        '''
        获取当前代理，为None表示不使用代理
        '''
        proxy_str = self.proxy_list[self.proxy_index]['proxy']
        proxy = None
        if proxy_str:
            proxy = {}
            proxy_str = proxy_str[7:]
            proxy['ip'] = proxy_str.split(':')[0]
            proxy['port'] = proxy_str.split(':')[1]

        if will_use:
            self.proxy_list[self.proxy_index]['use_count'] += 1

        return proxy

    def invalid_proxy(self, proxy_info):
        '''
        将代理不可用次数加1
        '''
        index = -1
        if isinstance(proxy_info, int):
            index = proxy_info
        else:
            if proxy_info:
                proxy_info = str(proxy_info)
                if not proxy_info.startswith('http://'):
                    proxy_info = 'http://' + proxy_info
            index = self.url_in_proxies(proxy_info)

        if index < 0 or index >= len(self.proxy_list):
            return

        self.proxy_list[index]['fail_count'] += 1

        # 如果是默认代理，不会将valid置为False
        if index >= self.fixed_proxy_count:
            # 更新proxy的valid值
            self.check_proxy_valid(index)

        if index == self.proxy_index:
            self.inc_proxy_index()

    def check_proxy_valid(self, index):
        '''
        更新proxy的valid值
        '''
        proxy = self.proxy_list[index]
        # use_count达到use_count_to_check_valid，且失败率大于invalid_rate，将置为False
        if proxy['use_count'] >= self.use_count_to_check_valid \
                and 1.0 * proxy['fail_count'] / proxy['use_count'] > self.invalid_rate:
            proxy['valid'] = False
        else:
            proxy['valid'] = True
        if not proxy['valid']:
            self.logger.info('invalid proxy: %s(%d/%d)' % (proxy['proxy'], proxy['fail_count'], proxy['use_count']))
            # self.dump_valid_proxy() # 不在这里dump了，在爬虫结束后再记录

    def dump_valid_proxy(self):
        ''' 
        保存当前可用代理列表
        不包含默认代理，可能包含use_count<use_count_to_check_valid的proxy
        '''
        valid_proxy = []
        for i in range(self.fixed_proxy_count, len(self.proxy_list)):
            proxy = self.proxy_list[i]
            if proxy['valid']:
                valid_proxy.append(proxy)
        with open(self.valid_proxy_file, 'w') as fw:
            json.dump(valid_proxy, fw, indent=4, separators=(',', ': '))

    def process_request(self, request, spider):
        ''' 给每个request赋值proxy '''
        # 防止某些代理将请求重定向到其他网址
        request.meta['dont_redirect'] = True

        # spider发现被ban或者其他错误，认为是代理出错，请求更换
        if 'change_proxy' in request.meta.keys() and request.meta['change_proxy']:
            self.logger.info('change proxy request by spider: %s' % request)
            if 'proxy_index' in request.meta.keys():
                self.invalid_proxy(request.meta['proxy_index'])
            request.meta['change_proxy'] = False

        self.set_proxy(request)
        #proxy_user_pass = 'USERNAME:PASSWORD'
        #encoded_user_pass = base64.encodestring(proxy_user_pass)
        #request.headers['Proxy-Authorization'] = 'Basic ' + encoded_user_pass

    def process_response(self, request, response, spider):
        '''
        检查response.status，如果不在允许的状态码中则更换proxy
        '''
        # website_possible_httpstatus_list是spider在正常的爬取过程中可能会出现的状态码
        if response.status != 200 \
                and (not hasattr(spider, 'website_possible_httpstatus_list') \
                    or response.status not in spider.website_possible_httpstatus_list):
            self.logger.info('response status error: %s. to invalid proxy: %s' % \
                    (response.status, request.meta['proxy'] if 'proxy' in request.meta.keys() else ''))
            self.invalid_proxy(request.meta['proxy_index'])

            if request.meta['proxy_index'] >= self.fixed_proxy_count:
                new_request = request.copy()
                # 不过滤重复的url请求
                new_request.dont_filter = True
                return new_request
            else:
                return response
        else:
            return response

    def process_exception(self, request, exception, spider):
        '''
        处理由于使用代理导致的异常
        '''
        if 'proxy_index' in request.meta.keys():
            request_proxy_index = request.meta['proxy_index']
            #self.logger.info('%s exception: %s' % (self.proxy_list[request_proxy_index]['proxy'], exception))
            #if isinstance(exception, self.DONT_RETRY_ERRORS):
            # 不检查默认的代理
            if request_proxy_index >= self.fixed_proxy_count:
                self.logger.info('occur exception. to invalid proxy: %s' % request.meta['proxy'])
                self.invalid_proxy(request_proxy_index)
            if request_proxy_index == self.proxy_index:
                self.inc_proxy_index()
            new_request = request.copy()
            # 不过滤重复的url请求
            new_request.dont_filter = True
            return new_request
        self.logger.info('not handled exception at count %s: %s' % (request.meta['count'], exception))