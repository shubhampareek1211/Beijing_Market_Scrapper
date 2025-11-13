class UserAgentMiddleware:
    def process_request(self, request, spider):
        # A mainstream desktop UA helps avoid HTML shells.
        request.headers.setdefault(
            b"User-Agent",
            b"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        request.headers.setdefault(b"Accept", b"application/json, text/javascript, */*; q=0.01")
        request.headers.setdefault(b"Accept-Language", b"zh-CN,zh;q=0.9,en;q=0.8")
        request.headers.setdefault(b"Origin", b"https://www.cninfo.com.cn")
        request.headers.setdefault(b"Referer", b"https://www.cninfo.com.cn/")
        request.headers.setdefault(b"X-Requested-With", b"XMLHttpRequest")
        return None
