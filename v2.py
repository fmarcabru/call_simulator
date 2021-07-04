import struct
filename="tenminrtp.pcap"
outfile="rtp"
with open(filename, "rb") as rtpfile:
    with open(outfile, "wb") as outf:
        # header capture file
        data = rtpfile.read(24)
        #(tag, majv, minv, res1, res2, snaplen, lt) = struct.unpack("=LHHLLLL", data)
        tag = struct.unpack("=L20x", data)[0]
        if tag == 2712847316:
            print('Type is pcap')
            while data:
            #packet header
                
                data = rtpfile.read(16)
                try:
                    capturelen = struct.unpack("=8xL4x", data)[0]
                except:
                    print("over")
                    break
                if capturelen == 214:
                    #print('capture is correct')


                    data=rtpfile.read(38)
                    ethertype,proto=struct.unpack("12xh9xc14x",data)
                    if ethertype==8 and int.from_bytes(proto,"little")==17:
                        #print("UDP IP")

                        data=rtpfile.read(16)
                        udplength=struct.unpack(">H14x",data)[0]
                        if udplength==180:
                            #print("udp length matches")
                            data=rtpfile.read(160)
                            #print(data)
                            print(len(data))
                            outf.write(data)
                        else:
                            print("the udp content does not match the expected length")
                    else:
                        print("it is not UDP IP")
                else:
                    print('capture len is not as expected')
                    rtpfile.read(capturelen)
        else:
            print('Save your file as pcap')