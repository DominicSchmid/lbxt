LBXD_LOGO = 'https://i.imgur.com/qpz1mJ0.png'
LBXD_URL = 'https://letterboxd.com'
DB_NAME = 'main.sqlite'
DISCORD_TOKEN = './static/discord_token.txt'
CMD_PREFIX = '.'  # TODO these alll need to go into a config outside


class Movie(object):

    # To create movie you need at least year and name
    def __init__(self, name: str, release_year: str or int, id: int = -1, img: str = None, link: str = None):
        """Movie object. Must provide name and release year.

        You can add an image dict: `{ 'src': img_src, 'width': img_width, 'height': img_height }`"""
        self.name = name
        self.release_year = release_year
        self.id = id
        self.img = img
        self.link = link
        if not self.json():
            raise ValueError(f'Your movie parameters are wrong. {name} ({release_year})')

    def json(self):
        try:
            return {
                'id': self.id,
                'name': self.name,
                'release_year': self.release_year,
                'img': self.img,
                'link': self.link
            }
        except Exception as e:
            print(e)
            return None

    def __str__(self) -> str:
        return f'{self.name} ({self.release_year})'
