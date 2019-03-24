import datetime
import os


class Lock:

    def __init__(self, book_output_dir):
        self.lock_path = '/'.join([book_output_dir, 'lock'])

    def lock(self):
        f = open(self.lock_path, 'w')
        now = datetime.datetime.now()
        f.write(now.strftime("%Y-%m-%d %H:%M"))
        f.close()

    def unlock(self):
        os.remove(self.lock_path)

    def is_locked(self):
        return os.path.isfile(self.lock_path)





