import json
import logging
import ssl
import string
import urllib.request

from bs4 import BeautifulSoup

from constants import BASE_URL, PRIVACY_POLICY, STOP_WORDS, URL

ssl._create_default_https_context = ssl._create_unverified_context


logger = logging.getLogger(__name__)
logger.setLevel(level="DEBUG")
logger_format = logging.Formatter(
    "[%(asctime)s] :: %(levelname)s :: %(lineno)s :: %(message)s"
)
logger_stream = logging.StreamHandler()
logger_stream.setFormatter(logger_format)
logger.addHandler(logger_stream)


def get_list_all_external_resources(soup):
    resourses = []

    links = soup.find_all("link")
    for link in links:
        href = link.get("href")
        if href is not None and href.startswith("http") and BASE_URL not in href:
            resourses.append(href)

    scripts = soup.find_all("script")
    for script in scripts:
        src = script.get("src")
        if src is not None and src.startswith("http") and BASE_URL not in src:
            resourses.append(src)

    return resourses


def identifies_page_link(soup, target_title):
    a_links = soup.find_all("a")

    for a_link in a_links:
        a_title = a_link.get("title")

        if a_title and a_title.lower() == target_title:
            href = a_link.get("href")
            return href


def get_page_soup(url):
    response = urllib.request.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, "html.parser")
    return soup


def get_page_content(soup):
    content = soup.find("main", id="main")
    return content.get_text()


def process_page_content(content):
    stop_words = set(STOP_WORDS)

    content = "".join([el if ord(el) < 128 else " " for el in content])

    for el in string.punctuation:
        content = content.replace(el, " ")

    content = content.replace("\n", " ")
    content_words = content.lower().split()

    filtered_content_words = [w for w in content_words if not w in stop_words]

    map_words = {}

    for word in filtered_content_words:
        if len(word) < 2 or word.isdigit():
            continue
        if word in map_words:
            map_words[word] += 1
        else:
            map_words[word] = 1

    return map_words


def store_result(data):
    json_data = json.dumps(data)
    with open("output.json", "w") as f:
        f.write(json_data)


def main():
    try:
        logger.info("Script started")

        index_soup = get_page_soup(URL)
        external_resources = get_list_all_external_resources(index_soup)

        privacy_policy_link = identifies_page_link(index_soup, PRIVACY_POLICY)
        privacy_policy_soup = get_page_soup(URL + privacy_policy_link)
        privacy_policy_page_content = get_page_content(privacy_policy_soup)
        privacy_policy_words_map = process_page_content(privacy_policy_page_content)

        output_data = {
            "external_resources": external_resources,
            "privacy_policy_words_map": privacy_policy_words_map,
        }
        store_result(output_data)

        logger.info("Script finished")

    except Exception as e:
        logger.error(f"Script failed: {e}")


if __name__ == "__main__":
    main()
