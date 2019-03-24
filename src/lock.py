import datetime
import os


class Lock:

    def __init__(self, book_output_dir):
        self.audio_lock_path = '/'.join([book_output_dir, 'audio.lock'])
        self.intro_lock_path = '/'.join([book_output_dir, 'intro.lock'])

    def lock_audio(self):
        f = open(self.audio_lock_path, 'w')
        now = datetime.datetime.now()
        f.write(now.strftime("%Y-%m-%d %H:%M"))
        f.close()

    def lock_intro(self):
        f = open(self.intro_lock_path, 'w')
        now = datetime.datetime.now()
        f.write(now.strftime("%Y-%m-%d %H:%M"))
        f.close()

    def is_audio_locked(self):
        return os.path.isfile(self.audio_lock_path)

    def is_intro_locked(self):
        return os.path.isfile(self.intro_lock_path)




