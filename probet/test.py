from bs4 import BeautifulSoup
import urllib2
import urllib
from bs4.element import NavigableString


def getTeams(debug=False, save=False):
    #get standings and return soup
    
    if debug:
        html = open('teams.html').read()
    else:
        url = "http://www.tsn.ca/nhl/standings/?show=league"
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
                row = [i.stripped_strings for i in tds]   #whole row stripped
                clean = []
                for i in row:
                        strings = []
                        for s in i:
                            strings.append(s)

                        if len(strings) > 1:
                            clean.append(strings[1])
                        elif len(strings) == 1:
                            clean.append(strings[0])

                ODDS.append(clean)

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
        standings.append('%s. %s (%s)' % (v.place, v.name))
    
    for x in sorted(standings): #not really sorted
        print x

class Wager(object):
    def __init__(self,data):
        self.time = data[2]
        #self.sport = data[3]
        self.visitor = data[4]
        self.home = data[6]
        self.v_plus = float(data[7])
        self.v = float(data[8])
        self.tie = float(data[9])
        self.h = float(data[10])
        self.h_plus = float(data[11])
        self.over = float(data[12])
        self.over_under = float(data[13])
        self.under = float(data[14])

        #determine favourite and underdog:
        if self.h > self.v:
            self.favourite = teams[self.visitor]
            self.dog = teams[self.home]
        else:
            self.favourite = teams[self.home]
            self.dog = teams[self.visitor]

        self.odd_spread = abs(self.h - self.v)
        self.point_spread =  self.favourite.points - self.dog.points

        self.plus = self.determinePlus(self.favourite, self.dog)

    def __repr__(self):
        return '%s is %s points ahead of %s and is favoured by %s' % (self.favourite.name, self.point_spread, self.dog.name, self.odd_spread)

    def determinePlus(self,fav,dog):
        #this is an attempt to determine if you should bet > +1
        if self.favourite = teams[self.visitor]:
            base = self.v
            plus = self.v_plus
        else:
            base = self.h
            plus = self.h_plus

        fav_goals = fav.goals_for
        fav_against = fav.goal_against
        dog_goals = dog.goals_for
        dog_against = dog.goal_against

        #determine if fav can score lots

        #determine if dog lets in a lot




DEBUG = True    #debug reads local files
SAVE = False    #save writes local files

odds = parseOdds(getOdds(save=SAVE, debug=DEBUG))
teams = parseStandings(getTeams(save=SAVE, debug=DEBUG))


#printOdds(odds)
#printTeams(teams)



wagers = []

for game in odds:
    wagers.append(Wager(game))

wagers.sort(key=lambda x: x.odd_spread,reverse=True)

for wager in wagers:
    print wager


