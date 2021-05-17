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
    #print(f'Loaded info for {film_id}')

    return data.text if data.status_code == requests.codes.ok else None  # Returns HTML or None


def get_watchlist_size(user: str) -> int:
    """Returns the watchlist size or -1 on error (and maybe 0, needs to be tested)"""
    size = -1
    data = requests.get(res.LBXD_URL + f'/{user}/watchlist')
    soup = BeautifulSoup(data.text, 'html.parser')
    wl_header = soup.find('div', class_='js-watchlist-content')  # Returns page of watchlist but containing html
    if wl_header:
        size = int(wl_header['data-num-entries'])
    return size


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
    return 0


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
            #print(f'Loaded movie {movie}')
            movies.append(movie)

    return movies


def get_watchlist(user: str, limit: int = 0) -> List[res.Movie]:
    # TODO add random.shuffle(watchlist)  # So watchlist doesnt show same movies every time
    # Hard because loading from site is always the same and you would need to load all to shuffle
    watchlist = []
    movies_loaded = 0

    start_time = time.time()

    WL_URL = res.LBXD_URL + f'/{user}/watchlist'

    # Start by only getting first page. From there get how many more pages there are, if any TODO
    first_page = requests.get(WL_URL)

    if first_page.status_code == 200:  # Account exists
        # Directly get user watchlist length to save work
        pages = _get_watchlist_pages_direct(first_page.text)

        if pages > 0:
            movies_on_page = get_movies_on_page(first_page.text)
            movies_loaded += len(movies_on_page)
            watchlist.extend(movies_on_page)

            if pages > 1 and (limit != 0 and movies_loaded < limit) or limit == 0:  # Load any additional pages
                for page in range(2, pages + 1):  # because range does not include last element but we need to read page 6
                    data = requests.get(WL_URL + f'/page/{page}')
                    if data.status_code == 200:
                        movies_on_page = get_movies_on_page(data.text)
                        movies_loaded += len(movies_on_page)
                        watchlist.extend(movies_on_page)
                        # Break if limit was reached or gone past (Usually it will go over it because a whole page is parsed)
                        if limit > 0 and movies_loaded >= limit:
                            break
                    else:
                        print(f'Could not get data for page {page}')
        else:
            print('EMPTY LIST???')
    else:
        print('Error: Account does not exist!')
        return None

    print(f'{len(watchlist)} movies successfully loaded from the site!')
    print(f'--- {time.time() - start_time} seconds')

    if limit > 0 and limit <= movies_loaded:
        return watchlist[:limit]
    else:
        return watchlist
# with open('file.html', 'r') as html_file:


if __name__ == '__main__':
    user = 'l1chael'
    print(f"{user}'s watchlist contains: {len(get_watchlist(user, -1))} movies")
