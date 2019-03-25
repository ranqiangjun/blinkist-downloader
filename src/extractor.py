from bs4 import BeautifulSoup
from src.urls import book_urls, category_urls
from multiprocessing.pool import ThreadPool
import pickle
import os


class BookUrlExtractor:

    def __init__(self, s):
        self.urls = category_urls
        self.s = s
        self.data = self.__get_data()

    def __get_data(self):
        cache_file_name = '.book.cache'
        if os.path.exists(cache_file_name):
            print("Cache exists")
            f = open(cache_file_name, 'rb')
            return pickle.load(f)
        items = []
        book_names = []
        for category_url in self.urls:
            r = self.s.get(category_url)
            soup = BeautifulSoup(r.text, 'html.parser')
            category = self.__get_category(category_url)
            print("Category: " + category)
            for item in self.__get_books(soup):
                book_url = item['href']
                book_name = self.__get_book_name(book_url)
                if book_name not in book_names:
                    book_names.append(book_name)
                    items.append((category, book_name))
        f = open(cache_file_name, 'wb')
        pickle.dump(items, f)
        return items

    @staticmethod
    def __get_category(category_url):
        # Get the 2nd last part.
        name = category_url.split('/')[-2]
        parts = name.split('-')
        # Remove -en.
        parts.pop()
        return '-'.join(parts)

    @staticmethod
    def __get_book_name(book_url):
        # Get the last part.
        name = book_url.split('/')[-1]
        parts = name.split('-')
        # Remove -en.
        parts.pop()
        return '-'.join(parts)

    @staticmethod
    def __get_books(soup):
        return soup.select('.book-list .letter-book-list__item')

    def get_intro_pages(self):
        items = []
        for item in self.data:
            category, name = item
            url = book_urls['intro_page_prefix'] + name
            items.append((category, name, url))
        return items

    def get_listen_pages(self):
        items = []
        for item in self.data:
            category, name = item
            url = book_urls['listen_page_prefix'] + name
            items.append((category, name, url))
        return items


class IntroPageExtractor:

    def __init__(self, s, intro_page_url):
        r = s.get(intro_page_url)
        self.soup = BeautifulSoup(r.text, 'html.parser')
        self.s = s
        self.url = intro_page_url

    def __get_author(self):
        return self.soup.select('.book__header__author')[0].text.strip()

    def __get_title(self):
        return self.soup.select('.book__header__title')[0].text.strip()

    def __get_subtitle(self):
        return self.soup.select('.book__header__subtitle')[0].text.strip()

    def __get_read_time(self):
        return self.soup.select('.book__header__info-item-body')[0].text.strip()

    def __get_synopsis(self):
        node = self.soup.select('div[ref=synopsis]')[0]
        del node['class']
        return node.prettify().strip()

    def __get_who_should_read(self):
        node = self.soup.select('div[ref=who_should_read]')[0]
        del node['class']
        return node.prettify().strip()

    def __get_about_the_author(self):
        node = self.soup.select('div[ref=about_the_author]')[0]
        del node['class']
        return node.prettify().strip()

    def get_meta(self):
        title = self.__get_title()
        subtitle = self.__get_subtitle()
        author = self.__get_author()
        time_to_read = self.__get_read_time()
        return title, subtitle, author, time_to_read

    def get_description(self):
        summary = self.__get_synopsis()
        for_who = self.__get_who_should_read()
        about_author = self.__get_about_the_author()
        return summary, for_who, about_author

    def get_cover_images(self):
        url1 = self.soup.select('.book__header__image > img')[0]['src']
        url2 = self.soup.select('.book__header__image > img')[1]['src']
        return url1, url2

    def is_audio_available(self):
        if len(self.soup.select('.book__header__info-item-body')) > 1:
            text = self.soup.select('.book__header__info-item-body')[1].text.strip()
            if text == "Audio available":
                return True
        return False


class ListenPageExtractor:

    def __init__(self, s, listen_page_url):
        r = s.get(listen_page_url)
        self.soup = BeautifulSoup(r.text, 'html.parser')
        self.s = s
        self.url = listen_page_url

    def __get_id(self):
        return self.soup.select('main > div.reader__container')[0]['data-book-id']

    def __get_chapter_data(self):
        data = []
        for chapter in self.soup.select('.chapter.chapter'):
            chapter_id = chapter['data-chapterid']
            chapter_number = chapter['data-chapterno']
            data.append((chapter_id, chapter_number))
        return data

    def __get_csrf_token(self):
        return self.soup.select('meta[name="csrf-token"]')[0]['content']

    def __get_audio_url(self, item):
        chapter_number, audio_endpoint = item
        file_name = str(chapter_number) + '.m4a'
        csrf_token = self.__get_csrf_token()
        user_agent = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2)',
            'AppleWebKit/537.36 (KHTML, like Gecko)',
            'Chrome/72.0.3626.121 Safari/537.36'
        ]
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRF-Token': csrf_token,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': self.url,
            'User-Agent': ' '.join(user_agent)
        }
        r = self.s.get(audio_endpoint, headers=headers)
        j = r.json()
        return file_name, j['url']

    def get_audio_items(self):
        book_id = self.__get_id()
        items = []
        for chapter in self.__get_chapter_data():
            chapter_id, chapter_number = chapter
            audio_endpoint = book_urls['audio_api_prefix'] + book_id + '/chapters/' + chapter_id + '/audio'
            items.append((chapter_number, audio_endpoint))
        number = len(items)
        tp = ThreadPool(number)
        result = tp.imap_unordered(self.__get_audio_url, items)
        audio_items = []
        for audio_item in result:
            audio_items.append(audio_item)
        tp.terminate()
        return audio_items

    def get_html_data(self):
        content = ''
        for chapter in self.soup.select('.chapter.chapter'):
            content += chapter.prettify()
        return content

    def get_html_data_per_chapter(self):
        data = []
        for chapter in self.soup.select('.chapter.chapter'):
            content = chapter.prettify()
            chapter_number = chapter['data-chapterno']
            file_name = chapter_number + '.html'
            data.append((file_name, content))
        return data
