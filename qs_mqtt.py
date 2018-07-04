#!/usr/bin/python
import os
import commands
import usb.core
import usb.util
import sys
import argparse
import threading

import pprint
import logging

import struct
import binascii

logger = logging.getLogger(__name__)

import time

sys.path.insert(1, os.path.join(os.path.dirname(__file__), './ext/paho-mqtt-clie                                                                                                                               nt'))
import client as mqtt
softwareversion = '0.01'

mqtt_host = "10.0.0.247"
mqtt_port = 1883
lastcounter = {}


class QwickSwithMqtt:

        def __init__(self):


                self._mqtt = mqtt.Client(client_id="abc", clean_session=True, us                                                                                                                               erdata=None)

                self._mqtt.loop_start()  # creates new thread and runs Mqtt.loop                                                                                                                               _forever() in it.

                self._mqtt.on_connect = self._on_connect
                self._mqtt.on_message = self._on_message

                logger.debug('Connecting to host')
                self._mqtt.connect_async(mqtt_host, port=mqtt_port, keepalive=60                                                                                                                               , bind_address="")
                logger.debug('our client id (and also topic) is %s' % "abc")

                self._init_usb();
                self._start_usb_listen();




        def _on_message(self, client, userdata, msg):

                try:
                        logger.debug('message! userdata: %s, message %s' % (user                                                                                                                               data, msg.topic+" "+str(msg.payload)))
                        address = msg.topic.split('/')[-2]

                        ## Way to hacky method, need get into struct or somethin                                                                                                                               g
                        output = '0107'+address+'000607';
                        if msg.payload == "ON" :
                                msg.payload = 100

                        if msg.payload == "OFF":
                                msg.payload = 0
                        logger.debug("sending value %s" ,"%02d" % ((int(msg.payl                                                                                                                               oad)*64)/100))
                        ##Make it into hex from 100 .. get converted back when g                                                                                                                               ets send from hex to int .. prob better way todo it.
                        output += "%02d" % ((int(msg.payload)*64)/100)
                        #output += "%02d" % int(msg.payload)

                        logger.debug('Writing Message: %s' % output)
                except:
                        return


                try:
                        self.qwickswitch_dev.write(1,binascii.unhexlify(output))
                except usb.core.USBError as e:
                        ##aaasdf
                        print e

        def _on_connect(self, client, userdata, flags, rc):


                """
                RC definition:
                0: Connection successful
                1: Connection refused - incorrect protocol version
                2: Connection refused - invalid client identifier
                3: Connection refused - server unavailable
                4: Connection refused - bad username or password
                5: Connection refused - not authorised
                6-255: Currently unused.
                """

                logger.debug('connected! client=%s, userdata=%s, flags=%s, rc=%s                                                                                                                               ' % (client, userdata, flags, rc))
                # Subscribing in on_connect() means that if we lose the connecti                                                                                                                               on and
                # reconnect then subscriptions will be renewed.
                client.subscribe("QwikSwitch/+/set")

        def _receive_qs_data(self,packet):
                ##Get global var
                global lastcounter

                #Decode packet
                data = self._decode_qs_packet(packet);
                ##Get counter and id
                counter =  data['counter']
                id =  data['id']

                #If not set yet, then set
                if id in lastcounter:
                        logger.debug("counter in last counter=%s", binascii.hexl                                                                                                                               ify(lastcounter[id]))

                else :
                         lastcounter[id] = 0


                if lastcounter[id] != counter:
                        lastcounter[id] = counter
                        logger.debug("Not Same, so lets publish")

                        logger.debug("data %s",data)

                        ##Publish all with Hex values to try keep with QS methol                                                                                                                               ogy
                        #self._publish(binascii.hexlify(data['id'])+'/command',b                                                                                                                               inascii.hexlify(data['command']));

                        ## Pusblish actual value so can see
                        self._publish(binascii.hexlify(data['id'])+'/value',data                                                                                                                               ['value']);

                        #self._publish(binascii.hexlify(data['id'])+'/data',bina                                                                                                                               scii.hexlify(data['data']));
                        #self._publish(binascii.hexlify(data['id'])+'/type',bina                                                                                                                               scii.hexlify(data['type']));
                        #self._publish(binascii.hexlify(data['id'])+'/data3',bin                                                                                                                               ascii.hexlify(data['data3']));
                        #self._publish(binascii.hexlify(data['id'])+'/data4',bin                                                                                                                               ascii.hexlify(data['data4']));
                        #self._publish(binascii.hexlify(data['id'])+'/counter',b                                                                                                                               inascii.hexlify(data['counter']));

                else:
                        logger.debug("Counter same, so duplicate command, skippi                                                                                                                               ng")


        def _publish(self,topic,value):

                topic = 'QwikSwitch/' + topic
                payload = value
                logger.debug('publishing on topic "%s", data "%s"' % (topic, pay                                                                                                                               load))

                self._mqtt.publish(topic, payload=payload, qos=0, retain=False)

        def _decode_qs_packet(self,packet):

                #DEBUG:__main__:data {'counter': array('B', [68]), 'unkown3': ar                                                                                                                               ray('B', [0]), 'unkown2': array('B', [11]), 'unkown1': array('B', [1]), 'command                                                                                                                               ': array('B', [130]), 'data': array('B', [129]), 'id': array('B', [29, 177, 16])                                                                                                                               }
                ##Off
                #DEBUG:__main__:data {'counter': array('B', [65]), 'unkown3': ar                                                                                                                               ray('B', [0]), 'unkown2': array('B', [11]), 'unkown1': array('B', [1]), 'command                                                                                                                               ': array('B', [130]), 'data4': array('B', [58, 131, 0, 0]), 'data': array('B', [                                                                                                                               129]), 'id': array('B', [29, 177, 16]), 'data3': array('B', [125]), 'data2': arr                                                                                                                               ay('B', [51])}
                ##On
                #DEBUG:__main__:data {'counter': array('B', [66]), 'unkown3': ar                                                                                                                               ray('B', [0]), 'unkown2': array('B', [11]), 'unkown1': array('B', [1]), 'command                                                                                                                               ': array('B', [130]), 'data4': array('B', [59, 132, 0, 0]), 'data': array('B', [                                                                                                                               129]), 'id': array('B', [29, 177, 16]), 'data3': array('B', [30]), 'data2': arra                                                                                                                               y('B', [51])}

                ##Off
                #DEBUG:__main__:data {'counter': array('B', [67]), 'unkown3': ar                                                                                                                               ray('B', [0]), 'unkown2': array('B', [11]), 'unkown1': array('B', [1]), 'command                                                                                                                               ': array('B', [130]), 'data4': array('B', [59, 131, 0, 0]), 'data': array('B', [                                                                                                                               129]), 'id': array('B', [29, 177, 16]), 'data3': array('B', [125]), 'data2': arr                                                                                                                               ay('B', [51])}





                #@1da124.00.00.06.01.54 --> Press
                #01:09:1d:a1:24:00:05:06:01:53:86:3b:84:

                #@1da124.00.01.06.00.53 -- Pres RElease
                #01:09 :1d:a1:24: 00 : 05:06:00: 52:86:  3b:84

                # {"id":"@1db110","cmd":"STATUS.ACK","data":"0%,RX1DIM,V51","rss                                                                                                                               i":"75%"}
                # @1db110.00.42.82.81337d.3b

                ##Commands
                # 02 = Get Output Status
                # 05 = Toggle output
                # 06 = Hold to Dim
                # 07 = Set Output Level

                # command  Data:
                #00 = Start Dimming
                #01 = Stop Dimming
                #00 - 64 Level 0% to 100%
                #82 = Ack Get Status ON = Relay Output ON
                #OFF = Relay Output OFF
                #00% = Dimmer Output off
                #01% - 64% = Dimmer Level 1% - 100%
                #85 = Ack Toggle output
                #86 = Ack Hold to Dim
                #87 = Ack Set Output Level ON = Relay Output ON
                #OFF = Relay Output OFF
                #00% = Dimmer Output off
                #01% - 64% = Dimmer Level 1% - 100%


                data = {};


                hex2bin_map = {
                "0":"0000",
                "1":"0001",
                "2":"0010",
                "3":"0011",
                "4":"0100",
                "5":"0101",
                "6":"0110",
                "7":"0111",
                "8":"1000",
                "9":"1001",
                "a":"1010",
                "b":"1011",
                "c":"1100",
                "d":"1101",
                "e":"1110",
                "f":"1111",
                }
                hex_num=binascii.hexlify(packet)
                logger.debug("Binary %s",  " ".join(hex2bin_map[i] for i in hex_                                                                                                                               num))

                logger.debug("Hex %s" ,binascii.hexlify(packet))
                #print packet[2:5].tostring()

                data['unkown1'] = packet[0:1].tostring()
                data['unkown2']  = packet[1:2].tostring()
                data['id'] = packet[2:5].tostring()
                data['unkown3'] = packet[5:6].tostring()
                data['counter'] = packet[6:7].tostring()
                data['command']= packet[7:8].tostring()
                data['data'] = packet[8:9].tostring()
                data['type'] = packet[9:10].tostring()

                data['data3'] = packet[10:11].tostring()
                data['data4'] = packet[11:15].tostring()
                ## Value is first 7 bytes of packet 11, so shift one over to mak                                                                                                                               e normal value
                value =  (ord(packet[10:11].tostring())>>1)
                logger.debug("Value before %s" , value)

                if  ord(data['type']) == 51:
                        if value >= 61:
                                logger.debug("value below 4 so off")
                                data['value'] = 0
                        else:
                                logger.debug("value on")
                                data['value'] = ((64-value)*100/64)
                else:
                        if value == 64:
                                data['value'] = "ON"
                        else:
                                data['value'] = "OFF"




                logger.debug("Address %s" ,binascii.hexlify(data['id']))
                logger.debug( "counter %s" ,binascii.hexlify(data['counter']))
                logger.debug( "Command %s" , binascii.hexlify(data['command']))
                logger.debug( "Value %s" , data['value'])
                logger.debug( "Data2 %s" , binascii.hexlify(data['type']))
                logger.debug( "Data3 %s" , binascii.hexlify(data['data3']))

                logger.debug( "Data %s" , binascii.hexlify(data['data']))


                #self.qwickswitch_dev.write(1,binascii.unhexlify('01071DB1100006                                                                                                                               0700'))
                #self.qwickswitch_dev.write(1,binascii.unhexlify('01071DB1100006                                                                                                                               0715'))



                #data = ":".join("{:02x}".format(c) for c in packet)
                #data.addres

                #print data



                return data

        def _init_usb(self):

                #next line sets Vendor/Product id, these values have to be set a                                                                                                                               lso in PIC-side
                #You can check the set values in linux using command "lsusb". Th                                                                                                                               is shows ID VendorId:ProductId
                self.qwickswitch_dev = usb.core.find(idVendor=0x04d8, idProduct=                                                                                                                               0x2005)

                if self.qwickswitch_dev is None:
                        raise ValueError('Device not found')

                #When you connect the device to linux. Linux automatically sets                                                                                                                                some drivers to it. In order to this script to work
                #we must first detach the driver
                if self.qwickswitch_dev.is_kernel_driver_active(0) is True:
                        print "Detaching device"
                        self.qwickswitch_dev.detach_kernel_driver(0)

                interface = 0
                self.qs_endpoint = self.qwickswitch_dev[0][(0,0)][0]
                logger.debug("Device Found");
                try:
                        self.qwickswitch_dev.write(1,binascii.unhexlify('01071DB                                                                                                                               11000070764'))
                except usb.core.USBError as e:
                        ##aaasdf
                        print e


        def _start_usb_listen(self):
                logger.debug( "starting to listen");
                collected = 0
                attempts = 50

                while True:
                        try:
                                data = self.qwickswitch_dev.read(self.qs_endpoin                                                                                                                               t.bEndpointAddress,self.qs_endpoint.wMaxPacketSize,500)
                                collected += 1
                                self._receive_qs_data(data);
                                data = None
                                continue
                        except usb.core.USBError as e:
                                data = None

                        if e.args == (110,'Operation timed out',):
                                #print "timeout"
                                data = None
                                continue

