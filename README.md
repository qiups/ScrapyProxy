
# ��ֹ���汻��IP

    ��Ҫ�ο������Ŀ https://github.com/kohn/HttpProxyMiddleware

# Spider����

    # ����������ȡ�����п��ܻ���ֵ�״̬�룬��ϴ����м��ʹ�ã�
    # ��response.status������200�Ҳ��ڴ��б��У�����Ϊ����������ط�����
    website_possible_httpstatus_list = []

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'proxy.middlewares.RandomUserAgentMiddleware.RandomUserAgentMiddleware': 1, # ��̬����User-Agent
            'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 80, # ��ʱ����
            'proxy.middlewares.ProxyMiddleware.ProxyMiddleware': 100 # ʹ�ô���
        },
        'DOWNLOAD_TIMEOUT': 10, # 10-15���Ǻ���Χ
        'COOKIES_ENABLED': False, # ����cookies
        'DOWNLOAD_DELAY': 2 # �ӳ�����
    }

# parse����

    ���ǽ���response����ip���������������������� request.meta['change_proxy'] = True ���ط�����