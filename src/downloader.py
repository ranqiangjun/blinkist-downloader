import pathlib
# import os
from requests import RequestException
from src.extractor import IntroPageExtractor, ListenPageExtractor
from src.lock import *
from config import output_dir
from multiprocessing.pool import ThreadPool
from src.log import Log


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
        tp = ThreadPool(100)
        result = tp.imap_unordered(self.__worker, self.items)
        for item in result:
            ok, book_output_dir = item
            if not ok:
                l = Log()
                l.write_error("Intro: " + book_output_dir + '\n')
        tp.terminate()

    def __worker(self, item):
        category, book_name_no_tail, book_url = item
        print("Start downloading intro page: " + book_url)
        book_output_dir = "/".join([output_dir, category, book_name_no_tail])
        self.__prepare_dir(book_output_dir)
        lock = Lock(book_output_dir)
        ok = True
        if not lock.is_intro_locked():
            try:
                ipe = IntroPageExtractor(self.s, book_url)
                try:
                    self.save_cover_images(book_output_dir, ipe.get_cover_images())
                    self.save_meta(book_output_dir, ipe.get_meta())
                    self.save_description(book_output_dir, ipe.get_description())
                    lock.lock_intro()
                    if not ipe.is_audio_available():
                        lock.lock_audio()
                        self.save_no_audio_note(book_output_dir)
                        print(book_output_dir + " No audio, locked")
                except:
                    lock.unlock_intro()
                    ok = False
            except:
                lock.unlock_intro()
                ok = False
        else:
            print(book_output_dir + " skipped")
        return ok, book_output_dir

    def save_cover_images(self, book_output_dir, data):
        url1, url2 = data

        items = [
            ('/'.join([book_output_dir, '470.jpg']), url1),
            ('/'.join([book_output_dir, '250.jpg']), url2)
        ]

        tp = ThreadPool(2)
        result = tp.imap_unordered(self.downloader.download_file, items)
        for file_path in result:
            print(file_path + " downloaded")
        tp.terminate()

    def save_meta(self, book_output_dir, data):
        title, subtitle, author, time_to_read = data
        self.downloader.write_file('/'.join([book_output_dir, 'title.md']), title)
        self.downloader.write_file('/'.join([book_output_dir, 'subtitle.md']), subtitle)
        self.downloader.write_file('/'.join([book_output_dir, 'author.md']), author)
        self.downloader.write_file('/'.join([book_output_dir, 'time_to_read.md']), time_to_read)

    def save_description(self, book_output_dir, data):
        summary, for_who, about_author = data
        self.downloader.write_file('/'.join([book_output_dir, 'summary.md']), summary)
        self.downloader.write_file('/'.join([book_output_dir, 'for_who.md']), for_who)
        self.downloader.write_file('/'.join([book_output_dir, 'about_author.md']), about_author)

    def save_no_audio_note(self, book_output_dir):
        now = datetime.datetime.now()
        self.downloader.write_file('/'.join([book_output_dir, 'no_audio.md']), now.strftime("%Y-%m-%d %H:%M"))


class ListenPagesDownloader:
    def __init__(self, s, listen_pages, downloader):
        self.s = s
        self.items = listen_pages
        self.downloader = downloader

    @staticmethod
    def __prepare_dir(dir_path):
        pathlib.Path(dir_path).mkdir(parents=True, exist_ok=True)

    def download(self):
        tp = ThreadPool(5)
        result = tp.imap_unordered(self.__worker, self.items)
        for item in result:
            ok, book_output_dir = item
            if not ok:
                l = Log()
                l.write_error("Listen: " + book_output_dir + '\n')
        tp.terminate()

    def __worker(self, item):
        category, book_name_no_tail, book_url = item
        print("Start downloading listen page: " + book_url)
        book_output_dir = "/".join([output_dir, category, book_name_no_tail])
        self.__prepare_dir(book_output_dir)

        lock = Lock(book_output_dir)

        is_audio_locked = lock.is_audio_locked()
        is_markup_locked = lock.is_markup_locked()
        ok = True
        if is_audio_locked and is_markup_locked:
            print(book_output_dir + " skipped")
        else:
            try:
                lpe = ListenPageExtractor(self.s, book_url)
                if not is_audio_locked:
                    try:
                        self.__save_audio(book_output_dir, lpe.get_audio_items(), lock)
                        lock.lock_audio()
                    except:
                        ok = False
                        lock.unlock_audio()
                        lock.unlock_markup()
                if not is_markup_locked:
                    self.__save_html(book_output_dir, lpe.get_html_data())
                    self.__save_html_per_chapter(book_output_dir, lpe.get_html_data_per_chapter())
                    lock.lock_markup()
            except:
                lock.unlock_audio()
                lock.unlock_markup()
                ok = False
        return ok, book_output_dir

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
