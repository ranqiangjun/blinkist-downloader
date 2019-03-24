from bs4 import BeautifulSoup
from urls import book_urls, category_urls


class BookUrlExtractor:

    def __init__(self, s):
        print("Init BookUrlExtractor")
        self.urls = category_urls
        self.s = s
        self.data = self.__get_data()

    def __get_data(self):
        items = []
        names = []
        for url in self.urls:
            r = self.s.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            category = self.__get_category(soup)
            print("category: " + category)
            for item in self.__get_books(soup):
                url = item['href']
                name = url.split('/')[-1]
                if name not in names:
                    names.append(name)
                    items.append((category, name))
        return items

    @staticmethod
    def __get_category(soup):
        return soup.select('.book-list__header')[0].text.strip()

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

    def __get_audio_url(self, audio_endpoint):
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
        return j['url']

    def get_audio_items(self):
        data = []
        book_id = self.__get_id()
        for chapter in self.__get_chapter_data():
            chapter_id, chapter_number = chapter
            audio_endpoint = book_urls['audio_api_prefix'] + book_id + '/chapters/' + chapter_id + '/audio'
            audio_url = self.__get_audio_url(audio_endpoint)
            chapter_number = int(chapter_number) + 1
            file_name = str(chapter_number) + '.m4a'
            data.append((file_name, audio_url))
        return data

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
            chapter_number = int(chapter_number) + 1
            file_name = str(chapter_number) + '.html'
            data.append((file_name, content))
        return data
