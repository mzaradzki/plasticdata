
from google.appengine.ext import db as models
from google.appengine.api.users import User
from geo.geomodel import GeoModel

import datetime
import urllib2, urlparse
import codecs
from BeautifulSoup import BeautifulSoup



def stringtotable(tablestr):
    table = []
    for rowstr in tablestr.split('##')[0:-1]:
        table.append(rowstr.split('#'))
    return table

multipliers = { 'K':1000., 'M':1000000., 'B':1000000000., 'T':1000000000000. }

def stringtofloat(fstr):
    try:
        return float(fstr)
    except:
        try:
            return float(fstr[0:-1])*multipliers[str(fstr[-1]).upper()]
        except:
            return 'na'


def onelineadress(country='France', state=None, city='Nice', zipcode='06000', adress='4 avenue de verdun'):
    if not(state in [None,'None','']):
        raise ValueError('not handled yet')
    else:
        return adress+', '+zipcode+' '+city+', '+country


DEFAULTLOCATION = models.GeoPt(10, 10)

class GeoAdress(GeoModel):

    city = models.StringProperty(default='')
    country = models.StringProperty(default='')
    state = models.StringProperty(default='')
    zipcode = models.StringProperty(default='')
    adress = models.StringProperty(default='')

    def put(self):
        fulladress = onelineadress(self.country, self.state, self.city, self.zipcode, self.adress)
        webadress = 'http://maps.googleapis.com/maps/api/geocode/xml?address='+fulladress.replace(' ','+')+'&sensor=false'
        pagehtml = codecs.getreader('latin1')(urllib2.urlopen(webadress))
        soup = BeautifulSoup(pagehtml)
        geometry = soup.findAll('geometry')[0]
        lng = float(geometry.findAll('lng')[0].text)
        lat = float(geometry.findAll('lat')[0].text)
        self.location = models.GeoPt(lat, lng)
        self.update_location()
        super(GeoAdress,self).put()


class Document(models.Model):

    name = models.StringProperty(default='')
    blob = models.BlobProperty(default='')


class Gallery(models.Model):

    #slug = models.SlugField()
    #category = models.ForeignKey(Category)
    #markdown_content = models.TextField()
    name = models.StringProperty(default='')
    city = models.StringProperty(default='')
    country = models.StringProperty(default='')
    state = models.StringProperty(default='')
    zipcode = models.StringProperty(default='')
    adress = models.StringProperty(default='')
    webadress = models.StringProperty(default='')
    emailadress = models.StringProperty(default='')
    #created = models.DateTimeProperty(auto_now_add=True)
    modified = models.DateTimeProperty(auto_now=True)

    def getNetloc(self):
        return urlparse.urlparse(self.webadress).netloc

    def put(self):
        
        if not('' in [str(self.country),str(self.city),str(self.zipcode),str(self.adress)]) and not('None' in [str(self.country),str(self.city),str(self.zipcode),str(self.adress)]):
            q = GeoAdress.all()
            q.filter('country =', self.country)
            q.filter('state =', self.state)
            q.filter('city =', self.city)
            q.filter('zipcode =', self.zipcode)
            q.filter('adress =', self.adress)
            if (q.get() is None):
                ga = GeoAdress(location=DEFAULTLOCATION, country=self.country, state=self.state, city=self.city, zipcode=self.zipcode, adress=self.adress)
                ga.put()
        
        if str(self.webadress).startswith('http://'):
            q = WebPage.all()
            q.filter('crawlrooturl =', self.webadress)
            q.filter('url =', self.webadress)
            if (q.get() is None):
                webpage = WebPage(url=self.webadress, crawlrooturl=self.webadress)
                webpage.put()
        super(Gallery,self).put()


class Image(models.Model):

    gallery = models.ReferenceProperty(Gallery)
    url = models.StringProperty(default='')
    netloc = models.StringProperty(default='') # auto-set when saving down the object
    sourcepageurl = models.StringProperty(default='')
    status = models.StringProperty(choices=set(['toReview','toShow','toHide']), default='toReview')
    created = models.DateTimeProperty(auto_now_add=True)

    def put(self):
        self.netloc = urlparse.urlparse(self.url).netloc
        super(Image,self).put()


class WebPage(models.Model):

    url = models.StringProperty(default='')
    netloc = models.StringProperty(default='') # auto-set when saving down the object
    urllength = models.IntegerProperty() # auto-set when saving down the object
    crawlrooturl = models.StringProperty(default='')
    crawled = models.BooleanProperty(default=False)
    imagecount = models.IntegerProperty(default=0)
    scrapped = models.BooleanProperty(default=False)
    created = models.DateTimeProperty(auto_now_add=True)

    def put(self):
        self.netloc = urlparse.urlparse(self.url).netloc
        self.urllength = len(str(self.url))
        super(WebPage,self).put()


