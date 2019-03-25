import pathlib
# import os
from src.extractor import IntroPageExtractor, ListenPageExtractor
from src.lock import *
from config import output_dir
from multiprocessing.pool import ThreadPool


class Downloader:

    def __init__(self, s):
        self.s = s

    def download_file(self, item):
        file_path, url = item
        r = self.s.get(url, stream=True)
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        # os.system('wget "' + url + '" -O "' + file_path + '"')
        return file_path

    @staticmethod
    def write_file(file_path, content):
        f = open(file_path, 'w')
        f.write(content)
        f.close()


class IntroPagesDownloader:

    def __init__(self, s, items, downloader):
        self.s = s
        self.items = items
        self.downloader = downloader

    @staticmethod
    def __prepare_dir(dir_path):
        pathlib.Path(dir_path).mkdir(parents=True, exist_ok=True)

    def download(self):
        for item in self.items:
            category, name, url = item
            print("Start downloading intro page: " + url)
            book_output_dir = "/".join([output_dir, category, name])
            self.__prepare_dir(book_output_dir)
            lock = Lock(book_output_dir)
            if not lock.is_intro_locked():
                ipe = IntroPageExtractor(self.s, url)
                self.save_cover_images(book_output_dir, ipe.get_cover_images())
                self.save_meta(book_output_dir, ipe.get_meta())
                self.save_description(book_output_dir, ipe.get_description())
                if not ipe.is_audio_available():
                    lock.lock_audio()
                    self.save_no_audio_note(book_output_dir)
                    print(book_output_dir + " No audio, locked")
                lock.lock_intro()
            else:
                print(book_output_dir + " skipped")

    def save_cover_images(self, book_output_dir, data):
        url1, url2 = data

        items = [
            ('/'.join([book_output_dir, '470.jpg']), url1),
            ('/'.join([book_output_dir, '250.jpg']), url2)
        ]

        tp = ThreadPool(2)
        result = tp.imap_unordered(self.downloader.download_file, items)
        for i in result:
            print(i + " downloaded")
        tp.terminate()

    def save_meta(self, book_output_dir, data):
        title, subtitle, author, time_to_read = data
        self.downloader.write_file('/'.join([book_output_dir, 'title.txt']), title)
        self.downloader.write_file('/'.join([book_output_dir, 'subtitle.txt']), subtitle)
        self.downloader.write_file('/'.join([book_output_dir, 'author.txt']), author)
        self.downloader.write_file('/'.join([book_output_dir, 'time_to_read.txt']), time_to_read)

    def save_description(self, book_output_dir, data):
        summary, for_who, about_author = data
        self.downloader.write_file('/'.join([book_output_dir, 'summary.txt']), summary)
        self.downloader.write_file('/'.join([book_output_dir, 'for_who.txt']), for_who)
        self.downloader.write_file('/'.join([book_output_dir, 'about_author.txt']), about_author)

    def save_no_audio_note(self, book_output_dir):
        now = datetime.datetime.now()
        self.downloader.write_file('/'.join([book_output_dir, 'no_audio.txt']), now.strftime("%Y-%m-%d %H:%M"))


class ListenPagesDownloader:
    def __init__(self, s, listen_pages, downloader):
        self.s = s
        self.items = listen_pages
        self.downloader = downloader

    @staticmethod
    def __prepare_dir(dir_path):
        pathlib.Path(dir_path).mkdir(parents=True, exist_ok=True)

    def download(self):
        for item in self.items:
            category, name, url = item
            print("Start downloading listen page: " + url)
            book_output_dir = "/".join([output_dir, category, name])
            self.__prepare_dir(book_output_dir)

            lock = Lock(book_output_dir)

            is_audio_locked = lock.is_audio_locked()
            is_markup_locked = lock.is_markup_locked()

            if is_audio_locked and is_markup_locked:
                print( book_output_dir + " skipped")
            else:
                lpe = ListenPageExtractor(self.s, url)
                if not is_audio_locked:
                    self.__save_audio(book_output_dir, lpe.get_audio_items(), lock)
                    lock.lock_audio()
                if not is_markup_locked :
                    self.__save_html(book_output_dir, lpe.get_html_data())
                    self.__save_html_per_chapter(book_output_dir, lpe.get_html_data_per_chapter())
                    lock.lock_markup()

    def __save_html(self, book_output_dir, content):
        file_path = '/'.join([book_output_dir, 'README.md'])
        self.downloader.write_file(file_path, content)

    def __save_html_per_chapter(self, book_output_dir, items):
        for item in items:
            file_name, content = item
            file_path = '/'.join([book_output_dir, file_name])
            self.downloader.write_file(file_path, content)

    def __save_audio(self, book_output_dir, items, lock):
        audio_items = []
        for item in items:
            file_name, audio_url = item
            file_path = '/'.join([book_output_dir, file_name])
            audio_items.append((file_path, audio_url))
        number = len(audio_items)
        tp = ThreadPool(number)
        result = tp.imap_unordered(self.downloader.download_file, audio_items)
        for i in result:
            print(i + " downloaded")
        tp.terminate()
        lock.lock_audio()
        print( book_output_dir + " locked")
