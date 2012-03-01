#from bs4 import BeautifulSoup
from BeautifulSoup import BeautifulSoup
import urllib2
import urllib
from bs4.element import NavigableString
import math
from google.appengine.api import memcache
import re
import datetime
from google.appengine.ext import db

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
    table = re.compile('.*<tbody', re.M | re.S )
    table_end = re.compile('.*</table>', re.M | re.S)
    test = re.compile('.*<html>', re.M | re.S )


    scoop = False
    hand = ''
    dump = ''
    for line in response:
        if scoop:
            if table_end.match(line):
                scoop = False
                #drop in string
                dump += hand
                hand = ''
            else:
                #build string
                hand += line
        else:
            if table.match(line):
                scoop = True

    table = dump

    return table

    scoop = False
    hand = ''
    dump = ''
    for line in table:
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

    def setStatus(self, stats):
        if self.goals_for/self.games > stats['avg_goals']:
            #print self.goals_for/self.games, stats['avg_goals']
            self.scorer = True
        else:
            self.scorer = False

        if self.goals_against/self.games > stats['avg_goals']:
            self.loose = True
        else:
            self.loose = False

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

    for k,v in teams.items():
        if isinstance(v, Team):
            v.setStatus(teams['stats'])

    memcache.set('teams',teams, 60*60*6)    
    return teams

def parseOdds(soup):
    table = soup.findAll('tr')
    ODDS = []
    old = []
    known = []

    for i in table:
        if isinstance(i, NavigableString):
            pass
        else:
            tds = i.findAll('td')
            if len(tds) > 5:
                #first row had few items     
                #row = [i.contents for i in tds]   #whole row stripped

                clean = []
                clean.append(int(tds[1].b.string))
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
                clean.append(date)
                clean.append(event_list)
                

                if int(clean[0]) in known:
                    #do not add this
                    old.append(clean)
                else:
                    ODDS.append(clean)

            else:
                date = tds[0].span.string
                event_list = int(tds[0].contents[2].strip()[-4:])
                
                #get a list of previously recorded games
                r  = Wager.all()
                r.filter('event_list =',event_list)
                known_list = r.fetch(99)
                known = [g.game for g in known_list]

    return (ODDS, old)

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


class Wager(db.Model):
    game = db.IntegerProperty()
    time = db.StringProperty()
    sport = db.StringProperty()
    visitor = db.StringProperty()
    home = db.StringProperty()
    v_plus = db.FloatProperty()
    v = db.FloatProperty()
    tie = db.FloatProperty()
    h = db.FloatProperty()
    h_plus = db.FloatProperty()
    over = db.FloatProperty()
    over_under = db.FloatProperty()
    under = db.FloatProperty()
    date = db.StringProperty()
    event_list = db.IntegerProperty()


class create_Wager(object):

    def __init__(self,data, bettor, save=False):
        self.game = int(data[0])
        self.time = data[1]
        self.sport = data[2]
        self.visitor = data[3].strip()
        self.home = data[4].strip()
        self.v_plus = float(data[5])
        self.v = float(data[6])
        self.tie = float(data[7])
        self.h = float(data[8])
        self.h_plus = float(data[9])
        self.over = float(data[10])
        self.over_under = float(data[11])
        self.under = float(data[12])
        self.date = data[13].strip()
        self.list = int(data[14])

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
        self.bet_over_under = self.determineOverUnder()

        
        #store database object:
        if save:
            e = Wager(game=self.game, time=self.time, 
                sport = self.sport,
                visitor = self.visitor,
                home = self.home,
                v_plus = self.v_plus,
                v = self.v,
                tie = self.tie,
                h = self.h,
                h_plus = self.h_plus,
                over = self.over,
                over_under = self.over_under,
                under = self.under,
                date = self.date,
                event_list = self.list
            )
            e.put()


    def __repr__(self):
        return '%s is %s points ahead of %s and is favoured by %s %s' % (self.favourite.name, int(self.point_spread), self.dog.name, self.odd_spread, '+' if self.plus else '')

    def determineOverUnder(self):
        # 16 cases:
        # S = high scorer
        # s = low scorer
        # A = allows alot
        # a = allows little

        # fav    SA    Sa    sa    sA
        # dog    SA    Sa    sa    sA
        # O/U     O     -     U     -

        # fav    SA    Sa    sa    sA
        # dog    sA    SA    Sa    sa    
        # O/U     O     O     U     U

        # fav    SA    Sa    sa    sA
        # dog    sa    sA    SA    Sa       
        # O/U     -     O     -     U

        # fav    SA    Sa    sa    sA
        # dog    Sa    sa    sA    SA       
        # O/U     -     U     -     O 

        if self.favourite.scorer and self.dog.loose:
            return 1

        if not self.dog.loose and not self.favourite.scorer:
            return -1

        if not self.favourite.scorer and self.favourite.loose and self.dog.scorer and self.dog.loose:
            return 1

        return 0


    def determinePlus(self,fav,dog):
        #this is an attempt to determine if you should bet > +1
        teams = self.bettor.teams

        if self.favourite == teams[self.visitor]:
            base = self.v
            plus = self.v_plus
        else:
            base = self.h
            plus = self.h_plus

        if self.favourite.scorer and not self.favourite.loose and self.dog.loose:
            #works if dog is a scorer or not, risky?
            return True


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
        self.wagers = memcache.get('wagers')
        #self.wagers = None
        if not self.wagers:

            self.new, self.old = parseOdds(getOdds())
            
            self.teams = memcache.get('teams')
            if not self.teams: self.teams = parseStandings(getTeams())
           
            self.wagers = []

            for game in self.new:
                #save new games to the datastore
                self.wagers.append(create_Wager(game, self, True))
            for game in self.old:
                self.wagers.append(create_Wager(game, self))

            self.wagers.sort(cmp=self.sortWagers)

            memcache.set('wagers', self.wagers, 60*60*6)

    def getTeams(self):
        if not hasattr(self,'teams'):
            self.teams = parseStandings(getTeams())
        return self.teams

    def getWagers(self, top=None, risk=0):
        #top: number of wagers to get
        #risk: level of risk willing to take

        return [[wager.date, str(wager.game) + (' H' if wager.favourite.nick == wager.home else ' V'), wager.favourite.nick, wager.dog.nick, int(wager.point_spread),wager.odd_spread, wager.plus, wager.bet_over_under] for wager in self.wagers[:top] if self.risk(wager,risk)]

    def risk(self,wager,risk):
        if risk == 0:
            #conservative, safe, obvious
            if wager.odd_spread >= 1.0 and wager.point_spread >= 10:
                return True
        elif risk == 1:
            #still cautious
            if wager.odd_spread >= 0.5 and wager.point_spread > 5:
                return True

        elif risk == 5:
            #all the things!
            return True

        return False

    def sortWagers(self,x,y):
        #sort wagers by difference in odds, then by difference in standings
        if x.odd_spread < y.odd_spread:
            return 1
        elif y.odd_spread < x.odd_spread:
            return -1
        else:
            return int(y.point_spread - x.point_spread)



