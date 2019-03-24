# -*- coding: UTF-8 -*-

import requests
from login import *
from extractor import BookUrlExtractor
from downloader import *

s = requests.Session()
log_me_in = Login(s)
log_me_in.login()


bue = BookUrlExtractor(s)
intro_pages = bue.get_intro_pages()
listen_pages = bue.get_listen_pages()


downloader = Downloader(s)
# ipd = IntroPagesDownloader(s, intro_pages, downloader)
# ipd.download()

lpd = ListenPagesDownloader(s, listen_pages, downloader)
lpd.download()
