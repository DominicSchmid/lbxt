import requests
import os

USERS = ["DomskiPlays", "Pablo0_", "L1chael", "EmilPvp1"]

CLIENT_ID = ''
CLIENT_SECRET = ''
OAUTH_TOKEN = ''
BASEURL = "https://logs.ivr.fi/"
#BASEURL = "http://localhost:8025/"

CHANNELS = []


def get_env():
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    OAUTH_TOKEN = os.getenv('OAUTH_TOKEN')


def get_tracked_channels():
    res = requests.get(BASEURL + "channels")
    jsres = res.json()
    channels = jsres["channels"]

    print(f"Tracking {len(channels)} channels.")
    return channels

# Find out in which streamer chats the user was active at least one time
# Returns a dict in the form of {user1: [channel1, channel2, ...], user2: [channel1, channel2, ...], ...}


def get_log_list(usernames: list[str]):
    data = {}
    for user in usernames:
        userid = _get_userid(user)
        logs = []
        for channel in CHANNELS:
            c = channel["name"]
            res = requests.get(BASEURL + "list", params={"userid": userid,
                                                         "channel": c}, headers={"Accept": "application/json"})
            if res.status_code == 200:
                res = res.json()
                logs.append(c)
                """print(logs)
                logs[c].extend(res["availableLogs"])"""
        data[user] = logs
    return data


def get_token():
    body = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        "grant_type": 'client_credentials'
    }
    r = requests.post('https://id.twitch.tv/oauth2/token', body)

    # data output
    keys = r.json()

    print(keys)

    return keys['access_token']


def _get_userid(username):
    # First, get newest oauth token
    if OAUTH_TOKEN:
        headers = {'Client-ID': CLIENT_ID, 'Authorization': 'Bearer ' + OAUTH_TOKEN}
    else:
        token = get_token()
        headers = {'Client-ID': CLIENT_ID, 'Authorization': 'Bearer ' + token}
        print(f"--- Requested new auth token: {token}")

    res = requests.get('https://api.twitch.tv/helix/users',  params={"login": username}, headers=headers)
    if res.status_code == 200:
        res = res.json()
        userid = res["data"][0]["id"]
        return str(userid)
    return ""


if __name__ == "__main__":
    CHANNELS = get_tracked_channels()
    logs = get_log_list(USERS)
    for user, channels in sorted(logs.items()):
        if(channels):
            print(f"{user} ({len(channels)}): {channels}")
