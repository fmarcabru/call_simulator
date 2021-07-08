# define the class for sip call

class sipCall:
    import secrets
    def __init__(self, callid, from, to, via, contact, tag, cseq, allow, localrtpport, remotertpport, localrtpip, remotertpip, ssrc, rtpseqnumber=18489, rtptime=4192261776):
        self.callid = callid
        self.from = from
        self.to = to
        self.via = via
        self.contact = contact
        self.tag = tag
        self.cseq = cseq
        self.allow = allow
        self.localrtpport = localrtpport
        self.remotertpport = remotertpport
        self.localrtpip = localrtpip
        self.remotertpip = remotertpip
        self.ssrc = ssrc
        self.rtpseqnumber = rtpseqnumber
        self.rtptime = rtptime


    def new_ssrc(self):
        self.ssrc = self.secrets.token_hex(4)

    def new_tag(self):
        self.tag = self.secrets.token_hex(8)

    def sipTrying(self):
        self._trying = True
        message="SIP/2.0 100 Trying"+"\r\nVia:"+self.via+"\r\nFrom:"+self.from+"\r\nTo:"+self.to+"\r\nCall-ID:"+self.callid+"\r\nCSeq:"+self.cseq+"\r\n\r\n"

    def sipRinging(self):
        if hasattr(self, _trying):
            self._ringing = True
        else:
            # log here an error we are at a wrong state, there is no 100 trying attr found shouldnt be here
            print("error")
    

