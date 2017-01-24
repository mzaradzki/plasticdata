
from google.appengine.ext import db as models
from google.appengine.api.users import User
#from google.appengine.ext.models import User
from geo.geomodel import GeoModel

import datetime
import urllib2, urlparse
import codecs
from BeautifulSoup import BeautifulSoup



#from htmlutils import htmlForTextInput, htmlForReadOnlyTextField, htmlForReadOnlyDateTimeField, htmlForSelectInput, htmlForTextArea, htmlForContentEdition
#from htmlutils import htmlForDateInput, htmlForReadOnlyDateField


#STORY_STATUS_CHOICES = ['Needs Edit','Needs Approval','Published','Archived']

#LANGUAGE_CHOICES = ['French','English']

class StockStory(models.Model):

    hashedurl = models.StringProperty()
    #slug = models.SlugField()
    #category = models.ForeignKey(Category)
    #markdown_content = models.TextField()
    content = models.TextProperty()
    #owner = models.UserProperty(auto_current_user_add=True)
    #status = models.StringProperty(choices=set(STORY_STATUS_CHOICES), default='Needs Edit')
    #language = models.StringProperty(choices=set(LANGUAGE_CHOICES), default='French')
    #created = models.DateTimeProperty(auto_now_add=True)
    #modified = models.DateTimeProperty(auto_now_add=True)

    '''
    def fieldsForView(self):
        return [
                ('id', htmlForReadOnlyTextField('id', str(self.key().id()))),
                ('owner', htmlForReadOnlyTextField('owner', self.owner.email())),
                ('title', htmlForReadOnlyTextField('title', self.title)),
                ('content', htmlForTextArea('content', self.content, True)),
                ('status', htmlForReadOnlyTextField('status', self.status)),
                ('language', htmlForReadOnlyTextField('language', self.language)),
                #('created', htmlForReadOnlyDateTimeField('created', self.created)),
                ('created', htmlForReadOnlyDateField('created', self.created)),
                #('modified', htmlForReadOnlyDateTimeField('modified', self.modified)),
                ('modified', htmlForReadOnlyDateField('modified', self.modified)),
                ]

    def fieldsForEdit(self):
        return [
                ('id', htmlForReadOnlyTextField('id', str(self.key().id()))),
                ('title', htmlForTextInput('title', self.title)),
                ('content', htmlForContentEdition(self.content)),
                ('status', htmlForSelectInput('status', STORY_STATUS_CHOICES)),
                ('language', htmlForSelectInput('language', LANGUAGE_CHOICES)),
                ]
    '''


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

    '''
    def refresh(self, full=False):
        ftrs = ['quote','marketcap','cash','debt','pe_trailing','quaterly_earning_growth','quaterly_revenue_growth','return_on_equity','dividendtableasstring']
        if (self.lasthighlowobsevationage()>=31):
            ftrs+= ['hltableasstring']
        if full:
            ftrs+= ['name','sector','industry','brief']
        for fieldname in ftrs:
            setattr(self, fieldname, None)
        self.scrap()

    def scrap(self):
        if (self.sector is None):
            try:
                sectorinfo = sector(self.moniker)
                self.sector = sectorinfo['sector']
            except:
                self.sector = 'na'
        if (self.industry is None):
            try:
                sectorinfo = sector(self.moniker)
                self.industry = sectorinfo['industry']
            except:
                self.industry = 'na'
        if (self.name is None):
            try:
                self.name = getprofile(self.moniker)['name']
            except:
                self.name = 'na'
        if (self.brief is None):
            try:
                self.brief = getprofile(self.moniker)['brief']
            except:
                self.brief = 'na'
        for fieldname in ['quote','marketcap','cash','debt','pe_trailing','quaterly_earning_growth','quaterly_revenue_growth','return_on_equity']:
            if (getattr(self,fieldname) is None):
                try:
                    setattr(self, fieldname, str(kstats(str(self.moniker))[fieldname]))
                except:
                    setattr(self, fieldname, 'na')
        if (self.hltableasstring is None):
            try:
                table = HL2yr(str(self.moniker))
                strtable = ''
                for a, b, c in table:
                    strtable+= str(a)+'#'+str(b)+'#'+str(c)+'##'
                self.hltableasstring = strtable
            except:
                self.hltableasstring = 'na'
        if (self.dividendtableasstring is None):
            try:
                table = dividends(str(self.moniker))
                strtable = ''
                for a, b in table:
                    strtable+= str(a)+'#'+str(b)+'##'
                self.dividendtableasstring = strtable
            except:
                self.dividendtableasstring = 'na'
        self.put()
            
    def get(self, fieldname='quote'):
        try:
            if not(getattr(self, fieldname) is None):
                return getattr(self, fieldname)
            else:
                raise
        except:
            self.scrap()
            return getattr(self, fieldname)

    def lasthighlowobsevationage(self):
        try:
            hltable = stringtotable(self.get('hltableasstring'))
            datestr = [str(a) for a,b,c in hltable][0]
            mdstr, ystr = datestr.split(', ')
            mstr, dstr = mdstr.split(' ')
            return (datetime.date.today() - datetime.date(int(ystr), monthmapper(mstr.lower()), int(dstr))).days
        except:
            return 0

    def distancetobounds(self):
        try:
            hltable = stringtotable(self.get('hltableasstring'))
            ratiobot = min([float(b) for a,b,c in hltable]+[float(self.get('quote'))])/float(self.get('quote'))
            ratiotop = max([float(c) for a,b,c in hltable]+[float(self.get('quote'))])/float(self.get('quote'))
            return [int((ratiotop-1.)*100.), int((ratiobot-1.)*100.)]
        except:
            return ['na', 'na']

    def nextdividenddate(self):
        try:
            divtable = stringtotable(self.get('dividendtableasstring'))
            return [a.split(',')[0] for a, b in divtable if ('2011' in a)][-1]
        except:
            return 'na'

    def previousyeardividend(self):
        try:
            divtable = stringtotable(self.get('dividendtableasstring'))
            return sum([float(b) for a, b in divtable if ('2011' in a)])
        except:
            return 'na'

    def previousyeardividendyield(self):
        try:
            yld = 100.*float(self.previousyeardividend())/float(self.get('quote'))
            l, r = str(yld).split('.')
            return (l+'.'+r[0:2])
        except:
            return 'na'

    def real_trailing_pe(self):
        def pospart(x):
            if x<0.:
                return 0.
            else:
                return x
        try:
            adjratio = pospart(stringtofloat(self.get('cash'))-stringtofloat(self.get('debt'))) / stringtofloat(self.get('marketcap'))
            rpe = stringtofloat(self.get('pe_trailing')) * (1.-adjratio)
            l, r = str(rpe).split('.')
            return (l+'.'+r[0:1])
        except:
            return 'na'

    def keywords(self):
        badwords = ['','None','na','and']
        keywords = []+badwords # a trick to insure the 'remove' method works
        try:
            keywords+= (str(self.get('sector')).replace('/',' ').replace(',',' ').replace('-',' ')).split(' ')
        except:
            None
        try:
            keywords+= (str(self.get('industry')).replace('/',' ').replace(',',' ').replace('-',' ')).split(' ')
        except:
            None
        keywords = list(set(keywords))
        for bw in badwords:
            keywords.remove(bw)
        keywords.sort()
        return keywords

    def pricetobookratio(self):
        try:
            ratio = stringtofloat(self.get('pe_trailing')) * float(self.get('return_on_equity')[0:-1]) / 100.
            return str(int(ratio*100.)/100.)
        except:
            return 'na'
    '''


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


