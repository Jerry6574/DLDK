from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import re
import pandas as pd
import os
import time

j = 1


def get_webdriver(chrome_options=None):
    chromedriver_path = r"lib/chromedriver"

    browser = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
    browser.set_page_load_timeout(240)

    return browser


def delete_files(folder):
    for root, dirs, files in os.walk(folder):
        for file in files:
            os.remove(os.path.join(folder, root, file))


class DLDK:
    default_dl_root = os.path.join(os.getcwd(), "dl_root")

    def __init__(self, url, dl_root=default_dl_root):
        self.url = url
        self.dl_root = dl_root

        if not os.path.isdir(self.dl_root):
            os.mkdir(self.dl_root)

        self.n_items = 0
        self.n_pages = 0

        self.pg = url.split('/')[5]
        self.spg = url.split('/')[6]
        pg_spg = self.pg + "_" + self.spg

        self.dl_spg_dir = os.path.join(self.dl_root, pg_spg)
        self.concat_dir = os.path.join(os.getcwd(), "concat")

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
        if ("page=1" in self.url and "pageSize=500" in self.url) or ("product-detail" in self.url):
            return 1

        self.n_items = self.get_n_items()
        page_size = 500

        n_pages = 0
        if self.n_items <= 500:
            n_pages = 1
        elif self.n_items % page_size == 0:
            self.n_items = self.n_items // page_size
        else:
            n_pages = self.n_items // page_size + 1

        return n_pages

    def dl_spg(self, wsw_pn=None, page_start=1, file_index=None):
        self.n_pages = self.get_n_pages()

        chrome_options = webdriver.ChromeOptions()
        pg_spg = self.pg + "_" + self.spg
        dl_dir = os.path.join(self.dl_root, pg_spg)
        self.dl_spg_dir = dl_dir

        if not os.path.isdir(dl_dir):
            os.mkdir(dl_dir)

        prefs = {"download.default_directory": dl_dir}
        chrome_options.add_experimental_option("prefs", prefs)

        n_try = 0

        for i in range(page_start, self.n_pages+1):
            while n_try < 5:
                try:
                    if "page=" in self.url and "pageSize=" in self.url:
                        dl_spg_url = self.url
                    elif "?" not in self.url:
                        dl_spg_url = self.url + "?pageSize=500" + "&page=" + str(i)
                    else:
                        dl_spg_url = self.url + "&pageSize=500" + "&page=" + str(i)

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
                        try:
                            dl_buttons[1].click()
                        except IndexError:
                            browser.quit()
                            print("1 item: ", wsw_pn, self.url)
                            return
                    except WebDriverException:
                        browser.find_element_by_css_selector("div.popover--overlay").click()
                        time.sleep(1)
                        try:
                            dl_buttons[1].click()
                        except IndexError:
                            print("1 item: ", wsw_pn, self.url)
                            browser.quit()
                            return
                    time.sleep(8)
                    browser.quit()

                    rename_src = os.path.join(dl_dir, "download.csv")

                    if file_index is not None:
                        rename_dst = os.path.join(dl_dir, "dl_" + str(file_index) + ".csv")
                    else:
                        rename_dst = os.path.join(dl_dir, "dl_" + str(i) + ".csv")

                    os.rename(rename_src, rename_dst)
                    df = pd.read_csv(rename_dst)

                    if wsw_pn is not None:
                        df["WSW PN"] = wsw_pn

                    df.to_excel(rename_dst.replace(".csv", ".xlsx"))
                    os.remove(rename_dst)
                    break

                except (NoSuchElementException, TimeoutException, WebDriverException):
                    browser.quit()
                    print("Fail " + str(n_try))
                    n_try += 1

        # reset to default download directory
        prefs = {"download.default_directory": r"C:\Users\jerryw\Downloads"}
        chrome_options.add_experimental_option("prefs", prefs)

    def concat_all(self, delete_csv=False):
        csv_paths = []
        csv_df_list = []

        for root, dirs, files in os.walk(self.dl_spg_dir):
            for file in files:
                if file.endswith(".csv"):
                    csv_paths.append(os.path.join(self.dl_spg_dir, root, file))

        for csv_path in csv_paths:
            csv_df = pd.read_csv(csv_path)
            csv_df["Product Group"] = self.pg
            csv_df["Subproduct Group"] = self.spg
            csv_df_list.append(csv_df)

        csv_df_concat = pd.concat(csv_df_list, ignore_index=True)
        pg_spg = self.pg + "_" + self.spg
        csv_df_concat.to_excel(os.path.join(self.concat_dir, pg_spg + ".xlsx"), index=False)

        time.sleep(10)
        if delete_csv:
            delete_files(self.dl_spg_dir)


# download one product group
def one_dl(url, page_start=1, wsw_pn=None, file_index=None, concat=True):
    tb = DLDK(url)
    tb.dl_spg(wsw_pn=wsw_pn, page_start=page_start, file_index=file_index)
    if concat:
        tb.concat_all(delete_csv=True)


# download multiple product group
def multi_dl(filename, concat=True):
    df = pd.read_excel(filename)

    for file_index, row in enumerate(df.itertuples()):
        wsw_pn = getattr(row, "WSW_PN")
        url = getattr(row, "DK_Link")
        one_dl(url, wsw_pn=wsw_pn, concat=concat, file_index=file_index)


def main():
    multi_dl("dl list.xlsx", concat=False)


if __name__ == '__main__':
    main()
