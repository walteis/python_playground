#!/usr/bin/python3.8 

'''
Purpose: 
	Reads a list of rss feeds and returns feed items that match given search terms

Version: 0.2

'''

import feedparser
import argparse
from datetime import datetime, timedelta


def getTermsFromFile(term_file):
	terms = list()
	try:
		txt_file = open(term_file, "r")
		terms = txt_file.read().splitlines()
	except:
		print("Error opening Search Terms file.")
		
	return terms
	
	

def readFeeds(feed_file, numdays, terms, inc_desc):
	
	# print output header
	print("<h1>News Roundup</h1> \n <h3>feed_reader v.1</h3>") 
	
	
	try:
		txt_file = open(feed_file, "r")
		feeds = txt_file.read().splitlines()
		
		check_date = datetime.today() - timedelta(days=numdays)
		print("<h4>For the period " + check_date.strftime("%A %d %B %Y") + " to " + datetime.today().strftime("%A %d %B %Y") + "</h4>")

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
						if (check_tags(post.tags, terms) or check_keywords(post.title, post.description, terms) ):
							print_post(post, inc_desc)
				
					except: 
						pass
	except:
		print("Error reading feed list.")

def getSmartTerms(feed_file, numdays):
	
	tag_set = dict()
	terms = list()
	try:
		txt_file = open(feed_file, "r")
		feeds = txt_file.read().splitlines()
		
		for url in feeds:		
			
			if url.startswith('#'): continue     # ignore comments in feed file
			
			feed = feedparser.parse(url)
			
			for post in feed.entries:
				#print(post.tags)
				for tag in post.tags:
					#tag_set.update({tag.term: 1})
					if tag.term.lower() in tag_set:
						x = tag_set.get(tag.term.lower())
						tag_set.update({tag.term.lower(): x+1})
					else:
						tag_set.update({tag.term.lower(): 1})
				    
	except:
		pass	
		
	#print(tag_set)	
	#clean out known bogus tags
	tag_set.pop("thumbnail")
	tag_set.pop("large")
	tag_set.pop("medium")
	tag_set.pop("full")
	out_dict = reversed(sorted(tag_set.items(), key = lambda kv:(kv[1], kv[0])))		
	for k,v in out_dict:
		if v > 3:
			terms.append(k)
				
	#print(terms)			
	return terms

#
#  Print the post
#  parms:
#		   	post (post object)
#			include description (bool)
#		
def print_post(p, desc):
	print('<h3><a target="_blank" href=' + p.link + '>' + p.title +'</a></h3>')
	if desc:
		try:
			print(p.description)
		except:
			pass
	
#
#  Check the post categories/tags for search terms
#  parms:
#		   	categories (set)
#			search terms (set)
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
#		   	title (string)
#			description (string)
#			search terms (set)
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
	

parser = argparse.ArgumentParser(
	description='Scan feeds in list for target tags')
parser.add_argument('-i', '--input', help='file with feed list.', type=str, required=True)
parser.add_argument('-d', '--days', help='number of days to include.', type=str, required=False, default='1')

group1 = parser.add_mutually_exclusive_group(required=True)
group1.add_argument('-t', '--terms', help='file with search terms.', type=str)
group1.add_argument('-s', '--smart-terms', help='use top terms found in feeds.', action="store_true", default=False)

parser.add_argument('--include-desc', help='include description', action="store_true", default=False)
#parser.add_argument('terms', help='comma delimited list of terms, use "*" for all', type=lambda s: [str(item).lower() for item in s.split(',')])

args = parser.parse_args()

if args.smart_terms == True:
	readFeeds(args.input, int(args.days), getSmartTerms(args.input, int(args.days)), args.include_desc)
else:
	readFeeds(args.input, int(args.days), getTermsFromFile(args.terms), args.include_desc)	

