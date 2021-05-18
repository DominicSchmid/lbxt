from typing import List
LBXD_LOGO = 'https://i.imgur.com/qpz1mJ0.png'
LBXD_LOGO_WIDE = 'https://i.imgur.com/JchhRTf.png'
LBXD_URL = 'https://letterboxd.com'
DB_NAME = 'main.sqlite'
DISCORD_TOKEN = './static/discord_token.txt'
CMD_PREFIX = '.'  # TODO these alll need to go into a config outside
BOT_NAME = 'LBxt'


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
    def __init__(self, user=BOT_NAME, name="Movie List"):
        """List of movies that provides class operations. Optionally provide a name to your list"""
        self.movies = []
        self.name = str(name)
        self.user = str(user)

    def common_movies(movielists: List['Movielist']) -> 'Movielist':
        """Takes a list of Movielists and finds all common movies, which are then returned in a new Movielist"""
        if not movielists:  # Empty, or None
            return None
        if len(movielists) == 1:  # Only one element in list, return it
            return movielists[0]

        common_movies = Movielist(name='Common Movies')

        movielists.sort()  # Sort by length, shortest first
        base_list = movielists[0]
        other_movielists = movielists[1:]

        for movie in base_list.get_movies():
            for movielist in other_movielists:
                # Movie has to be in all lists so if its not in this one its definitely not in common
                if not movielist.contains_movie(movie):
                    continue
                common_movies.append(movie)

        return common_movies

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

    def get_movies(self, begin: int = 0, end: int = None) -> List[Movie]:
        if end and begin < end:
            return self.movies[begin:end]
        return self.movies  # getattr(self, 'movies')

    def set_movies(self, movies: List[Movie]):
        setattr(self, 'movies', movies)

    def join_movielist(self, other_movielist: 'Movielist' = None):
        self.movies.extend(other_movielist.get_movies)
        self.name + ", " + other_movielist.name
        self.user + ", " + other_movielist.user

    def append(self, movie: Movie):
        """Append a movie to the movielist"""
        return self.movies.append(movie)

    def extend(self, movies: List[Movie]):
        """Append a list of movies to the movielist"""
        self.movies.extend(movies)

    def length(self) -> int:
        """Returns the length of the contained movielist"""
        return len(self.movies)

    def contains_movie(self, movie: Movie) -> bool:
        return movie in self.movies

    def get_common_movies(self, other_movielists: List['Movielist']):
        common_movies = Movielist(name='Common Movies')

        for movie in self.movies:
            for movielist in other_movielists:
                # Movie has to be in all lists so if its not in this one its definitely not in common
                if not movielist.contains_movie(movie):
                    continue
                common_movies.append(movie)

        return common_movies

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
        return f"{self.user}'s list '{self.name}' with {len(self.movies)} movies"

    __repr__ = __str__
