
# 防止爬虫被禁IP

    主要参考这个项目 https://github.com/kohn/HttpProxyMiddleware

# Spider设置

    # 在正常的爬取过程中可能会出现的状态码，配合代理中间件使用，
    # 若response.status不等于200且不在此列表中，将视为代理出错，会重发请求
    website_possible_httpstatus_list = []

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'proxy.middlewares.RandomUserAgentMiddleware.RandomUserAgentMiddleware': 1, # 动态设置User-Agent
            'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 80, # 超时设置
            'proxy.middlewares.ProxyMiddleware.ProxyMiddleware': 100 # 使用代理
        },
        'DOWNLOAD_TIMEOUT': 10, # 10-15秒是合理范围
        'COOKIES_ENABLED': False, # 禁用cookies
        'DOWNLOAD_DELAY': 2 # 延迟下载
    }

# parse错误

    若是解析response出错（ip被禁，或代理出错），可设置 request.meta['change_proxy'] = True 并重发请求