import datetime


class Log:

    def __init__(self):
        self.__log_path = 'error.log'

    def __write_log(self, message):
        f = open(self.__log_path, 'a')
        f.write(message)
        f.close()

    def write_error(self, message):
        print("!" * 32 + "\n" + message + "\n" + "!" * 32 + "\n")
        self.__write_log(message)
