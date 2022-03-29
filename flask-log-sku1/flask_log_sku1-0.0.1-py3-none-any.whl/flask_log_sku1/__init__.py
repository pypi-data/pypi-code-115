#Used to print out messages server side, and make them pretty
import datetime

class log:
    def __init__(self,*messages):
        emptystring = ''
        for msg in messages:
            emptystring += str(msg)
        self.string = emptystring
        self.main = '[LOG] '
        self.timestamp = '[ '+str(get_current_time())+' ]'
    def success(self):
        print (self.main,self.timestamp,'[**Success**]',self.string)
    def fail(self):
        print (self.main,self.timestamp,'[**Failed**]',self.string)
    def error(self):
        print (self.main,self.timestamp,'[**Error**]',self.string)

def get_current_time():
    return datetime.datetime.now().strftime("[%d/%b/%Y %H:%M:%S]")