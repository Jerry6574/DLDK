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
        self.pg = url.split('/')[5]
        self.spg = url.split('/')[6]

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

    def dl_spg(self, dl_root):
        chrome_options = webdriver.ChromeOptions()
        pg_spg = self.pg + "_" + self.spg
        dl_dir = os.path.join(dl_root, pg_spg)

        # https://www.digikey.com/products/en/connectors-interconnects/terminal-blocks-headers-plugs-and-sockets/370?pageSize=500
        prefs = {"download.default_directory": dl_dir}
        chrome_options.add_experimental_option("prefs", prefs)

        n_try = 0
        browser = None

        for i in range(1, self.n_pages+1):
            while n_try < 5:
                try:
                    dl_spg_url = self.url + "?pageSize=500" + "&page=" + str(i)
                    browser = get_webdriver(chrome_options)
                    browser.get(dl_spg_url)
                    try:
                        toggle_ok = browser.find_element_by_css_selector("div.button")
                        toggle_ok.click()
                    except:
                        pass
                    time.sleep(1)
                    # scroll to bottom of page
                    browser.maximize_window()
                    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)

                    dl_buttons = browser.find_elements_by_css_selector("form.download-table input.button")
                    try:
                        dl_buttons[1].click()
                    except WebDriverException:
                        browser.find_element_by_css_selector("div.popover--overlay").click()
                        time.sleep(1)
                        dl_buttons[1].click()

                    time.sleep(5)
                    browser.quit()
                    break
                except (NoSuchElementException, TimeoutException, WebDriverException):
                    browser.quit()
                    print("Fail " + str(n_try))
                    n_try += 1


def main():
    url = "https://www.digikey.com/products/en/connectors-interconnects/terminal-blocks-headers-plugs-and-sockets/370"
    tb = DLDK(url)
    tb.dl_spg()
    print(tb.n_items, tb.n_pages, tb.pg, tb.spg)


if __name__ == '__main__':
    main()
