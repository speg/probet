from bs4 import BeautifulSoup
import urllib2

url = "http://www.nhl.com/ice/m_standings.htm?type=LEA&season=20112012"

try:
  result = urllib2.urlopen(url)
  html = open('data.html')#result.read()
  soup = BeautifulSoup(html)
except urllib2.URLError, e:
  print e

table = soup.find_all('table')


for i in table[1].children:
    tds = i.find_all('td')
    print tds[1].text.strip(), tds[6].text.strip()
    
