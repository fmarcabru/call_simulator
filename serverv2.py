#!/usr/bin/env python
import socket
import os
#from threading import Thread
import concurrent.futures
from threading import Lock
import logging
import traceback
import time
import multiprocessing
import sys
import secrets


def ringing(call,callid,connection):
    logging.debug("Building ringing message")
    global ip
    global port
    try:
        logging.debug("received %s",call)
        tag=secrets.token_hex(8)
        hruri="SIP/2.0 180 Ringing"
        contactvalue=secrets.token_hex(12)
        hcontact="\r\nContact: <sip:{}@{}:{}>".format(contactvalue,ip,port)
        logging.debug("contact built")
        hallow = "\r\nAllow: INVITE, INFO, BYE, CANCEL, ACK, UPDATE"
        logging.debug("allow built")
        hvia="\r\nVia:"+call[0]['VIA']
        logging.debug("via built")
        hfrom="\r\nFrom:"+call[0]['FROM']
        logging.debug("from built")
        hto="\r\nTo:"+call[0]['TO']+";tag="
        logging.debug("to built")
    #   hto="\r\nTo:"+parsed['TO']+";tag="+tag
        hcseq="\r\nCSeq:"+call[0]['CSEQ']
        logging.debug("cseq built")
    #   hcseq="\r\nCSeq:"+parsed['CSEQ']
        hcallid="\r\nCall-ID:"+callid
        logging.debug("callid built")
    #   hcallid="\r\nCall-ID:"+parsed['CALL-ID']
        hend="\r\n\r\n"
        hcontentlength="\r\nContent-Length: 0"
        logging.debug("headers built")
        ringing=hruri+hvia+hfrom+hto+hcallid+hcseq+hcontact+hallow+hcontentlength+hend
        sendsipmessage(connection,remoteip,remoteport,ringing)
        call.append({"TIME":time.time()})
        call[-1].update({"MESSAGE":"180 Ringing"})
        call[-1].update({"CONTACT":hcontact})
        call[-1].update({"TO":hto})
        logging.debug("%s",call)
        return call
    except Exception as e:
        logging.error("Error in ringing section")
        if hasattr(e,'message'):
            logging.critical("%s",e.message)
        else:
            logging.critical("%s",e)

def start_server(host, port):
    # AF_INET for IPv4 and SOCK_DGRAM for UDP
    ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        ServerSocket.bind((host,port))
    except socket.error as err:
        print(str(err))
    logging.info("Started server in %s:%s...",host,str(port))


    return ServerSocket
# Can't listen cause it is not TCP    
#   ServerSocket.listen(5)


# can't accept, only for TCP
#    connection, address = ServerSocket.accept()



def parsemessage(sipmess):
    #print(sipmess)
    headers={}
    info={}
    firstline=0
    sdp=0
    #break sip message into lines
    for line in sipmess.splitlines():
        if firstline==0:
            headers['SIPURI']=line
            firstline=1
        #find when header section ends
        elif len(line)==0:
            sdp=1
        elif sdp==0:
            header,content=breakline(line,":")
            headers[header]=content
        else:
            header,content=breakline(line,"=")
            if header not in  headers.keys():
                headers[header]=[]
            headers[header].append(content)
    return(headers)

def sendsipmessage(socket,ip,port,message):
    try:
        socket.sendto(message.encode(),(ip,port))
    except Exception as e:
        logging.error("Error in sendsipmessage section")
        print(type(message))
        print(type(ip))
        print(ip)
        print(type(port))
        if hasattr(e,'message'):
            logging.exception("%s",e.message)
        else:
            logging.exception("%s",e)


def answer(call,callid,connection):
    global ip
    global rtpport
    try:
        rtpport = rtpport + 2
        hruri="SIP/2.0 200 OK"
        hcontenttype="\r\nContent-Type: application/sdp"
        haccept="\r\nAccept: application/dtmf-relay,application/sdp"
        #-------
        hvia="\r\nVia:"+call[0]['VIA']
        hfrom="\r\nFrom:"+call[0]['FROM']
        #Need to change the way I store the parameters as they are over different messages
        hto=call[-1]['TO']
        hcallid="\r\nCall-ID:"+callid
        hcseq="\r\nCSeq:"+call[0]['CSEQ']
        hcontact=call[-1]['CONTACT']
        hallow="\r\nAllow: INVITE, INFO, BYE, CANCEL, ACK, UPDATE"
        #---------------------------
        v="\r\nv=0"
        o="\r\no=- {} IN IP4 {}".format(str(time.time()).replace("."," "),ip)
        s="\r\ns=-"
        c="\r\nc=IN IP4 {}".format(ip)
        t="\r\nt=0 0"
        m="\r\nm=audio {} RTP/AVP 8 101".format(rtpport)
        a="\r\na=rtpmap:101 telephone-event/8000\r\na=fmtp:101 0-15\r\na=sendrecv"
        body=v+o+s+c+t+m+a
        contentlength=len(body.encode())
        hcontentlength="\r\nContent-Length: {}".format(str(contentlength))
        hend="\r\n\r\n"
        answer=hruri+hvia+hfrom+hto+hcallid+hcseq+hcontact+hallow+hcontenttype+haccept+hcontentlength+"\r\n"+body+hend
        sendsipmessage(connection,remoteip,remoteport,answer)
        return call
    except Exception as e:
        logging.error("Error in answer section")
        if hasattr(e,'message'):
            logging.exception("%s",e.message)
        else:
            logging.exception("%s",e)


