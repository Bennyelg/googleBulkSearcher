import requests
import random
import re
import time
import string
import multiprocessing
from bs4 import BeautifulSoup
from multiprocessing import Pool
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

    # Hidden value is generate a 15 chars long sequence to randomize the search.
    # This is some "Workaround" to allow high capacity of search before getting
    # Maximum tries exceed.
    hidden = "".join([random.choice(string.ascii_uppercase) for _ in xrange(15)])
    link = 'http://www.google.com/search?q=' + word + '&gws_rd=cr,ssl&ei=XesHV7-' + hidden
    # print ('Fetching search results for: ' + word)
    # Request the data using `get`
    with requests.Session() as s:
        r = requests.get(link)
    if r.status_code != 200:
        raise Exception("Error code is not allow to fetch data: {}".format(r.status_code))
    else:
        # Using bs4 to get the request content.
        content = BeautifulSoup(r.text)
        # Fetching results. (description, title, link)
        result = content.find_all("h3", {"class": "r"})[0]
        result_descrip = content.find_all("div", {"class": "s"})[0]
        description = result_descrip.find_all("span", {"class": "st"})[0]
        # Get the link from the description.
        for link in result_descrip.findAll('a'):
            link = link.get('href')
            break
        # Clean-ups.
        # - Cleanups is simply to clean-up un-needed tags,
        #   such html tags and non readable tags.
        try:
            title = re.sub('<[^<]+?>', '', unicode(result))
            try:
                link = unicode(link.replace('/url?q=', '')).split('://')[2]
            except IndexError as ind_err:
                link = unicode(link.replace('/url?q=', '')).split('://')[1]
            link = link.split('%')[0]
            description = re.sub('<[^<]+?>', '', unicode(description))
            # Return a set of cleaned ready to display term result.
            return {"Term": unicode(word), "Title": unicode(title),
                    "Link": link, "Description": unicode(description)}
        except Exception as parse_err:
            pass


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
    # Create the processes pool according to the machine cpu count.
    # Since multi-threading is not a good option to use in python.
    # I selected a multiprocessing module knowing we got a little bit overhead
    # when setting-up the processes.
    p = Pool(processes=multiprocessing.cpu_count())
    # Get the random words from the site by the cnt value the user selected.
    random_words = search_paths_generator(cnt)
    # mapping the work throw processes and return mid result set.
    result_set = p.map(get_word_search_results, random_words)
    # p.join()
    # Catch done time
    end = time.time()
    return render_template('index.html', title="Result set",
                           results=result_set, total_time=(end - start))


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
    app.run(debug=True, port=8000)
