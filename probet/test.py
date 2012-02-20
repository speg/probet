from bs4 import BeautifulSoup
import urllib2
import urllib
from bs4.element import NavigableString
import math

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
        self.place = float(data[0].text)
        self.games = float(data[2].text)
        self.wins = float(data[3].text)
        self.losses = float(data[4].text)
        self.overtime = float(data[5].text)
        self.points = float(data[6].text)
        self.goals_for = float(data[7].text)
        self.goals_against = float(data[8].text)
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
        
    average_goals = 0.0
    average_allowed = 0.0
    average_points = 0.0
    games_played = 0.0

    for team in teams.values():
        average_points += team.points
        average_goals += team.goals_for
        average_allowed += team.goals_against
        games_played += team.games

    
    average_goals = average_goals
    average_points = average_points
    average_allowed = average_allowed

    stddev_goals = 0.0
    stddev_points = 0.0
    stddev_allowed = 0.0

    for team in teams.values():
        stddev_goals += math.pow(team.goals_for - average_goals,2)
        stddev_points += math.pow(team.points - average_points, 2)
        stddev_allowed += math.pow(team.goals_against - average_allowed, 2)

    stddev_goals = math.sqrt(stddev_goals/average_goals)
    stddev_points = math.sqrt(stddev_points/average_points)
    stddev_allowed = math.sqrt(stddev_allowed/average_allowed)

    teams['stats']={'avg_goals':average_goals/games_played,
                    'avg_points':average_points/games_played,
                    'avg_allowed':average_allowed/games_played,
                    'std_goals':stddev_goals/games_played,
                    'std_allowed':stddev_allowed/games_played,
                    'stddev_points':stddev_points/games_played,
                    }

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
        return '%s is %s points ahead of %s and is favoured by %s %s' % (self.favourite.name, int(self.point_spread), self.dog.name, self.odd_spread, '+' if self.plus else '')

    def determinePlus(self,fav,dog):
        #this is an attempt to determine if you should bet > +1
        if self.favourite == teams[self.visitor]:
            base = self.v
            plus = self.v_plus
        else:
            base = self.h
            plus = self.h_plus

        #determine if fav can score lots
        if fav.goals_for/fav.games < teams['stats']['avg_goals'] + teams['stats']['std_goals']*2:
            return False

        #determine if dog lets in a lot
        if dog.goals_against/dog.games < teams['stats']['avg_allowed'] + teams['stats']['std_allowed']*2:
            return False

        return True

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


