from bs4 import BeautifulSoup
from urls import login_urls
from config import email, password


class Login:

    def __init__(self, s):
        self.s = s

    def login(self):
        r = self.s.get(login_urls['get'])
        html = r.text
        soup = BeautifulSoup(html, 'html.parser')
        csrf_token = self._get_csrf_token(soup)
        values = {
            'utf8': '✓',
            'authenticity_token': csrf_token,
            'login[password]': password,
            'login[email]': email,
            'login[google_id_token]': '',
            'login[facebook_access_token]': ''
        }
        rl = self.s.post(login_urls['post'], data=values)
        if rl.status_code == 200:
            print("Logged in")
        else:
            print("Login failed")

    @staticmethod
    def _get_csrf_token(soup):
        return soup.select('meta[name="csrf-token"]')[0]['content']

