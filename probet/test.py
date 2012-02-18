from bs4 import BeautifulSoup
import urllib2
import urllib
from bs4.element import NavigableString


def getTeams(debug=False, save=False):
    #get standings and return soup
    
    if debug:
        html = open('teams.html').read()
    else:
        url = "http://www.nhl.com/ice/m_standings.htm?type=LEA&season=20112012"
        result = urllib2.urlopen(url)
        html = result.read()

    if save:
        f = open('teams.html','w')
        f.write(html)
        f.close()

    return BeautifulSoup(html)

def getOdds(debug=False, save=False):
    #get odds and return soup
    
    if debug:
        html = open('odds.html').read()
    else:
        url = 'http://proline.olg.ca/prolineEvents.do'
        form = {'selectedSportId':'HKY',
            'selectedTimeTab':'thisWeek',
            'language':'',
            'wagerSelect':'2'
            }
        data = urllib.urlencode(form)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        html = response.read()
    
    if save:
        f = open('odds.html','w')
        f.write(html)
        f.close()

    return BeautifulSoup(html)



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

def translate(x):
    #translate proline abreviations to NHL ones.
    t = {   'LA':'LAK',
            'CLB':'CBJ',
            'TB':'TBL',
            'WAS':'WSH',
            'SJ':'SJS',
            'NAS':'NSH',
            'NJ':'NJD'
    }

    if x in t: x = t[x]

    return x

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
                ODDS.append([translate(odds[4]), translate(odds[6]), float(odds[8]), float(odds[10]),float(odds[7]),float(odds[11])])

            # for j, td in enumerate(tds):
            #     print '*',i, td.text.strip()
            #print tds[8].text.strip()
    return ODDS

def printOdds(odds):
    #pretty print of odds table
    #currentley: visitor, home, v, h, v+, h+
    print '### PROBET PROLINE ###'
    print ''
    print 'Visitor\tHome\tV\tH\tV+\tH+'
    for i in odds:
        print '%s\t%s\t%s\t%s\t%s\t%s' % tuple(i)



DEBUG = True    #debug reads local files
SAVE = False    #save writes local files

odds = parseOdds(getOdds(save=SAVE, debug=DEBUG))
teams = parseStandings(getTeams(save=SAVE, debug=DEBUG))


printOdds(odds)


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

    pd = teams[game[0]].get('pts') - teams[game[1]].get('pts')
    print '%s leads %s by %s (%s)' % (game[0], game[1], pd,round(game[2],2))


