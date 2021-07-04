# define the class for sip call

class sipCall:
    def __init__(self, callid, from, to):
        self.callid = callid
        self.from = from
        self.to = to

    def sipTrying(self):
        self._trying = True

    def sipRinging(self):
        if hasattr(self, _trying):
            self._ringing = True
        else:
            # log here an error we are at a wrong state, there is no 100 trying attr found shouldnt be here
            print("error")
    

