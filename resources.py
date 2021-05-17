from typing import List
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

    def __eq__(self, other):
        """Compares two movies. Returns true if name and year are equal."""
        if not isinstance(other, Movie):
            return NotImplemented
        return (self.name.lower(), self.release_year) == (other.name.lower(), other.release_year)

    def __lt__(self, other):
        """Returns true if the other movie was released after this one"""
        if not isinstance(other, Movie):
            return NotImplemented
        return self.release_year < other.release_year

    def __str__(self) -> str:
        return f'{self.name} ({self.release_year})'


class Movielist(object):

    # To create movie you need at least year and name
    def __init__(self, movies: List[Movie] = None, name="Movie List"):
        """List of movies that provides class operations. Optionally provide a name to your list"""
        self.movies = []
        if movies:
            self.movies.extend(movies)  # Append
        self.name = name

    """def json(self):
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
            return None"""

    def get_movies(self):
        return self.movies  # getattr(self, 'movies')

    def append(self, movie: Movie):
        return self.movies.append(movie)

    def extend(self, movies: List[Movie]):
        return self.movies.extend(movies)

    def length(self):
        return len(self.movies)

    def get_overlapping_movies(self, other: 'Movielist'):
        pass

    def __eq__(self, other):
        """Compares two movieslists. Returns true if all their movies are equal."""
        if not isinstance(other, Movielist):
            return NotImplemented

        self.movies.sort()
        other.movies.sort()
        return self.movies == other.movies  # TODO check if this compares movies or not

    def __lt__(self, other):
        """Returns true if the other movielist is longer"""
        if not isinstance(other, Movielist):
            return NotImplemented
        return self.length() < other.length()

    def __str__(self) -> str:
        return f'{self.name} with {len(self.movies)} movies'