def sip(connection):
    logging.info("SIP process started")
    global activecalls
    global ip
    global port
    global stop_threads
    global rtpport
    global remoteip
    global remoteport
    calls={}


    while not stop_threads:

        recv_data,[remoteip,remoteport] = connection.recvfrom(2048)
        
        messagetime=time.time()

        logging.debug("Message received from %s port %s ",remoteip,remoteport)
        
        if not recv_data:
            break
        parsed=parsemessage(recv_data.decode())
#-----------------------------------------------------------------------
        callid=parsed['CALL-ID'].replace(" ","")
        with data_lock:
            calls = activecalls.copy()

        if callid not in calls.keys():
            if (parsed['SIPURI'][:parsed['SIPURI'].find(" ")]) == 'INVITE':
    
                calls.update({callid:[{"TIME":messagetime}]})
                calls[callid][-1].update({"MESSAGE":"INVITE"})
                calls[callid][-1].update({"VIA":parsed['VIA']})
                calls[callid][-1].update({"FROM":parsed['FROM']})
                calls[callid][-1].update({"TO":parsed['TO']})
                calls[callid][-1].update({"CSEQ":parsed['CSEQ']})
                calls[callid][-1].update({"MEDIAIP":parsed['C'][0].split()[-1]})
                calls[callid][-1].update({"MEDIAPORT":parsed['M'][0].split()[1]})
                
                sendsipmessage(connection,remoteip,remoteport,"SIP/2.0 100 Trying"+"\r\nVia:"+parsed['VIA']+"\r\nFrom:"+parsed['FROM']+"\r\nTo:"+parsed['TO']+"\r\nCall-ID:"+parsed['CALL-ID']+"\r\nCSeq:"+parsed['CSEQ']+"\r\n\r\n")
                calls[callid].append({"TIME":time.time()})
                calls[callid][-1].update({"MESSAGE":"100 Trying"})
            

            else:
                print("received ({}) message with no active call".format(parsed['SIPURI']))
        else:
                print("RECEIVED ------{}".format(parsed['SIPURI']))
       
        
        with data_lock:
            activecalls = calls



def breakline(line,separator):
    header=line[:line.find(separator)]
    content=line[line.find(separator)+1:]
    return(header.upper(),content)


def maintaincalls(connection):
    logging.info("Maintaincalls process started")
    global activecalls
    timertrying=0.3
    ringingtime=2
    currtime=time.time()
    flag=0
    step=0
#    testtime=time.time()
    while True:
        try:
    #        if time.time()-testtime >1:
    #            testtime=time.time()
    #            print("mc")
    #            print (len(activecalls))
    #        print(type(activecalls))

    #        print(type(activecalls))
            #logging.debug("Activating the lock")

            with data_lock:
                initiated=activecalls.copy()
            step=1

            modification=0
            step=1.5
            previouslen=len(initiated)
            for call in initiated:
      #          updatedcall=calls[call]
                step=2
#                if flag==1:
#                    logging.debug("Second round %s",calls[call][-1]['MESSAGE'])
                lastmessage=initiated[call][-1]['MESSAGE']
                step=3
                rightnow=time.time()
                if lastmessage=='100 Trying' and rightnow - initiated[call][-1]['TIME'] > timertrying:
                    step=4
#                    logging.debug("Analysing call %s",call)
                    logging.info("Sending ringing for %s",call)
#                    calls.update({call:ringing(calls[call])})
                    message=ringing(initiated[call],call,connection)
                    modification = 1
                    if not message:
                        break
#                   else:
                        #calls.update({call:message})
                elif lastmessage=='180 Ringing' and time.time() - initiated[call][-1]['TIME'] > ringingtime:
#                    calls.update({call:answer(calls[call])}) 
                    message=answer(initiated[call],call,connection)
                    if not message:
                        break
#                    else:
#                        calls.update({call:message})
#                        logging.debug("Object Calls updated")
                    #--------------------------------------------

                    mediaip=initiated[call][0]['MEDIAIP']
                    mediaport=initiated[call][0]['MEDIAPORT']
                    logging.debug("Preparing media to %s:%s",mediaip,mediaport)
           
                    modification=1
#                    calls[call].append({"TIME":time.time()})
                    message.append({"TIME":time.time()})
