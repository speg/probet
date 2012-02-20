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





def translate(x):
    #translate proline abreviations to NHL ones.
    t = {   'Los Angeles':'LA',
            'Columbus':'CLB',
            'Tampa Bay':'TB',
            'Washington':'WAS',
            'San Jose':'SJ',
            'Nashville':'NAS',
            'New Jersey':'NJ',
            'Detroit':'DET',
            'Vancouver':'VAN',
            'NY Rangers':'NYR',
            'St. Louis':'STL',
            'Boston':'BOS',
            'Philadelphia':'PHI',
            'Pittsburgh':'PIT',
            'Chicago':'CHI',
            'Ottawa':'OTT',
            'Phoenix':'PHX',
            'Florida':'FLA',
            'Calgary':'CGY',
            'Toronto':'TOR',
            'Dallas':'DAL',
            'Colorado':'COL',
            'Winnipeg':'WPG',
            'Minnesota':'MIN',
            'Anaheim': 'ANA',
            'NY Islanders':'NYI',
            'Montreal':'MTL',
            'Buffalo':'BUF',
            'Carolina':'CAR',
            'Edmonton':'EDM'
    }

    return t.get(x,x)

class Team(object):


    def __init__(self,data):
        #initialize team from table data
        self.name = data[1].text
        self.place = int(data[0].text)
        self.games = int(data[2].text)
        self.wins = int(data[3].text)
        self.losses = int(data[4].text)
        self.overtime = int(data[5].text)
        self.points = int(data[6].text)
        self.goals_for = (data[7].text)
        self.goal_against = (data[8].text)
        self.home = data[9].text
        self.away = data[10].text
        self.last = data[11].text
        self.streak = data[12].text

    def __repr__(self):
        return '%s (%s)' % (self.name, self.place)




def parseStandings(soup):
    table = soup.find_all('table')
    teams = {}

    rows = soup.table.find_all('tr')
    for row in rows[2:]: #thanks tsn for no tablebody!
        tds = [i for i in row.children]       
        if len(tds) > 2:
            teams[translate(tds[1].text)] = Team(tds)

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

def printTeams(teams):
    print '#### Teams ####'
    standings = []

    for k,v in teams.items():
        standings.append('%s. %s' % (v.place,v.name))
    
    for x in sorted(standings): #not really sorted
        print x

DEBUG = True    #debug reads local files
SAVE = False    #save writes local files

odds = parseOdds(getOdds(save=SAVE, debug=DEBUG))
teams = parseStandings(getTeams(save=SAVE, debug=DEBUG))


#printOdds(odds)
#printTeams(teams)

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

    pd = teams[game[0]].points - teams[game[1]].points
    print '%s leads %s by %s (%s)' % (game[0], game[1], pd,round(game[2],2))


