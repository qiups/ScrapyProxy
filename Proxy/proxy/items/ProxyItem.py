# -*- coding: utf-8 -*-

import scrapy

class ProxyItem(scrapy.Item):
	ip = scrapy.Field()
	port = scrapy.Field()