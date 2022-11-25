import requests


def link_define(url):
    if url is None or type(url) is not str:
        return None
    # []
    if "facebook" in url:
        title = "Facebook"
    elif "twitter" in url:
        title = "Twitter"
    elif "telegram" in url:
        title = "Telegram"
    elif "t.me" in url:
        title = "Telegram"
    elif "youtube" in url:
        title = "Youtube"
    elif "tiktok" in url:
        title = "Tiktok"
    elif "reddit" in url:
        title = "Reddit"
    elif "medium" in url:
        title = "Medium"
    elif "discord" in url:
        title = "Discord"
    else:
        title = "Website"
    return {
        "url": url,
        "title": title
    }


def get_username(page):
    results = []
    re = requests.post(
        "https://esapi.ens.vision/api/search",
        headers={
            "authorization": "Bearer AwhzvoIBrzCTLANDVvMf"
        },
        json={
            "index": "name",
            "query": {
                "page": page, "pageSize": 100, "category": 38,
                "contains": "", "startsWith": "",
                "endsWith": "", "minLength": 0, "maxLength": 0,
                "regState": "valid",
                "sortBy": "startingPrice_decimal",
                "sortOrder": "asc", "priceMin": "",
                "priceMax": "", "buyout": "true",
                "unlisted": "false", "profile": "",
                "includeTags": [], "excludeTags": []
            }
        }
    )
    for item in re.json()["hits"]:
        results.append(item["_source"]["name"])
    if page < 5:
        results = results + get_username(page + 1)
    return results
