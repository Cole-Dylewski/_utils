import time

import requests


def internet_test():
    url = "http://www.google.com"
    timeout = 5
    try:
        requests.get(url, timeout=timeout)
        return True
    except (requests.ConnectionError, requests.Timeout):
        # print("No internet connection...")
        time.sleep(5)
        return False


def fastAPI():
    url = "http://nginx/api/v2"
    timeout = 5
    try:
        request = requests.get(url, timeout=timeout)
        print(request.text)
        return True
    except (requests.ConnectionError, requests.Timeout):
        # print("No internet connection...")
        time.sleep(5)
        return False
