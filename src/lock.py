import datetime
import os


class Lock:

    def __init__(self, book_output_dir):
        self.__audio_lock_path = '/'.join([book_output_dir, 'lock.audio'])
        self.__intro_lock_path = '/'.join([book_output_dir, 'lock.intro'])
        self.__markup_lock_path = '/'.join([book_output_dir, 'lock.markup'])

    @staticmethod
    def __write_lock(lock_path):
        f = open(lock_path, 'w')
        now = datetime.datetime.now()
        f.write(now.strftime("%Y-%m-%d %H:%M"))
        f.close()

    def __remove_file(self, lock_path):
        if self.__is_file_exists(lock_path):
            os.remove(lock_path)

    def lock_audio(self):
        self.__write_lock(self.__audio_lock_path)

    def lock_intro(self):
        self.__write_lock(self.__intro_lock_path)

    def unlock_audio(self):
        self.__remove_file(self.__audio_lock_path)

    def unlock_intro(self):
        self.__remove_file(self.__intro_lock_path)

    def unlock_markup(self):
        self.__remove_file(self.__markup_lock_path)

    def lock_markup(self):
        self.__write_lock(self.__markup_lock_path)

    @staticmethod
    def __is_file_exists(file_path) :
        return os.path.isfile(file_path)

    def is_audio_locked(self):
        return self.__is_file_exists(self.__audio_lock_path)

    def is_intro_locked(self):
        return self.__is_file_exists(self.__intro_lock_path)

    def is_markup_locked(self):
        return self.__is_file_exists(self.__markup_lock_path)
