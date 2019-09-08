import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import re

with open('raw_kaggle_huffpost.json', 'r') as file:
    entries = file.read().lower().split("\n")


def create_cookies():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
    driver.get('https://www.huffpost.com/entry/immigrant-children-separated-from-parents_n_5b087b90e4b0802d69cb4070')
    driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[4]/div/div[2]/form[1]/div/input').click()
    cookies_list = driver.get_cookies()
    cookies_dict = {}
    for cookie in cookies_list:
        cookies_dict[cookie['name']] = cookie['value']

    return cookies_dict


def parse_response(response, new):
    soup = BeautifulSoup(response.text, 'html.parser')

    title = soup.find(attrs={"class": "headline__title"})
    if title is not None:
        title = title.getText()
    else:
        title = soup.find(attrs={"class": "headline"}).getText()

    subtitle = soup.find(attrs={"class": "headline__subtitle"})
    if subtitle is not None:
        subtitle = subtitle.getText()
    else:
        subtitle = soup.find(attrs={"class": "dek"})
        if subtitle is not None:
            subtitle = subtitle.getText()

    date = soup.find(attrs={"class": "timestamp"})
    if date is not None:
        date = date.getText().split()[0]

    text = ""

    paragraphs = soup.find_all(attrs={"class": "content-list-component yr-content-list-text text"})
    if len(paragraphs) == 0:
        paragraphs = soup.find_all(attrs={"class": "cli cli-text"})

    for paragraph in paragraphs:
        text += paragraph.getText()
        text += '\n'

    return {
        'title': title,
        'subtitle': subtitle,
        'category': new['category'],
        'text': text,
        'date': date,
        'url': url
    }


regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

cookies = create_cookies()
headers = {
    'Referer': 'https://www.huffpost.com/entry/immigrant-children-separated-from-parents_n_5b087b90e4b0802d69cb4070',
    'Sec-Fetch-Mode': 'no-cors',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'
}

cached = pd.read_csv('datasets/cached_news.csv')
network = pd.read_csv('datasets/network_news.csv')

df = pd.concat([cached, network]).drop_duplicates().reset_index(drop=True)
df.to_csv('datasets/cached_news.csv', index=False)
network.iloc[0:0].to_csv('datasets/network_news.csv', index=False)

data_source = []
news = []

for entry in entries:
    new = eval(entry)

    if new['category'] in ['politics', 'entertainment', 'queer voices',
                           'business', 'comedy', 'sports', 'black voices',
                           'the worldpost', 'women', 'impact', 'crime', 'media',
                           'weird news', 'green', 'religion', 'science', 'world news',
                           'tech', 'arts & culture', 'latino voices', 'education']:
        news.append(new)

index_from_network = 0
for i, new in enumerate(news):
    if i % 50 == 0:
        print(i, index_from_network, len(news))

    url = new['link']

    row = df[df.url == url]
    if not row.empty:
        continue

    try:
        index_from_network = index_from_network + 1
        if re.match(regex, url) is None:
            print('invalid url:', url)
            continue

        response = requests.get(url, headers=headers, cookies=cookies)
        new = parse_response(response, new)
        data_source.append(new)
        if index_from_network % 100 == 0:
            print('saving dataset', index_from_network)
            pd.DataFrame(data_source).to_csv('datasets/network_news.csv', index=False)
    except:
        print('error when trying to process', url)
