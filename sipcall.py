# define the class for sip call

class sipCall:
    def __init__(self, callid, from, to, via, contact, allow, localrtpport, remotertpport, localrtpip, remotertpip, ssrc, rtpseqnumber, rtptime):
        self.callid = callid
        self.from = from
        self.to = to
        self.via = via
        self.contact = contact
        self.allow = allow
        self.localrtpport = localrtpport
        self.remotertpport = remotertpport
        self.localrtpip = localrtpip
        self.remotertpip = remotertpip
        self.ssrc = ssrc
        self.rtpseqnumber = rtpseqnumber
        self.rtptime = rtptime

    def sipTrying(self):
        self._trying = True

    def sipRinging(self):
        if hasattr(self, _trying):
            self._ringing = True
        else:
            # log here an error we are at a wrong state, there is no 100 trying attr found shouldnt be here
            print("error")
    

