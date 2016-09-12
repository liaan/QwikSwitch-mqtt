#!/usr/bin/python
import os
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

sys.path.insert(1, os.path.join(os.path.dirname(__file__), './ext/paho-mqtt-client'))
import client as mqtt
softwareversion = '0.01'

mqtt_host = "10.0.0.247"
mqtt_port = 1883
lastcounter = {}


class QwickSwithMqtt:

	def __init__(self):
	
		
		self._mqtt = mqtt.Client(client_id="abc", clean_session=True, userdata=None)
		
		self._mqtt.loop_start()  # creates new thread and runs Mqtt.loop_forever() in it.
		
		self._mqtt.on_connect = self._on_connect
		self._mqtt.on_message = self._on_message
		
		logger.debug('Connecting to host')
		self._mqtt.connect_async(mqtt_host, port=mqtt_port, keepalive=60, bind_address="")
		logger.debug('our client id (and also topic) is %s' % "abc")
		
		self._init_usb();		
		self._start_usb_listen();
		


		
	def _on_message(self, client, userdata, msg):

		try:
			logger.debug('message! userdata: %s, message %s' % (userdata, msg.topic+" "+str(msg.payload)))
			address = msg.topic.split('/')[-2]	
			
			## Way to hacky method, need get into struct or something
			output = '0107'+address+'000607';		
			if msg.payload == "ON" :
				msg.payload = 100
			
			if msg.payload == "OFF":
				msg.payload = 0
			
			output += "%02d" % ((int(msg.payload)*64)/100)		
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

		logger.debug('connected! client=%s, userdata=%s, flags=%s, rc=%s' % (client, userdata, flags, rc))
		# Subscribing in on_connect() means that if we lose the connection and
		# reconnect then subscriptions will be renewed.
		client.subscribe("/QwikSwitch/+/level")	

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
			logger.debug("counter in last counter=%s", binascii.hexlify(lastcounter[id]))
			
		else :
			 lastcounter[id] = 0
			
		
		if lastcounter[id] != counter:
			lastcounter[id] = counter
			logger.debug("Not Same, so lets publish")
			
			logger.debug("data %s",data)
			
			##Publish all with Hex values to try keep with QS methology
			self._publish(binascii.hexlify(data['id'])+'/command',binascii.hexlify(data['command']));
			self._publish(binascii.hexlify(data['id'])+'/data',binascii.hexlify(data['data']));
			self._publish(binascii.hexlify(data['id'])+'/data2',binascii.hexlify(data['data2']));
			self._publish(binascii.hexlify(data['id'])+'/data3',binascii.hexlify(data['data3']));
			self._publish(binascii.hexlify(data['id'])+'/counter',binascii.hexlify(data['counter']));
		else:
			logger.debug("Counter same, so duplicate command, skipping")
		
		
	def _publish(self,topic,value):

		topic = '/QwikSwitch/' + topic
		payload = value
		logger.debug('publishing on topic "%s", data "%s"' % (topic, payload))
		
		self._mqtt.publish(topic, payload=payload, qos=0, retain=False)
	
	def _decode_qs_packet(self,packet):
		
		#DEBUG:__main__:data {'counter': array('B', [68]), 'unkown3': array('B', [0]), 'unkown2': array('B', [11]), 'unkown1': array('B', [1]), 'command': array('B', [130]), 'data': array('B', [129]), 'id': array('B', [29, 177, 16])}
		##Off
		#DEBUG:__main__:data {'counter': array('B', [65]), 'unkown3': array('B', [0]), 'unkown2': array('B', [11]), 'unkown1': array('B', [1]), 'command': array('B', [130]), 'data4': array('B', [58, 131, 0, 0]), 'data': array('B', [129]), 'id': array('B', [29, 177, 16]), 'data3': array('B', [125]), 'data2': array('B', [51])}
		##On
		#DEBUG:__main__:data {'counter': array('B', [66]), 'unkown3': array('B', [0]), 'unkown2': array('B', [11]), 'unkown1': array('B', [1]), 'command': array('B', [130]), 'data4': array('B', [59, 132, 0, 0]), 'data': array('B', [129]), 'id': array('B', [29, 177, 16]), 'data3': array('B', [30]), 'data2': array('B', [51])}

		##Off
		#DEBUG:__main__:data {'counter': array('B', [67]), 'unkown3': array('B', [0]), 'unkown2': array('B', [11]), 'unkown1': array('B', [1]), 'command': array('B', [130]), 'data4': array('B', [59, 131, 0, 0]), 'data': array('B', [129]), 'id': array('B', [29, 177, 16]), 'data3': array('B', [125]), 'data2': array('B', [51])}




		
		#@1da124.00.00.06.01.54 --> Press
		#01:09:1d:a1:24:00:05:06:01:53:86:3b:84:
		
		#@1da124.00.01.06.00.53 -- Pres RElease
		#01:09 :1d:a1:24: 00 : 05:06:00: 52:86:  3b:84
		
		# {"id":"@1db110","cmd":"STATUS.ACK","data":"0%,RX1DIM,V51","rssi":"75%"}
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
		
		logger.debug("Hex %s" ,binascii.hexlify(packet))
		#print packet[2:5].tostring()
		
		data['unkown1'] = packet[0:1].tostring()
		data['unkown2']  = packet[1:2].tostring()
		data['id'] = packet[2:5].tostring()
		data['unkown3'] = packet[5:6].tostring()
		data['counter'] = packet[6:7].tostring()
		data['command']= packet[7:8].tostring()	
		data['data'] = packet[8:9].tostring()
		data['data2'] = packet[9:10].tostring()
		data['data3'] = packet[10:11].tostring()
		data['data4'] = packet[11:15].tostring()
		
		
		
		
		
		logger.debug("Address %s" ,binascii.hexlify(data['id']))
		logger.debug( "counter %s" ,binascii.hexlify(data['counter']))
		logger.debug( "Command %s" , binascii.hexlify(data['command']))
		logger.debug( "Data %s" , binascii.hexlify(data['data']))
		
		#self.qwickswitch_dev.write(1,binascii.unhexlify('01071DB11000060700'))
		#self.qwickswitch_dev.write(1,binascii.unhexlify('01071DB11000060715'))
		
		
		
		#data = ":".join("{:02x}".format(c) for c in packet)
		#data.addres

		#print data

	
		
		return data
	
	def _init_usb(self):
		#next line sets Vendor/Product id, these values have to be set also in PIC-side
		#You can check the set values in linux using command "lsusb". This shows ID VendorId:ProductId
		self.qwickswitch_dev = usb.core.find(idVendor=0x04d8, idProduct=0x2005)
		
		if self.qwickswitch_dev is None:
			raise ValueError('Device not found')
			
		#When you connect the device to linux. Linux automatically sets some drivers to it. In order to this script to work
		#we must first detach the driver
		if self.qwickswitch_dev.is_kernel_driver_active(0) is True:
			print "Detaching device"
			self.qwickswitch_dev.detach_kernel_driver(0)
		
		interface = 0
		self.qs_endpoint = self.qwickswitch_dev[0][(0,0)][0]
		print "Device Found"
		try:
			self.qwickswitch_dev.write(1,binascii.unhexlify('01071DB11000070764'))
		except usb.core.USBError as e:
			##aaasdf
			print e
		
		
	def _start_usb_listen(self):		
		print "starting to listen";
		collected = 0
		attempts = 50

		while True:
			try:
				data = self.qwickswitch_dev.read(self.qs_endpoint.bEndpointAddress,self.qs_endpoint.wMaxPacketSize,0,500)
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


