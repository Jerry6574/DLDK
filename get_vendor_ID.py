import bs4
import requests
import pandas as pd


def get_soup(url):
    content = requests.get(url).content
    soup = bs4.BeautifulSoup(content, 'lxml')
    return soup


def unpack_li(li):
    dk_domain = 'https://www.digikey.com'
    href = li.find('a')['href']
    supplier_name = href.split('/')[-1]
    supplier_url = dk_domain + href

    return supplier_name, supplier_url


def dk_suppliers():
    suppliers_center = "https://www.digikey.com/en/supplier-centers"
    soup = get_soup(suppliers_center)

    suppliers_li = soup.find_all('li', attrs={'class': 'supplier-list-item'})

    supplier_arr = []
    for li in suppliers_li:
        supplier_arr.append(unpack_li(li))

    supplier_df = pd.DataFrame(supplier_arr, columns=["Supplier Name", "Supplier URL"])
    return supplier_df


def get_id(href):
    last = href.split('/')[-1]
    start_index = last.find('v=') + 2
    vendor_id = last[start_index:]
    return vendor_id


def id_by_view_all(soup):
    href = soup.find('span', text='Product Listing').find_next('a', text='View All')['href']
    vendor_id = get_id(href)
    return vendor_id


def id_by_product_category(soup):
    product_category = soup.find('div', attrs={'class': 'product-categories-row'})
    href = product_category.find('a')['href']
    vendor_id = get_id(href)
    return vendor_id


def get_vendor_id(supplier_url):
    soup = get_soup(supplier_url)
    try:
        vendor_id = id_by_view_all(soup)
    except AttributeError:
        try:
            vendor_id = id_by_product_category(soup)
        except AttributeError:
            return "None"
    return vendor_id


def main():
    suppliers_df = dk_suppliers()

    vendor_ids = []
    for url in suppliers_df['Supplier URL'].tolist():
        _id = get_vendor_id(url)
        print(_id)
        vendor_ids.append(_id)

    suppliers_df["Vendor ID"] = vendor_ids
    suppliers_df.to_excel("suppliers_id.xlsx", index=False)


if __name__ == '__main__':
    main()
