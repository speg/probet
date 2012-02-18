import cgi
import datetime
import webapp2
import jinja2
import os
import urllib2
import bs4
from bs4 import BeautifulSoup

from google.appengine.api import urlfetch



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
        url = "http://www.nhl.com/ice/m_standings.htm"
        #url = 'http://www.speg.com'

        url = "http://www.google.com/"
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            self.ParseResult(result.content)

    def ParseResult(self, x):
        #soup = BeautifulSoup(x.read())
        #print soup.prettify()
        print x

app = webapp2.WSGIApplication([('/', MainPage),('/standings', GetStandings)],
                              debug=True)