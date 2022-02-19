import requests
from bs4 import BeautifulSoup
from time import sleep

x = 0
while True:
    if x == 0:
        url = "https://news.ycombinator.com/newest"
    else:
        url = "https://news.ycombinator.com/newest" + next_page[6:]
    request = requests.get(url)
    r = requests.get(url)

    if r.status_code != 200:
        y = 0
        while y < 3:
           print("URL: {} Status code is {}, waiting 5 seconds and try again".format(
               url, r.status_code))
           sleep(5)  # wait for 5 seconds before trying to fetch again
           r = requests.get(url)
           y = y + 1

    soup = BeautifulSoup(r.text, "html.parser")

    topics = soup.find_all('td', class_='title')
    for topic in topics:
        topic = topic.find("a", {'class': 'titlelink'})
        if topic is not None and 'github.com' in str(topic):
            sublink = topic.get('href')
            print(str(topic.text) + "  " + str(sublink))
            print("===")

    next_link = soup.find("a", {'class': 'morelink'})
    next_page = next_link.get('href')
    x = x+1
