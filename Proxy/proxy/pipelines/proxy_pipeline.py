# -*- coding: utf-8 -*-

import json
from proxy import util
from proxy import threadpool

class ProxyPipeline(object):
    logger = None
    proxy_file = 'freeproxy.json'
    valid_proxy = []
    check_thread_pool = threadpool.ThreadPool(10)

    def open_spider(self, spider):
        self.logger = spider.logger

    def process_item(self, item, spider):
        self.check_thread_pool.putRequest(threadpool.WorkRequest(util.check_proxy, [item, 3], None, callback=self.check_proxy_callback))
        try:
            self.check_thread_pool.poll()
        except BaseException:
            pass
        return item

    def check_proxy_callback(self, request, result):
        item = request.args[0]
        if result:
            self.valid_proxy.append(dict(item))
        else:
            self.logger.info('##### invalid proxy: %s:%s' % (item['ip'], item['port']))

    def close_spider(self, spider):
        self.logger.info('##### waiting for proxy threadpool exit...')
        self.check_thread_pool.wait()
        self.logger.info('##### save valid proxy. count: %d' % len(self.valid_proxy))
        with open(self.proxy_file, 'w') as _file:
            json.dump(self.valid_proxy, _file, indent=4, separators=(',', ': '))