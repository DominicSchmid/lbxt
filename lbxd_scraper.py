import time
import resources as res
from typing import List
from bs4 import BeautifulSoup
import requests
import concurrent.futures


# Because of lazy load, for every movie need to make info request in form of
# GET 'https://letterboxd.com/ajax/poster/film/goldeneye/menu/linked/125x187/'


def req_movie_info(movie):
    img_width = movie['data-image-width']
    img_height = movie['data-image-height']
    target_link = movie['data-target-link']
    linked = movie['data-linked']
    menu = movie['data-menu']

    data = requests.get(res.LBXD_URL + f'/ajax/poster{target_link}{menu}/{linked}/{img_width}x{img_height}')
    # print(f'Loaded info for {film_id}')

    return data.text if data.status_code == requests.codes.ok else None  # Returns HTML or None


def get_watchlist_pages(user: str) -> int:
    """Gets the number of pages on somebodys watchlist"""
    WL_URL = res.LBXD_URL + f'/{user}/watchlist'

    # Start by only getting first page. From there get how many more pages there are, if any
    first_page = requests.get(WL_URL)

    if first_page.status_code == 200:  # Account exists
        return _get_watchlist_pages_direct(first_page.text)
        # Directly get user watchlist length to save work
    else:
        print('Error user doesnt exist')
        return None


def _get_watchlist_pages_direct(page) -> int:
    """Helper function that takes html code of page and gets wl pages from it"""
    soup = BeautifulSoup(page, 'html.parser')
    pages = soup.find_all('li', class_='paginate-page')  # Get the list of pages

    if pages:  # The list is not empty, there is at least one page
        if len(pages) == 1:
            return 1
        soup = BeautifulSoup(str(pages[-1]), 'html.parser')  # Access last list element
        return int(soup.find('a').get_text())
    return 1  # 1 because this is direct, which means the site exists but on the first page no pages are displayed so it cant find it


def get_watchlist_size(user: str) -> int:
    """Returns the watchlist size or -1 if account does not exist"""

    WL_URL = res.LBXD_URL + f'/{user}/watchlist'
    # Start by only getting first page. From there get how many more pages there are, if any
    first_page = requests.get(WL_URL)

    if first_page.status_code == 200:  # Account exists
        return _get_watchlist_size_direct(first_page.text)
        # Directly get user watchlist length to save work
    else:
        print('Error user doesnt exist')
        return -1


def _get_watchlist_size_direct(page) -> int:
    """Returns the watchlist size or -1 on error (and maybe 0, needs to be tested)"""
    size = 0
    soup = BeautifulSoup(page, 'html.parser')
    wl_header = soup.find('div', class_='js-watchlist-content')  # Returns page of watchlist but containing html
    if wl_header:
        size = int(wl_header['data-num-entries'])
    return size


def get_movies_on_page(page) -> List[res.Movie]:
    """Takes the HTML movie list of a watchlist page and returns a list of Movies"""
    movies = []

    soup = BeautifulSoup(page, 'html.parser')
    m_list = soup.find_all('div', class_='film-poster')  # Returns list containing html movies

    if not m_list:  # if there are no movies in the watchlist
        return movies

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for m in m_list:
            futures.append(executor.submit(req_movie_info, m))

    return_values = [f.result() for f in futures]  # Wait for all the movies to be loaded

    for v in return_values:
        soup = BeautifulSoup(v, 'html.parser')
        div = soup.find('div')
        img = soup.find('img')
        a = soup.find('a')

        if div and img and a:  # If no null values
            id = div['data-film-id']
            name = div['data-film-name']
            release_year = div['data-film-release-year']
            img_src = img['src']
            link = a['href']

            movie = res.Movie(name, release_year, id=id, img=img_src, link=f'{res.LBXD_URL}{link}')
            # print(f'Loaded movie {movie}')
            movies.append(movie)

    return movies


def get_page(url):
    with requests.get(url) as response:
        if response.status_code == 200:
            movies_on_page = get_movies_on_page(response.text)
            return movies_on_page
        else:
            print(f'Could not get data for page {url}')
            return []


def get_watchlist(user: str, limit: int = 0) -> List[res.Movie]:
    """Returns a tuple (length, list) where:
    - length = watchlist length (-1 for no user found)
    - list = (empty) list (of movies)"""
    # TODO add random.shuffle(watchlist)  # So watchlist doesnt show same movies every time
    # Hard because loading from site is always the same and you would need to load all to shuffle
    movies_loaded = 0
    watchlist = []

    start_time = time.time()

    WL_URL = res.LBXD_URL + f'/{user}/watchlist'

    # Start by only getting first page. From there get how many more pages there are, if any TODO
    first_page = requests.get(WL_URL)

    if first_page.status_code == 200:  # Account exists
        # Directly get user watchlist length to save work
        wl_size = _get_watchlist_size_direct(first_page.text)
        pages = _get_watchlist_pages_direct(first_page.text)
        # DEV Note: This leads to a req being made to the first page TWICE. Trying to fix it

        if pages == 0 or wl_size == 0:
            print('EMPTY LIST???')  # TODO remove?
            return (wl_size, watchlist)

        # List is not empty
        movies_on_page = get_movies_on_page(first_page.text)
        movies_loaded += len(movies_on_page)
        watchlist.extend(movies_on_page)

        # Load any additional pages if need be
        # If there are more pages and a limit was given, check if it hasnt been reached yet, otherwise check if no limit was set
        if pages > 1 and (limit != 0 and movies_loaded < limit) or limit < 1:
            # Use threads to load all the following pages at the same time.
            # These threads should create threads inside to load the images
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for page in range(2, pages + 1):
                    futures.append(executor.submit(get_page, WL_URL + f'/page/{page}'))

            watchlist_pages = [f.result() for f in futures]  # Wait for all the movies to be loaded
            for movies_on_page in watchlist_pages:
                movies_loaded += len(movies_on_page)
                watchlist.extend(movies_on_page)
                # Break if limit was reached or gone past (Usually it will go over it because a whole page is parsed)
                if limit > 0 and movies_loaded >= limit:
                    break

        print(f'{len(watchlist)} movies successfully loaded from the site!')
        print(f'--- {time.time() - start_time} seconds')

        if limit > 0 and limit <= movies_loaded:  # If limit was given, splice watchlist
            watchlist = watchlist[:limit]
    else:
        print('Error: Account does not exist!')
        wl_size = -1

    return (wl_size, watchlist)


if __name__ == '__main__':
    user = 'l1chael'
    wl = get_watchlist(user)
    print(f"{wl[0]} - {user}'s watchlist contains: {len(wl[1])} movies")
