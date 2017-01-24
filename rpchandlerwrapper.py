
from google.appengine.ext import webapp
from django.utils import simplejson

class RPCHandlerWrapper(webapp.RequestHandler):
    """ Allows the functions defined in the RPCMethods class to be RPCed."""

    def makemethodlist(self):
        raise ValueError('to be defined in subclasses')
    
    def __init__(self):
        webapp.RequestHandler.__init__(self)
        self.methods = self.makemethodlist()

    def get(self):

        ip = self.request.remote_addr
        
        func = None

        action = self.request.get('action')
        if action:
            if action[0] == '_':
                self.error(403) # access denied
                return
            else:
                func = getattr(self.methods, action, None)

        if not func:
            self.error(404) # file not found
            return

        args = ()
        while True:
            key = 'arg%d' % len(args)
            val = self.request.get(key)
            if val:
                args+= (simplejson.loads(val),)
            else:
                break

        args+= (str(ip),)
        
        result = func(*args)
        self.response.out.write(simplejson.dumps(result))
