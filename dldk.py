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
        self.n_items = self.get_n_items()
        self.n_pages = self.get_n_pages()

    def get_n_items(self):
        browser = get_webdriver()
        browser.get(self.url)

        num_re = re.compile(r"[^0-9]")
        n_items_str = browser.find_element_by_id("matching-records-count").text
        n_items = int(re.sub(num_re, "", n_items_str))

        browser.close()
        browser.quit()

        return n_items

    def get_n_pages(self):
        page_size = 500

        if self.n_items <= 500:
            n_pages = 1
        elif self.n_items % page_size == 0:
            self.n_items = self.n_items // page_size
        else:
            n_pages = self.n_items // page_size + 1

        return n_pages


def main():
    url = "https://www.digikey.com/products/en/connectors-interconnects/terminal-blocks-headers-plugs-and-sockets/370"
    dldk = DLDK(url)
    print(dldk.n_items, dldk.n_pages)


if __name__ == '__main__':
    main()
