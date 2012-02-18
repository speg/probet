from bs4 import BeautifulSoup
import urllib2
import urllib
from bs4.element import NavigableString

url = "http://www.nhl.com/ice/m_standings.htm?type=LEA&season=20112012"
url = 'http://proline.olg.ca/prolineEvents.do'

form = {'selectedSportId':'HKY',
    'selectedTimeTab':'thisWeek',
    'language':'',
    'wagerSelect':'2'
    }
data = urllib.urlencode(form)

#req = urllib2.Request(url, data)
#response = urllib2.urlopen(req)
#the_page = response.read()
try:
  #result = urllib2.urlopen(url)
  html = open('odds.html')#result.read()
  soup = BeautifulSoup(html)
except urllib2.URLError, e:
  print e


def parseStandings(soup):
    table = soup.find_all('table')


    teams = {}


    for i in table[1].children:
        tds = i.find_all('td')
        #print tds[1].text.strip(), tds[6].text.strip()
        try:
            pts = int(tds[6].text.strip())
        except:
            pts = None

        teams[tds[1].text.strip()] = {'pts': pts}

    return teams

def parseOdds(soup):
    table = soup.find_all('table')
    ODDS = []
    for i in table[9].tbody.children:
        if isinstance(i, NavigableString):
            pass#print 'S'
        else:
            tds = i.find_all('td')
            if len(tds) > 5:
                #first row had few items
                #print tds[4].text.strip(), tds[5].text.strip(), tds[9].text.strip()
                odds = []
                for j, td in enumerate(tds):
                    s = td.stripped_strings
                    bj = []
                    for l in s:
                        bj.append(l)
                    if len(bj) > 1:
                        odds.append(bj[1])
                    elif len(bj) == 1:
                        odds.append(bj[0])
                ODDS.append([odds[4], odds[6], float(odds[8]), float(odds[10])])

            # for j, td in enumerate(tds):
            #     print '*',i, td.text.strip()
            #print tds[8].text.strip()
    return ODDS

odds = parseOdds(soup)


try:
  #result = urllib2.urlopen(url)
  html = open('data.html')#result.read()
  soup = BeautifulSoup(html)
except urllib2.URLError, e:
  print e

teams = parseStandings(soup)

#print odds
#print teams

favs = []
#for each game, find favourite:
for game in odds:
    if game[2] < game[3]:
        fav = game[0]
        dog = game[1]
    else:
        fav = game[1]
        dog = game[0]
    favs.append([fav, dog, abs(game[3]-game[2])])
    #the higher the differece, the more heavily favourited

favs.sort(key=lambda x: x[2],reverse=True)


for game in favs:
    #determine difference in standings of the two teams:
    if game[0] == 'LA': game[0] = 'LAK'
    if game[0] == 'CLB': game[0] = 'CBJ'
    if game[1] == 'LA': game[1] = 'LAK'
    if game[1] == 'CLB': game[1] = 'CBJ'
    if game[0] == 'TB': game[0] = 'TBL'
    if game[1] == 'TB': game[1] = 'TBL'
    if game[0] == 'WAS': game[0] = 'WSH'
    if game[1] == 'WAS': game[1] = 'WSH'
    pd = teams[game[0]].get('pts') - teams[game[1]].get('pts')
    print '%s leads %s by %s (%s)' % (game[0], game[1], pd,round(game[2],2))


