#from bs4 import BeautifulSoup
from BeautifulSoup import BeautifulSoup
import urllib2
import urllib
from bs4.element import NavigableString
import math
from google.appengine.api import memcache
import re

def getTeams(debug=False, save=False):
    #get standings and return soup    
    
    url = "http://www.tsn.ca/nhl/standings/?show=league"
    result = urllib2.urlopen(url)
    html = result.read()        

    return BeautifulSoup(html)

def getOdds(debug=False, save=False):
    #get odds and return soup
    
    url = 'http://proline.olg.ca/prolineEvents.do'
    form = {'selectedSportId':'HKY',
        'selectedTimeTab':'thisWeek',
        'language':'',
        'wagerSelect':'2'
        }
    data = urllib.urlencode(form)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    #parse error in html file so need to hack this up.
    #manually extract tables.
    #response = open('odds.html')
    html = parseProline(response)

    return BeautifulSoup(html)

def parseProline(response):
    #proline can't code HTML
    row = re.compile('.*<tr class="(even|odd)">', re.M | re.S )
    end = re.compile('.*</tr>', re.M | re.S)
    test = re.compile('.*<html>', re.M | re.S )


    scoop = False
    hand = ''
    dump = ''
    for line in response:
        if scoop:
            if end.match(line):
                scoop = False
                #drop in string
                dump += '<tr>'+hand+'</tr>'
                hand = ''
            else:
                #build string
                hand += line
        else:
            if row.match(line):
                scoop = True
    return dump

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
        self.name = data[1].a.string
        self.place = float(data[0].string)
        self.games = float(data[2].string)
        self.wins = float(data[3].string)
        self.losses = float(data[4].string)
        self.overtime = float(data[5].string)
        self.points = float(data[6].string)
        self.goals_for = float(data[7].string)
        self.goals_against = float(data[8].string)
        self.home = data[9].string
        self.away = data[10].string
        self.last = data[11].string
        self.streak = data[12].string
        self.nick = translate(self.name)

    def __repr__(self):
        return '%s (%s)' % (self.name, self.place)

def parseStandings(soup):
    table = soup.findAll('table')
    teams = {}
    rows = soup.table.findAll('tr')

    for row in rows[2:]: #thanks tsn for no tablebody!
        tds = [i for i in row.contents]
        if len(tds) > 2:
            teams[translate(tds[1].a.string)] = Team(tds)
        
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
    memcache.set('teams',teams, 60*60*6)    
    return teams

def parseOdds(soup):
    table = soup.findAll('tr')
    ODDS = []
    

    for i in table:
        if isinstance(i, NavigableString):
            print 'S'
        else:
            tds = i.findAll('td')
            if len(tds) > 5:
                #first row had few items     
                #row = [i.contents for i in tds]   #whole row stripped
                clean = []
                clean.append(tds[1].b.string)
                clean.append(tds[2].string.strip())
                clean.append(tds[3].b.string.strip())
                clean.append(tds[4].b.string)
                clean.append(tds[6].b.string)
                clean.append(tds[8].b.string)
                clean.append(tds[9].b.string)
                clean.append(tds[10].b.string)
                clean.append(tds[11].b.string)
                clean.append(tds[12].b.string)
                clean.append(tds[14].b.string)
                clean.append(tds[15].b.string)
                clean.append(tds[16].b.string)

                # print 'wtf'
                # #print 'WTF',row[3]
                # for i in row:
                #         print '*',i
                #         strings = []
                #         for s in i:
                #             strings.append(s)

                #         if len(strings) > 1:
                #             clean.append(strings[1])
                #         elif len(strings) == 1:
                #             clean.append(strings[0])
                # print '*'+clean
                
                ODDS.append(clean)
    memcache.set('odds',ODDS,60*60*6)
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
    def __init__(self,data, bettor):
        self.time = data[1]
        #self.sport = data[2]
        self.visitor = data[3]
        self.home = data[4]
        self.v_plus = float(data[5])
        self.v = float(data[6])
        self.tie = float(data[7])
        self.h = float(data[8])
        self.h_plus = float(data[9])
        self.over = float(data[10])
        self.over_under = float(data[11])
        self.under = float(data[12])

        self.bettor = bettor   #need to get teams from probet object
        teams = self.bettor.teams

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
        teams = self.bettor.teams

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

class Probet(object):
    def __init__(self):
        #set up the probet instance
        self.odds = memcache.get('odds')
        if not self.odds: self.odds = parseOdds(getOdds())

        self.teams = memcache.get('teams')
        if not self.teams: self.teams = parseStandings(getTeams())
       
        self.wagers = []

        for game in self.odds:
            self.wagers.append(Wager(game, self))

        self.wagers.sort(key=lambda x: x.odd_spread,reverse=True)

    def getWagers(self, top=None):
        return [[wager.favourite.nick, wager.dog.nick, int(wager.point_spread),wager.odd_spread, wager.plus] for wager in self.wagers[:top]]



