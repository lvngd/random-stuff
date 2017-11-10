import requests
from bs4 import BeautifulSoup
import re
import collections
import statistics


"""

My solution to the wikipedia challenge: the Path to Philosophy

https://en.wikipedia.org/wiki/Wikipedia:Getting_to_Philosophy

"""

PAGES_VISITED = []
PAGES_THAT_LOOP_OR_LEAD_NOWHERE = []
PAGES_THAT_LEAD_TO_PHILOSOPHY = []
#dict of paths to philosophy with key as a page and value as the path
PATHS_TO_PHILOSOPHY = {}


class WikiStreak:
	"""class to represent each streak of wikipedia pages crawled"""
	def __init__(self, start_url='http://en.wikipedia.org/wiki/Special:Randompage'):
		self.starting_point = start_url
		self.current_streak = []
		next_link = self.get_random_wiki_first_link(self.starting_point)
		self.current_streak.append(next_link)
		self.crawl(next_link)
		
	def crawl(self, next_link):
		while next_link:
			if next_link not in PAGES_VISITED:
				PAGES_VISITED.append(next_link)	
			bad_streak = False
			if next_link in PAGES_THAT_LOOP_OR_LEAD_NOWHERE:
				bad_streak = True
			elif next_link in PAGES_THAT_LOOP_OR_LEAD_NOWHERE:
				bad_streak = True
			elif next_link in PATHS_TO_PHILOSOPHY.keys():
				#already know this leads to philosophy
				self.update_philosophy_paths(PATHS_TO_PHILOSOPHY[next_link])
				break
			if bad_streak:
				#bad streak does not lead to philosophy
				#update list of pages that don't lead to philosophy to include earlier elements
				if len(self.current_streak) > 0:
					self.add_current_streak_to_pages_that_go_nowhere()
				break
			to_crawl = next_link
			next_link = self.get_random_wiki_first_link('https://en.wikipedia.org' + to_crawl)		
			if next_link in self.current_streak:
				self.add_current_streak_to_pages_that_go_nowhere()
				break
			if next_link is None:
				self.add_current_streak_to_pages_that_go_nowhere()
				break
			if next_link == '/wiki/Philosophy':
				self.current_streak.append(next_link)
				self.update_philosophy_paths()
				break
			else:
				self.current_streak.append(next_link)
		return

	def add_current_streak_to_pages_that_go_nowhere(self):
		"""when a next_link returns None, add the pages in the current streak to pages that do not end at philosophy"""
		for page in self.current_streak:
			if page not in PAGES_THAT_LOOP_OR_LEAD_NOWHERE:
				PAGES_THAT_LOOP_OR_LEAD_NOWHERE.append(page)
		return

	def update_philosophy_paths(self, previous_path=None):
		"""if the path will lead to philosophy or has led to it, add to successful paths"""
		for page in self.current_streak:
			if previous_path:
				current_streak_path = self.current_streak[self.current_streak.index(page):]
				path_to_philosophy = current_streak_path[:-1] + previous_path
			else:
				path_to_philosophy = self.current_streak[self.current_streak.index(page):]
			if page not in PAGES_THAT_LEAD_TO_PHILOSOPHY:
				PAGES_THAT_LEAD_TO_PHILOSOPHY.append(page)
			if page not in  PATHS_TO_PHILOSOPHY.keys():
				PATHS_TO_PHILOSOPHY[page] = path_to_philosophy
		return

	def get_random_wiki_first_link(self, url):
		"""get first non-italicized, non-parenthesized link in wikipedia page, else return None"""
		response = requests.get(url)
		soup = BeautifulSoup(response.text, 'html.parser')
		content_div = soup.find('div', {'id': 'mw-content-text'})
		if content_div:
			paragraphs = content_div.find_all('p')
			for paragraph in paragraphs:
				if paragraph.parent.name == 'td':
					#skip table paragraphs
					pass
				else:
					paragraph_without_parentheses = self.delete_parens(str(paragraph))
					paragraph = BeautifulSoup(paragraph_without_parentheses, 'html.parser')
					links = paragraph.find_all('a', href=True)
					for link in links:
						if str(link['href']).startswith('#cite_note'):
							pass
						elif link.img:
							pass
						elif link.parent.name == 'i':
							pass
						elif link.parent.name == 'span':
							pass
						else:
							return link['href']
		return None

	def delete_parens(self, test_string):
		"""
		takes a chunk of text and returns a new string
		with any text between parentheses removed -- except for parentheses that are part
		of a url

		"""
		count = 0
		opening = 0
		closing = 0
		has_url_parenthesis = False
		url_length = 0
		starting_paren = 0
		for char in test_string[count:]:
			balanced = False
			if char in ['(',')']:
				if char == '(':
					if starting_paren == 0:
						starting_paren = count 
					opening += 1
				if char == ')':
					closing += 1
					if opening == closing:
						#don't want to delete urls that have parentheses in the href
						if test_string[starting_paren-1] == '_':
							has_url_parenthesis = True
							url_length = len(test_string[starting_paren:count+1])
							
						else:
							test_string = test_string.replace(test_string[starting_paren:count+1],'')
							balanced = True
							new_test_str = self.delete_parens(test_string)
							return new_test_str
			else:
				pass
			if has_url_parenthesis:
				count = count + url_length
			else:
				count += 1
		return test_string


def get_statistics():
	total_pages_visited = len(PAGES_VISITED)
	total_pages_to_philosophy = len(PAGES_THAT_LEAD_TO_PHILOSOPHY)
	if '/wiki/Philosophy' in PAGES_VISITED:
		#most of the time we don't actually visit the Philosophy page, but if it 
		#was visited then count it as a path
		func = [len(value) for key,value in PATHS_TO_PHILOSOPHY.items()]
	else:
		func = [len(value) for key,value in PATHS_TO_PHILOSOPHY.items() if len(value) != 1]
		total_pages_to_philosophy = total_pages_to_philosophy - 1
	percent_pages_that_lead_to_philosophy = total_pages_to_philosophy / total_pages_visited
	print("percent pages that lead to philosophy {}".format(str(percent_pages_that_lead_to_philosophy)))
	func.sort()
	counter = collections.Counter(func)
	print("path length distribution")
	for key,value in counter.items():
		print("path length: {}, frequency: {}".format(key,value))
	average_path_length = statistics.mean(func)
	print("average path length {}".format(str(average_path_length)))
	median_path_length = statistics.median(func)
	print("median path length {}".format(str(median_path_length)))
	try:
		mode_path_length = statistics.mode(func)
		print("mode {}".format(str(mode_path_length)))
	except statistics.StatisticsError:
		print("no mode")
	standard_deviation = statistics.pstdev(func)
	print("standard deviation: {} ".format(str(standard_deviation)))
	return
	



if __name__=='__main__':
	while len(PAGES_VISITED) < 500:
		print("PAGES VISITED {}".format(str(len(PAGES_VISITED))))
		WikiStreak()
	get_statistics()
	
	