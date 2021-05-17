import resources as res
from typing import List
from bs4 import BeautifulSoup
import requests
import concurrent.futures


# Because of lazy load, for every movie need to make info request in form of
# GET 'https://letterboxd.com/ajax/poster/film/goldeneye/menu/linked/125x187/'


def lazy_load_movie(movie):
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


def get_watchlist(user: str, limit: int = -1) -> List[res.Movie]:
    # TODO add random.shuffle(watchlist)  # So watchlist doesnt show same movies every time
    # Hard because loading from site is always the same and you would need to load all to shuffle
    watchlist = []
    movies_loaded = 0

    for page in range(1, 100):  # Stop condition at 100 pages to not overload
        if movies_loaded >= limit and limit > 0:  # Because index begins at 0
            break
        data = requests.get(res.LBXD_URL + f'/{user}/watchlist/page/{page}')

        # Always returns 200 on success but html won
        if data.status_code == requests.codes.ok:
            # print(data)
            soup = BeautifulSoup(data.text, 'html.parser')
            m_list = soup.find_all('div', class_='film-poster')  # Returns page of watchlist but containing html
            # print(m_list[0])

            if not m_list:  # All movies loaded, page X has 0 more
                break

            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for m in m_list:
                    futures.append(executor.submit(lazy_load_movie, m))
                    movies_loaded += 1
                    if movies_loaded >= limit and limit > 0:  # If no movie load limit was set load ALL movies
                        break

            return_values = [f.result() for f in futures]
            return_values = [v for v in return_values if v]  # Remove Null elements

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
                    #img_width = img['width']
                    #img_height = img['height']
                    link = a['href']

                    movie = res.Movie(name, release_year, id=id, img=img_src, link=f'{res.LBXD_URL}{link}')
                    print(f'Loaded movie {movie}')
                    watchlist.append(movie)
                    #print(f"Loaded movie: {movie['name']} ({movie['release_year']})")

    print(f'{len(watchlist)} movies successfully loaded!')
    return watchlist
# with open('file.html', 'r') as html_file:


if __name__ == '__main__':
    wl = get_watchlist('l1chael', -1)