def stop_if_already_running():
        script_name = os.path.basename(__file__)
        l = commands.getstatusoutput("ps aux | grep -e '%s' | grep -v grep | awk                                                                                                                                '{print $2}'| awk '{print $2}'" % script_name)
        if l[1]:
                sys.exit(0);


def main():

        global mqtt_host
        global mqtt_port

        stop_if_already_running();

        # Argument parsing

        parser = argparse.ArgumentParser(

                description='Qwickswitch v%s: Mqtt publisher of QwickSwith on th                                                                                                                               e Pi.' % softwareversion

        )

        parser.add_argument("-d", "--debug", help="set logging level to debug",
                                                action="store_true")

        parser.add_argument("-s", "--server", help='Mqtt Server, Default: %s ' %                                                                                                                                mqtt_host)
        parser.add_argument("-p", "--port", help="Mqtt Port, Default:  %s" % mqt                                                                                                                               t_port)


        args = parser.parse_args()



        # Init logging
        logging.basicConfig(level=(logging.DEBUG if args.debug else logging.INFO                                                                                                                               ))

        if args.server:
                mqtt_host = args.server
        logger.debug("Host: %s"%mqtt_host)

        if args.port:
                mqtt_port = args.port
                logger.debug("Port: %s"%mqtt_port)

        logger.debug("%s v%s is starting up" % (__file__, softwareversion))
        logLevel = {0: 'NOTSET', 10: 'DEBUG', 20: 'INFO', 30: 'WARNING', 40: 'ER                                                                                                                               ROR'}
        logger.debug('Loglevel set to ' + logLevel[logging.getLogger().getEffect                                                                                                                               iveLevel()])


        # Start and run the mainloop

        logger.debug("Starting mainloop, responding on only events")
        qs = QwickSwithMqtt()



        #@1db110.00.43.82.81337d.2e
        #
        ##Push button receive
        #@1da123.00.05.05..51
        #@1da124.00.06.05..52 --> click

        #@1da124.00.00.06.01.54 --> Press
        #@1da124.00.01.06.00.53 -- Pres RElease









if __name__ == "__main__":

        main()

