#! /usr/bin/python3.8

import couchdb
import feedparser
import argparse
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from abc import ABC
from datetime import datetime, timedelta


class HTMLFilter(HTMLParser, ABC):
    """

    A simple no dependency HTML -> TEXT converter.
    Usage:
          str_output = HTMLFilter.convert_html_to_text(html_input)
    """
    def __init__(self, *args, **kwargs):
        self.text = ''
        self.in_body = False
        self.is_script = False
        super().__init__(*args, **kwargs)

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() == "body":
            self.in_body = True
        elif tag.lower() == "script":
            self.is_script = True

    def handle_endtag(self, tag):
        if tag.lower() == "body":
            self.in_body = False
        elif tag.lower() == "script":
            self.is_script = False

    def handle_data(self, data):
        if self.in_body and not self.is_script:
            self.text += data

    @classmethod
    def convert_html_to_text(cls, html: str) -> str:
        f = cls()
        f.feed(html)
        return f.text.strip()           

#+++++++++++++++++++++++++++++++++++++++++
#
#
#
def rtn_page_text(url):

    req = Request(url)

    try:
        response = urlopen(req)
    except HTTPError as e:
        print('The server couldn\'t fulfill the request.')
        print('Error code: ', e.code)
    except URLError as e:
        print('We failed to reach a server.')
        print('Reason: ', e.reason)
    else:
        return HTMLFilter.convert_html_to_text(response.read().decode('utf-8')).replace('\n',' ').replace('\t','')
        


def readFeeds(feed_file, numdays, tags, keywords, inc_desc, terms):

    try:
        txt_file = open(feed_file, "r")
        feeds = txt_file.read().splitlines()
        db = db_init()

        for url in feeds:

            if url.startswith('#'): continue     # ignore comments in feed file
            
            feed = feedparser.parse(url)
            check_date = datetime.today() - timedelta(days=numdays)

            for post in feed.entries:

                postdate = datetime(post.published_parsed.tm_year, post.published_parsed.tm_mon, post.published_parsed.tm_mday)

                if postdate >= check_date:
                     date = "%d/%02d/%02d" % (post.published_parsed.tm_year,\
                     post.published_parsed.tm_mon, \
                     post.published_parsed.tm_mday)
                     try:
                          if (tags and check_tags(post.tags, terms)):
                               db_write(db, post, rtn_page_text(post.link))
                          elif (keywords and check_keywords(post.title, post.description, terms)):
                               db_write(db, post, rtn_page_text(post.link))
                     except:
                          print("Error writing")
    except:
         print("Error reading feed list.")

#
#  Check the post categories/tags for search terms
#  parms:
#                       categories (set)
#                       search terms (set)
#
def check_tags(post_tags, check_tags):
     found = False
     if check_tags[0] == '*':
         found = True
     else:
         try:
             for tag in post_tags:
                 if tag.term.lower() in check_tags:
                      found = True
         except:
             found = False
             print("Tag Error")
     return found


#
#  Check the post title and description for search terms
#  parms:
#                       title (string)
#                       description (string)
#                       search terms (set)
#
def check_keywords(title, description, keywords):
        found = False
        if keywords[0] == '*':
                found = True
        else:
                for word in keywords:
                        ltitle = title.lower()
                        ldesc = description.lower()
                        if ltitle.find(word) > 0:
                                found = True
                        elif ldesc.find(word) > 0:
                                found = True

        return found

#
#
#
#
def db_init():

    couch = couchdb.Server("http://feed:feed@localhost:5984")
    db = couch['feed_text']

    return db

#
#
#
#
def db_write(db, p, text):
 
    print(p.title)

    db.save({'date': p.published,
             "title": p.title, 
             "link": p.link,
             "desc": p.description,
             "text": text})


parser = argparse.ArgumentParser(
        description='Scan feeds in list for target tags and update feed datastore')
parser.add_argument('-i', '--input', help='file with feed list.', type=str, required=True)
parser.add_argument('-d', '--days', help='number of days to include.', type=str, required=False, default='1')

group1 = parser.add_mutually_exclusive_group(required=True)
group1.add_argument('-k', '--keywords', help='search text.', action="store_true", default=False)
group1.add_argument('-t', '--tags', help='search tags.', action="store_true", default=False)

parser.add_argument('--include-desc', help='include description', action="store_true", default=False)
parser.add_argument('terms', help='comma delimited list of terms, use "*" for all', type=lambda s: [str(item).lower() for item in s.split(',')])

args = parser.parse_args()

readFeeds(args.input, int(args.days), args.tags, args.keywords, args.include_desc, ((args.terms)))



