import cgi
import datetime
import webapp2
import jinja2
import os
import urllib2
import bs4
from bs4 import BeautifulSoup
from google.appengine.api import urlfetch
from probet import Probet

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class MainPage(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template('index.html')
        template_values = {'one':1}
        self.response.out.write(template.render(template_values))


class GetStandings(webapp2.RequestHandler):

    def get(self):
        #self.response.headers['Content-Type'] = 'text/plain'
        #self.response.out.write('Hello, webapp World!')
        url = "http://www.nhl.com/ice/m_standings.htm?type=LEA&season=20112012"
        #url = 'http://www.speg.com'

        #url = "http://www.google.com/"
        result = urllib2.urlopen(url)
        self.ParseResult(result.read())

    def ParseResult(self, x):
        #soup = BeautifulSoup(x.read())
        #print soup.prettify()
        template = jinja_environment.get_template('copy.html')
        template_values = {'page':x.decode('utf-8')}
        
        self.response.out.write(template.render(template_values))

class TodaysBets(webapp2.RequestHandler):
    def get(self):

        probet = Probet()

        template = jinja_environment.get_template('bets.html')
        template_values = {'bets':probet.getWagers()}        
        self.response.out.write(template.render(template_values))



app = webapp2.WSGIApplication([ ('/', MainPage),
                                ('/standings', GetStandings), 
                                ('/bets',TodaysBets)
                            ], 
                            debug=True)