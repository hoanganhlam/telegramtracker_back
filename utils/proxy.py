import random
import uuid
import urllib.parse
import urllib.request
import codecs
import json

USER_AGENT = "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
EXT_VER = "1.164.641"
EXT_BROWSER = "chrome"
PRODUCT = "cws"
CCGI_URL = "https://client.hola.org/client_cgi/"
user_uuid = uuid.uuid4().hex


def get_proxies():
    user_uuid = uuid.uuid4().hex
    session_key = background_init(user_uuid)["key"]
    tunnels = zgettunnels(user_uuid, session_key, country="us")
    proxies = dict(tunnels)
    userName = "user-uuid-" + user_uuid
    password = proxies['agent_key']
    return "http://{}:{}@{}:{}".format(userName, password, next(iter(proxies['ip_list'].values())), 22223)


def background_init(user_uuid, *, timeout=10):
    post_data = encode_params({
        "login": "1",
        "ver": EXT_VER,
    }).encode('ascii')
    query_string = encode_params({
        "uuid": user_uuid,
    })
    resp = fetch_url(CCGI_URL + "background_init?" + query_string,
                     data=post_data,
                     timeout=timeout)
    return json.loads(resp)


def encode_params(params, encoding=None):
    return urllib.parse.urlencode(params, encoding=encoding)


def fetch_url(url, *, data=None, method=None, timeout=10):
    http_req = urllib.request.Request(
        url,
        data=data,
        headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(http_req, None, timeout) as resp:
        coding = resp.headers.get_content_charset()
        coding = coding if coding is not None else "utf-8-sig"
        decoder = codecs.getreader(coding)(resp)
        res = decoder.read()
    return res


def zgettunnels(user_uuid, session_key, country="us", *, limit=1, is_premium=0, timeout=10):
    qs = encode_params({
        "country": country + ".pool_lum_" + country + "_shared",
        "limit": limit,  # Number of response proxies
        "ping_id": random.random(),
        "ext_ver": EXT_VER,  # TODO: Expose to env
        "browser": EXT_BROWSER,
        "product": PRODUCT,
        "uuid": user_uuid,
        "session_key": session_key,
        "is_premium": is_premium,
    })
    resp = fetch_url(CCGI_URL + "zgettunnels?" + qs, timeout=timeout)
    return json.loads(resp)
