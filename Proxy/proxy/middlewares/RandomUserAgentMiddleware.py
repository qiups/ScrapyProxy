# -*- coding: utf-8 -*-

import random

class RandomUserAgentMiddleware(object):
    def __init__(self, agents):
        self.agents = agents

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.getlist('USER_AGENTS')) # 返回的是本类的实例cls

    def process_request(self, request, spider):
        '''
        设置随机User-Agent
        '''
        request.headers.setdefault('User-Agent', random.choice(self.agents))