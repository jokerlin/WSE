from revision_crawler import RevisionCrawler
import sys
sys.stdout=open('log','w')
crawler = RevisionCrawler(urls=['https://en.wikipedia.org/w/index.php?title=Reverse_engineering&action=history'])
crawler.start()
