import requests
import random
import re
import time
import threading
import string
import Queue
import multiprocessing
from bs4 import BeautifulSoup
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
from fake_useragent import UserAgent
from flask import Flask, render_template


app = Flask(__name__)
app.config['SECRET_KEY'] = '!qaz@wsx'


__author__ = "elgazarbenny at gmail.com"
__version__ = (0, 0, 1)
__copyright__ = "MIT"


def get_word_search_results(word):
    # [get_word_search_results] =>
    # /* Working to fetch the 1st place term result from google page. */
    # @returns:  dict of result with the following keys:
    #            Term, Title, Link, Description

    global ua
    retry = 0
    # Hidden value is generate a 15 chars long sequence to randomize the search.
    # This is some "Workaround" to allow high capacity of search before getting
    # Maximum tries exceed.
    hidden = "".join([random.choice(string.ascii_uppercase) for _ in xrange(15)])
    link = 'http://www.google.com/search?q=' + word + '&gws_rd=cr,ssl&ei=' + hidden
    # print ('Fetching search results for: ' + word)
    # Request the data using `get`
    with requests.Session() as s:
        r = requests.get(link, headers={'User-Agent': ua.google})
    # If the status code was different than 200.
    # We try to fake an User-agent in-order to complete the google data fetch.
    if r.status_code != 200:
        # Seted a count of 15 tries to pull it out.
        while retry != 15:
            retry += 1
            r = requests.get(link, headers={'User-Agent': ua.google})
            # If we did it we break and continue.
            if r.status_code == 200:
                break
        # Nothing help since status code is not 200 we are doomed to death
        if r.status_code != 200:
            raise Exception("Error code is not allow to fetch data: {}".format(r.status_code))
    # Using bs4 to get the request content.
    content = BeautifulSoup(r.text)
    # Fetching results. (description, title, link)
    result = content.find_all("h3", {"class": "r"})[0]
    result_descrip = content.find_all("div", {"class": "s"})[0]
    description = content.find_all("span", {"class": "st"})[0]

    try:
        url_link = content.findAll('cite', attrs={'class':'_Rm'})[0].text
    except IndexError as err:
        url_link = ''

    title = re.sub('<[^<]+?>', '', unicode(result))
    description = re.sub('<[^<]+?>', '', unicode(description))
    # Return a set of cleaned ready to display term result.

    return {"Term": unicode(word), "Title": unicode(title),
            "Link": url_link, "Description": unicode(description)}


def search_paths_generator(amount):
    # [search_paths_generator] =>
    # /* by the amount the user input, generate X words */
    # @returns:  words list.

    # source_site which holds a-lot of words.
    global words
    # In order to prevent another request everytime,
    # Once we fetch the words what we do is just random them again.
    # and get the needed amount of words by request.
    if not words:
        source_site = \
            "http://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text/plain"
        # request the data from the source_site.
        response = requests.get(source_site)
        # Since each word indicate new line we split it.
        words = response.content.splitlines()
        # Shuffle it and return the N number of words according request.
    random.shuffle(words)
    # return ready to post urls.
    return words[0: amount]


@app.route('/<int:cnt>')
def main(cnt):
    # [main] =>
    # /* by the amount the user input, set html page to be display */
    # /* with the results found. */
    # @returns:  render_template - ready html.

    # Catch start time.
    start = time.time()
    results_wallet = []
    random_words = search_paths_generator(cnt)
    pool = ThreadPool(processes=30)
    results_wallet = pool.map(get_word_search_results, random_words)
    pool.close()
    #p.close()
    # Catch done time
    end = time.time()
    return render_template('index.html', title="Result set",
                           results=results_wallet, total_time=(end - start))


if __name__ == '__main__':
    # [4 Cores Laptop tests]:
    # ** Note: All the results are rounded up.
    # >> 1000 requests => 210.0 sec.
    # >> 300 requests => 66.0 sec.
    # >> 150 requests => 36.0 sec.
    # >> 100 requests => 27.0 sec.
    # >> 50 requests => 12.0 sec.
    # >> 1 requests => 3.0 sec.
    words = None
    ua = UserAgent(cache=False)
    app.run(debug=True, port=8000)