def main():

	global mqtt_host
	global mqtt_port
	

	# Argument parsing

	parser = argparse.ArgumentParser(

		description='Qwickswitch v%s: Mqtt publisher of QwickSwith on the Pi.' % softwareversion

	)

	parser.add_argument("-d", "--debug", help="set logging level to debug",
						action="store_true")

	parser.add_argument("-s", "--server", help='Mqtt Server, Default: %s ' % mqtt_host)
	parser.add_argument("-p", "--port", help="Mqtt Port, Default:  %s" % mqtt_port)
	

	args = parser.parse_args()
	


	# Init logging
	logging.basicConfig(level=(logging.DEBUG if args.debug else logging.INFO))	

	if args.server:
		mqtt_host = args.server
    	logger.debug("Host: %s"%mqtt_host)

	if args.port:
		mqtt_port = args.port		    		
		logger.debug("Port: %s"%mqtt_port)	

	logger.info("%s v%s is starting up" % (__file__, softwareversion))
	logLevel = {0: 'NOTSET', 10: 'DEBUG', 20: 'INFO', 30: 'WARNING', 40: 'ERROR'}
	logger.info('Loglevel set to ' + logLevel[logging.getLogger().getEffectiveLevel()])


	# Start and run the mainloop

	logger.info("Starting mainloop, responding on only events")
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


