import requests


def check_status(url):
    re = requests.get(url)
    if 100 <= int(re.status_code) <= 499:
        return True
    return False