#                    calls[call][-1].update({"MESSAGE":"RTP"})
                    message[-1].update({"MESSAGE":"RTP"})
                    logging.debug("Updating calls object")
#                    calls[call][-1].update({"MEDIAPROCESS":multiprocessing.Process(target=media, args=[calls[call][0]['MEDIAIP'],calls[call][0]['MEDIAPORT']])})
                    message[-1].update({"MEDIAPROCESS":multiprocessing.Process(target=media, args=[initiated[call][0]['MEDIAIP'],initiated[call][0]['MEDIAPORT']])})
                    logging.debug("Setting up the process")
#                    calls[call][-1]["MEDIAPROCESS"].start()
                    message[-1]["MEDIAPROCESS"].start()
                    logging.debug("RTP process Started")
                step=10
            if modification == 1:
                with data_lock:
                    activecalls[call]=message
      
        except Exception as e:
            logging.error("Something went wrong with maintain calls process, object is: %s",initiated)
            logging.error("Step is %i",step)
   #         if lastmessage=='100 Trying' and rightnow - calls[call][-1]['TIME'] > timertrying:
            logging.error("lastmessage is %s, rightnow is %s  calls[call][-1]['TIME'] is %s ",lastmessage, rightnow, initiated[call][-1]['TIME'])
            logging.error("current check is for %s",call)
            logging.error("previous len is %s and current len is %s",previouslen,len(initiated))
            if hasattr(e,'message'):
                logging.exception("%s",e.message)
                break
            else:
                logging.exception("%s",e)
                break
#        finally:
#            logging.debug("%s",initiated)



#    connection.close()
def media(remoteip,remoteport):
    try:
        global ip
        global rtpport
        import secrets
        ssrc=secrets.token_hex(4)
        seq=18489
        timestamp=4192261776
        print("-----------------------")
        
        #10.. .... version rfc 1889 v2
        #..0. .... Padding (false)
        #...0 .... Extension (false)
        #.... 0000 Contributing source identifiers count (0)
        value1=bytes.fromhex('80')
        #0... .... Marker (false)
        #.000 0100 Payload type (PCMA 8)
        value2a=bytes.fromhex('08')
        #1... .... Marker (true)
        #.000 0100 Payload type (PCMA 8)
        value2b=bytes.fromhex('88')

        #2 byte sequence number
        value3=bytes.fromhex(str(hex(seq))[2:])
        #4 byte timestamp
        value4=bytes.fromhex(str(hex(timestamp))[2:])
        #4 byte ssrc
        value5=bytes.fromhex(ssrc)
        print("here")   
        rtpheaders=value1+value2b+value3+value4+value5
        data=0
        deliverytime=0

        pasttime=time.time()
        print("media from {}:{} to {}:{} counter is {} and timestamp is {}".format(ip,rtpport,remoteip,remoteport,seq,timestamp))
        with start_server(ip,rtpport) as socket:
            print("socket opened")
            if len(rtpheaders)==12:
                with open("rtp", "rb") as rtpfile:
                    data = rtpfile.read(160)
                    rtppacket=rtpheaders+data
                    print("all good until here")
                    while data:
                        currenttime=time.time()
                        if currenttime-pasttime >= 0.02:
                            socket.sendto(rtppacket,(remoteip,int(remoteport)))

                            pasttime=currenttime
                            
                            seq += 1
                            #20ms ptime * 8000Khz enconding
                            timestamp += 160
                            value3=bytes.fromhex(str(hex(seq))[2:])
                            value4=bytes.fromhex(str(hex(timestamp))[2:])
                            rtpheaders=value1+value2a+value3+value4+value5
                            data = rtpfile.read(160)
                            rtppacket=rtpheaders+data

        total=value2a+value2b
        print(value4)
        print(total)
        print("type {} for {}".format(type(ssrc),str(ssrc)))
    except Exception as e:
        logging.error("Something went wrong with the media process")
        if hasattr(e,'message'):
            logging.exception("%s",e.message)
        else:
            logging.exception("%s",e)



def main():
    global ip
    global sipport
    global stop_threads
    try:

        socket=start_server(ip,sipport)

    #    signallingprocess=multiprocessing.Process(target=sip, args=socket)
    #    maintaincalls=multiprocessing.Process(target=activecalls)
    #    signallingprocess.start()
    #signallingprocess.join()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            signallingprocess=executor.submit(sip, socket)
#            callprocess=executor.submit(maintaincalls, activecalls)
            callprocess=executor.submit(maintaincalls, socket)
    finally:
        print("Closing server {}:{}".format(ip,str(sipport)))
        socket.close()
        stop_threads=True





if __name__ == "__main__":
    
    stop_threads = False
    ip='192.168.13.31'
    sipport=5060
    rtpport=6000
    port=5060
    activecalls={}
    data_lock = Lock()
    remoteip = ''
    remoteport = 0
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    logging.debug("Defined Initial parameters")
    main()