import concurrent.futures
import time
from typing import List
import random

import requests
from bs4 import BeautifulSoup

import resources as res
from resources import Movie, Movielist

# Because of lazy load, for every movie need to make info request in form of
# GET 'https://letterboxd.com/ajax/poster/film/goldeneye/menu/linked/125x187/'


def req_movie_info(movie):
    img_width = movie['data-image-width']
    img_height = movie['data-image-height']
    target_link = movie['data-target-link']
    linked = movie['data-linked']
    menu = movie['data-menu']

    data = requests.get(res.LBXD_URL + f'/ajax/poster{target_link}{menu}/{linked}/{img_width}x{img_height}')

    return data.text if data.status_code == requests.codes.ok else None  # Returns HTML or None


def get_list_pages(user: str, list_name: str) -> int:
    """Gets the number of pages on somebodys list"""
    if list_name == 'watchlist':  # Watchlist has a different format for some fucking reason
        WL_URL = res.LBXD_URL + f'/{user}/watchlist'
    else:
        WL_URL = res.LBXD_URL + f'/{user}/list/{list_name}'

    # Start by only getting first page. From there get how many more pages there are, if any
    first_page = requests.get(WL_URL)

    if first_page.status_code == 200:  # Account exists
        return _get_list_pages_direct(first_page.text)
        # Directly get user watchlist length to save work
    else:
        print('Error user doesnt exist')
        return -1


def _get_list_pages_direct(page) -> int:
    """Helper function that takes html code of list page and gets the pages from it"""
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


def get_movies_on_page(page) -> List[Movie]:
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

            movie = Movie(name, release_year, id=id, img=img_src, link=f'{res.LBXD_URL}{link}')
            movies.append(movie)

    return movies


def get_page(url):
    """Gets the additional data for a movie"""
    with requests.get(url) as response:
        if response.status_code == 200:
            movies_on_page = get_movies_on_page(response.text)
            return movies_on_page
        else:
            print(f'Could not get data for page {url}')
            return []


def get_random_movie_from_page(user: str, list_name: str) -> Movie:
    start_time = time.time()
    """Gets the number of pages on a list watchlist"""
    pages = get_list_pages(user, list_name)  # Makes one request to start page
    if pages == -1:
        return None

    page = random.randint(1, pages)  # Either 1 or a random number

    if list_name == 'watchlist':  # Watchlist has a different format for some fucking reason
        WL_URL = res.LBXD_URL + f'/{user}/watchlist'
    else:
        WL_URL = res.LBXD_URL + f'/{user}/list/{list_name}'

    # Gets the random page. From there get how many more pages there are, if any
    page = requests.get(WL_URL)

    if page.status_code != 200:
        print('Error during request')
        return

    soup = BeautifulSoup(page.text, 'html.parser')
    # TODO this is probably where one could optimize. Need to know how many movies are on this page to skip this findall
    m_list = soup.find_all('div', class_='film-poster')  # Returns list containing html movies

    if not m_list:  # if there are no movies in the list
        return None

    # Get random html movie from list and get additional html for the chosen movie
    movie_html = req_movie_info(random.choice(m_list))

    soup = BeautifulSoup(movie_html, 'html.parser')
    div = soup.find('div')
    img = soup.find('img')
    a = soup.find('a')

    if div and img and a:  # If no null values
        id = div['data-film-id']
        name = div['data-film-name']
        release_year = div['data-film-release-year']
        img_src = img['src']
        link = a['href']

        movie = Movie(name, release_year, id=id, img=img_src, link=f'{res.LBXD_URL}{link}')
        print(f'Found random movie after {round(time.time() - start_time, 5)} seconds.')
        return movie


def get_watchlist(user: str, limit: int = 0) -> Movielist:
    """Returns  Movielist object containing movies and some functionality
    Limit > 0 means the list that gets returned at the end only has Limit movies in it.
    This is so the bot doesnt need to request every page every time
    check that classes documentation."""
    # TODO add random.shuffle(watchlist)  # So watchlist doesnt show same movies every time
    # Hard because loading from site is always the same and you would need to load all to shuffle
    movies_loaded = 0
    watchlist = Movielist(user=user, name="watchlist")

    start_time = time.time()

    WL_URL = res.LBXD_URL + f'/{user}/watchlist'

    # Start by only getting first page. From there get how many more pages there are, if any TODO
    first_page = requests.get(WL_URL)

    if first_page.status_code == 200:  # Account exists
        # Directly get user watchlist length to save work
        #wl_size = _get_watchlist_size_direct(first_page.text)
        pages = _get_list_pages_direct(first_page.text)

        # DEV Note: This leads to a req being made to the first page TWICE. Trying to fix it
        # List is not empty
        movies_on_page = get_movies_on_page(first_page.text)
        movies_loaded += len(movies_on_page)
        watchlist.extend(movies_on_page)

        # Load any additional pages if need be
        # If there are more pages and a limit was given, check if it hasnt been reached yet, otherwise check if no limit was set
        if pages > 1 and (limit != 0 and movies_loaded < limit) or limit < 1:
            # Use threads to load all the following pages at the same time.
            # These threads should create threads inside to load the images
            futures = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for page in range(2, pages + 1):
                    futures.append(executor.submit(get_page, WL_URL + f'/page/{page}'))

            watchlist_pages = [f.result() for f in futures]  # Wait for all the movies to be loaded
            for movies_on_page in watchlist_pages:
                movies_loaded += len(movies_on_page)
                watchlist.extend(movies_on_page)
                # Break if limit was reached or gone past (Usually it will go over it because a whole page is parsed)
                if limit > 0 and movies_loaded >= limit:
                    break

        print(f'{user}: {watchlist.length()} movies loaded from lbxd in {round(time.time() - start_time, 5)} seconds!')

        if limit > 0 and limit <= movies_loaded:  # If limit was given and isnt out of index, cut from list
            watchlist.set_movies(watchlist.get_movies(end=limit))
        return watchlist
    else:  # Account not exists
        print(f"Error: Account '{user}' does not exist!")
        return None


if __name__ == '__main__':
    user = 'l1chael'
    wl = get_watchlist(user)
    print(f"{wl.length()} - {wl.name} contains: {len(wl.get_movies())} movies")
