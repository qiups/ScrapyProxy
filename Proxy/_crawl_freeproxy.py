# -*- coding: utf-8 -*-

import json
#from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from proxy.spiders.freeproxy_spider import FreeProxySpider
from proxy.spiders.testproxy_spider import TestProxySpider

from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging

# 记录有效的免费代理的文件
valid_proxy_file = 'validproxy.json'
# 需要的有效免费代理数目
valid_proxy_threshold = 10

if __name__ == '__main__':
    valid_count = 0
    if valid_proxy_threshold > 0:
        try:
            with open(valid_proxy_file, 'r') as f:
                proxies = json.load(f)
                valid_count = len(proxies)
        except:
            pass

    if valid_count >= valid_proxy_threshold:
        print '##### Already has enough proxies(demand %d): %d' % (valid_proxy_threshold, len(proxies))
    else:
        settings = get_project_settings()
        configure_logging(settings = settings)
        runner = CrawlerRunner(settings = settings)

        @defer.inlineCallbacks
        def crawl():
            yield runner.crawl(FreeProxySpider)
            yield runner.crawl(TestProxySpider)
            reactor.stop()

        crawl()
        reactor.run()
    
        #process = CrawlerProcess(get_project_settings())
        #process.crawl(FreeProxySpider)
        #process.crawl(TestProxySpider)
        #process.start()
