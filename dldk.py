from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import re
import pandas as pd
import os
import time
import datetime
import bs4


def get_webdriver(chrome_options=None):
    chromedriver_path = r"lib/chromedriver"

    browser = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
    browser.set_page_load_timeout(240)

    return browser


class DLDK:
    def __init__(self, url):
        self.url = url
        self.n_item = 0

    def get_n_items(self):
        soup = bs4.BeautifulSoup()