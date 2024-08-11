import usb.core
import usb.util
import signal
import daemon
import struct
import yaml
import time
import math
import logging
import argparse
import threading
import os
import sys

from PIL import Image

import util
import layouts
 
GLOBAL_INIT_LOCK = 0
MAX_GLOBAL_INIT = 13

GLOBAL_STAT = False
GLOBAL_RUNNING = False

CLASS_WRITE = "write"
CLASS_READ = "read"
CLASS_MAIN = "main"
CLASS_TRIGGER = "trigger"

IMAGE_PACKET_SIZE = 1020
IMAGE_CMD_SIZE = 4

DESIRED_CONFIG = 1

class USBControl:
	def __init__(self, dev, logger, endpoint = None):
		self.device = dev
		self.logger = logger
		self.endpoint = endpoint
		self.lock = threading.Lock()
	
	def read(self, buflen = -1, timeout = 10000):
		try:
			self.lock.acquire()
			if buflen >= 0:
				buf = usb.util.create_buffer(buflen)
			else:
				buf = 0
			self.endpoint.read(buf, timeout)
			return(buf)
		except:
			self.logger.warning("Failed to get data for endpoint {}".format(self.endpoint))
		finally:
			self.lock.release()

	def write(self, data = ""):
		try:
			self.lock.acquire()
			self.endpoint.write(data)
		except:
			self.logger.warning("Failed to send data for endpoint {}".format(self.endpoint))
		finally:
			self.lock.release()

	def control(self, bmRquestType, bmRequest, wValue, wIndex, buf = False, buflen = -1):
		try:
			self.lock.acquire()
			if buf != False:
				assert self.device.ctrl_transfer(bmRquestType, bmRequest, wValue, wIndex, buf) == len(buf)
			elif buflen >= 0:
				ret = self.device.ctrl_transfer(bmRquestType, bmRequest, wValue, wIndex, buflen)
				return(''.join([chr(x) for x in ret]))
			else:
				assert self.device.ctrl_transfer(bmRquestType, bmRequest, wValue, wIndex, 0) == 0
		except:
			self.logger.warning("Failed to perform control transfer")
		finally:
			self.lock.release()

	def descriptor(self, index, language):
		return(usb.util.get_string(self.device, index, language))

	def build(self, padding_len, *args):
		if padding_len > 0:
			padding = bytes("\x00" * padding_len, 'utf-8')
		
		packstr = "B" * len(args)

		if padding_len > 0:
			packstr = packstr + r'%ds'
			data = struct.pack(packstr % (len(padding),), *args, padding)
		else:
			data = struct.pack(packstr, *args)

		return(data)
	
	def raw_build(self, left_padding_len, right_padding_len, *args):
		packstr = "B" * len(args)
		right_padding = []
		left_padding = []

		if left_padding_len > 0:
			left_padding = bytes("\x00" * left_padding_len, 'utf-8')
			packstr = r'%ds' + packstr
		if right_padding_len > 0:
			right_padding = bytes("\x00" * right_padding_len, 'utf-8')
			packstr = packstr + r'%ds'
		
		if left_padding_len > 0 and right_padding_len > 0:
			data = struct.pack(packstr % (left_padding_len, right_padding_len,), left_padding, *args, right_padding)
		elif right_padding_len > 0:
			data = struct.pack(packstr % (right_padding_len,), *args, right_padding)
		elif left_padding_len > 0:
			data = struct.pack(packstr % (left_padding_len,), left_padding, *args)
		else:
			data = struct.pack(packstr, *args)

		return(data)

class Write(threading.Thread):
	def __init__(self, dev, endpoint, config, logger):
		self.device = dev
		self.endpoint = endpoint
		self.config = config
		self.logger = logger
		self.classes = {}
		self.running = False
		self.logger.info("Loaded Write Driver")
		threading.Thread.__init__(self)
	
	def set_class(self, class_index, cls):
		self.classes[class_index] = cls

	def run(self):
		global GLOBAL_INIT_LOCK, MAX_GLOBAL_INIT, GLOBAL_RUNNING
		self.running = True
		self.control = USBControl(self.device, self.logger, self.endpoint)

		self.logger.info("Write Started")

		self.init()

		while self.running:
			if GLOBAL_INIT_LOCK >= 13 and GLOBAL_INIT_LOCK < 14 and GLOBAL_RUNNING:
				time.sleep(2)
				pkt = self.control.build(436, 0x82, 0x01, 0x00, 0x80)
				self.control.write(pkt)
			else:
				time.sleep(0.1)

		self.logger.info("Shutdown Write")
	
	def shutdown(self):
		self.running = False

	def init(self):
		global GLOBAL_INIT_LOCK, MAX_GLOBAL_INIT

		while self.running and GLOBAL_INIT_LOCK < MAX_GLOBAL_INIT:
			if GLOBAL_INIT_LOCK >= 1 and GLOBAL_INIT_LOCK < 2:
				self.control.write(self.control.build(436, 0x85, 0x01, 0x00, 0x80))
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 3 and GLOBAL_INIT_LOCK < 4:
				self.control.write(self.control.build(436, 0x87, 0x01, 0x00, 0x80))
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 5 and GLOBAL_INIT_LOCK < 6:
				self.control.write(self.control.build(436, 0x85, 0x01, 0x00, 0x80))
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 7 and GLOBAL_INIT_LOCK < 8:
				self.control.write(self.control.build(436, 0x87, 0x01, 0x00, 0x80))
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 9 and GLOBAL_INIT_LOCK < 10:
				self.control.write(self.control.build(436, 0x84, 0x01, 0x00, 0x80))
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 11 and GLOBAL_INIT_LOCK < 12:
				self.control.write(self.control.build(436, 0x81, 0x01, 0x00, 0x80))
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1

			time.sleep(0.1)
		
	def write(self, packet):
		self.control.write(packet)

class Read(threading.Thread):
	def __init__(self, dev, endpoint, config, logger):
		self.device = dev
		self.endpoint = endpoint
		self.config = config
		self.logger = logger
		self.running = False
		self.logger.info("Loaded Read Driver")
		threading.Thread.__init__(self)
	
	def run(self):
		global GLOBAL_INIT_LOCK, MAX_GLOBAL_INIT, GLOBAL_RUNNING
		self.running = True
		self.control = USBControl(self.device, self.logger, self.endpoint)

		self.logger.info("Read Started")

		self.init()

		while self.running:
			if GLOBAL_INIT_LOCK >= 15 and GLOBAL_INIT_LOCK < 16 and GLOBAL_RUNNING:
				time.sleep(2)
				data = self.control.read(440, 2000)
			else:
				time.sleep(0.1)

		self.logger.info("Shutdown Read")

	def shutdown(self):
		self.running = False

	def init(self):
		global GLOBAL_INIT_LOCK, MAX_GLOBAL_INIT

		while self.running and GLOBAL_INIT_LOCK < MAX_GLOBAL_INIT:
			if GLOBAL_INIT_LOCK >= 2 and GLOBAL_INIT_LOCK < 3:
				data = self.control.read(440)
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 4 and GLOBAL_INIT_LOCK < 5:
				data = self.control.read(440)
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 6 and GLOBAL_INIT_LOCK < 7:
				data = self.control.read(440)
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 8 and GLOBAL_INIT_LOCK < 9:
				data = self.control.read(440)
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 10 and GLOBAL_INIT_LOCK < 11:
				data = self.control.read(440)
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 12 and GLOBAL_INIT_LOCK < 13:
				data = self.control.read(440)
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			
			time.sleep(0.1)

class Main(threading.Thread):
	def __init__(self, dev, endpoint, config, write_endpoint, logger):
		self.device = dev
		self.endpoint = endpoint
		self.config = config
		self.write_endpoint = write_endpoint
		self.logger = logger
		self.running = False
		self.block = False
		self.orientate_image = 0
		self.logger.info("Loaded Main Driver")
		threading.Thread.__init__(self)
	
	def _pause(self):
		self.block = True
	
	def _continue(self):
		self.block = False

	def orientate(self, mode):
		self.orientate_image = mode

	def run(self):
		global GLOBAL_INIT_LOCK, GLOBAL_STAT
		self.running = True
		self.control = USBControl(self.device, self.logger, self.endpoint)

		first = 0
		self.init()

		self.logger.info("Main Started")

		layout = False
		if self.config.get('use', False):
			if str(self.config.get('use', '')).upper() == "NODE":
				layout = layouts.Node(self.config, self.logger)
			elif str(self.config.get('use', '')).upper() == "KUBERNETES":
				layout = layouts.Kubernetes(self.config, self.logger)
			else:
				self.logger.critical("no such layout")	
		else:
			self.logger.critical("missing use selector")
		
		if layout:
			if not layout.setup():
				while self.running:
					blocked = False

					if GLOBAL_INIT_LOCK >= 13 and GLOBAL_INIT_LOCK < 14 and not GLOBAL_STAT:
						if first == 0:
							self.write_endpoint.write(self.control.build(435, 0x12, 0x01, 0x00, 0x80, 0x64))
							if first >= 1:
								first = 2
							else:
								first = 1

						image_path = layout.display(self.orientate_image)

						if self.orientate_image > 0:
							image = Image.open(image_path)
							rotated_image = image.rotate(self.orientate_image)
							rotated_image.save(image_path, "JPEG", quality = 80, optimize = True, progressive = False)

						with open(image_path, "rb") as rd:
							index = 0
							start = 0
							pkt_index = 1

							raw_data = rd.read().hex()
							bbytes = list(map(''.join, zip(*[iter(raw_data)]*2)))
							bbytes = ['0x' + x for x in bbytes]
							bbytes = [int(i, 0) for i in bbytes]

							iterations = math.ceil(len(bbytes) / (IMAGE_PACKET_SIZE))

							while index < iterations:
								packets = []
								pkt_command = [ 0x08, pkt_index, 0x00, 0x00 ]

								if index == 0:
									command = [0x08, iterations, 0x00, 0x80]
									if len(bbytes) > start+IMAGE_PACKET_SIZE:
										data = command + bbytes[0:start + IMAGE_PACKET_SIZE]
										packet = self.control.raw_build(0, 0, *data)
										packets.append(packet)
									else:
										data = command + bbytes
										packet = self.control.raw_build(0, IMAGE_PACKET_SIZE + IMAGE_CMD_SIZE - len(data), *data)
										packets.append(packet)
								else:
									if len(bbytes[start:]) > IMAGE_PACKET_SIZE:
										data = pkt_command + bbytes[start:start+IMAGE_PACKET_SIZE]
										packet = self.control.raw_build(0, 0, *data)
										packets.append(packet)
									else:
										data = pkt_command + bbytes[start:]
										packet = self.control.raw_build(0, IMAGE_PACKET_SIZE + IMAGE_CMD_SIZE - len(data), *data)
										packets.append(packet)

								for packet in packets:
									while(self.block):
										blocked = True
										time.sleep(0.25)

									if not blocked:
										self.control.write(packet)

									blocked = False

								if index > 0:
									pkt_index = pkt_index + 1

								index = index + 1
								start = start + IMAGE_PACKET_SIZE

							time.sleep(0.1)

						GLOBAL_STAT = True
					else:
						time.sleep(0.1)

				layout.cleanup()

				self.logger.info("Shutdown Main")
				GLOBAL_STAT = True
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1

	def shutdown(self):
		self.running = False

	def init(self):
		pass

class Trigger(threading.Thread):
	def __init__(self, dev, endpoint, config, logger):
		self.device = dev
		self.endpoint = endpoint
		self.config = config
		self.logger = logger
		self.running = False
		self.logger.info("Loaded Trigger Driver")
		threading.Thread.__init__(self)
	
	def run(self):
		global GLOBAL_INIT_LOCK, GLOBAL_STAT, GLOBAL_RUNNING

		self.logger.info("Trigger Started")

		self.running = True
		self.control = USBControl(self.device, self.logger, self.endpoint)

		self.init()

		while self.running:
			if GLOBAL_INIT_LOCK >= 13 and GLOBAL_INIT_LOCK < 14 and GLOBAL_STAT:
				self.control.read(16, 2000)
				GLOBAL_STAT = False
				GLOBAL_RUNNING = True
			time.sleep(0.1)
		
		# Break out of main loop and perform confirmation read to try and avoid device lockup
		while not GLOBAL_STAT:
			time.sleep(0.1)

		if GLOBAL_INIT_LOCK >= 13 and GLOBAL_INIT_LOCK < 14 and GLOBAL_STAT:
			self.control.read(16, 1000)
			GLOBAL_STAT = False

		self.logger.info("Shutdown Trigger")

	def shutdown(self):
		self.running = False

	def init(self):
		pass

class Control(threading.Thread):
	def __init__(self, dev, config, logger):
		self.device = dev
		self.config = config
		self.logger = logger
		self.running = False
		self.logger.info("Loaded Control Driver")
		threading.Thread.__init__(self)
	
	def run(self):
		self.running = True
		self.control = USBControl(self.device, self.logger)

		try:
			self.init()
		except usb.core.USBTimeoutError as e:
			self.logger.error("USBTimeoutError: please reset your device")
		except usb.core.USBError as e:
			self.logger.error("USBError: please reset your device")

	def shutdown(self):
		self.running = False

	def init(self):
		global GLOBAL_INIT_LOCK, MAX_GLOBAL_INIT

		while self.running and GLOBAL_INIT_LOCK < MAX_GLOBAL_INIT:
			if GLOBAL_INIT_LOCK >= 0 and GLOBAL_INIT_LOCK < 1:
				for index in [0x02, 0x03, 0x02, 0x03, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02]:
					try:
						self.control.descriptor(index, 0x0409)	# 0x0409 == English (United States)
					except usb.core.USBTimeoutError as e:
						self.control.descriptor(index, 0x0409)	# 0x0409 == English (United States)
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			time.sleep(0.1)

class LcdController:
	def __init__(self, config, logger):
		self.config = config
		self.logger = logger
		self.dev = usb.core.find(idVendor = self.config.get('idVendor'), idProduct = self.config.get('idProduct'))
		if self.dev is None:
			raise ValueError('Device not found')
		
		self.logger.info("Loaded LcdController")

	def setup(self):
		try:
			self.configuration = self.dev.get_active_configuration()
		except usb.core.USBError:
			self.configuration = None
		
		if self.configuration is None or self.configuration.bConfigurationValue != DESIRED_CONFIG:
			self.dev.set_configuration(DESIRED_CONFIG)

		if self.dev.is_kernel_driver_active(0):
			try:
				self.dev.detach_kernel_driver(0)
			except usb.core.USBError as e:
				self.logger.error("Could not detatch kernel driver from interface: %s", str(e))
				sys.exit(1)

		if self.dev.is_kernel_driver_active(1):
			try:
				self.dev.detach_kernel_driver(1)
			except usb.core.USBError as e:
				self.logger.error("Could not detatch kernel driver from interface: %s", str(e))
				sys.exit(2)

		self.interfaces = []
		self.interfaces.append(self.configuration[(0, 0)])
		self.interfaces.append(self.configuration[(1, 0)])

		self.endpoints = []
		self.endpoints.append(self.interfaces[0][0])
		self.endpoints.append(self.interfaces[0][1])
		self.endpoints.append(self.interfaces[1][0])
		self.endpoints.append(self.interfaces[1][1])

		self.init()

	def init(self):
		orientation = self.config.get('orientation', '').upper()

		if orientation == "BOTTOM":
			self.orientation = util.ROTATE_BOTTOM
		elif orientation == "LEFT":
			self.orientation = util.ROTATE_LEFT
		elif orientation == "RIGHT":
			self.orientation = util.ROTATE_RIGHT
		else:
			self.orientation = util.ROTATE_TOP

	def run(self):
		global GLOBAL_RUNNING

		self.control = Control(self.dev, self.config, self.logger)
		self.write = Write(self.dev, self.endpoints[0], self.config, self.logger)
		self.read = Read(self.dev, self.endpoints[1], self.config, self.logger)
		self.main = Main(self.dev, self.endpoints[2], self.config, self.write, self.logger)
		self.trigger = Trigger(self.dev, self.endpoints[3], self.config, self.logger)

		self.write.set_class(CLASS_READ, self.read)
		self.write.set_class(CLASS_MAIN, self.main)
		self.write.set_class(CLASS_TRIGGER, self.trigger)

		self.main.orientate(self.orientation)

		self.control.start()
		self.write.start()
		self.read.start()
		self.main.start()
		self.trigger.start()

		self.logger.info("ttlcd is running")

		while not GLOBAL_RUNNING:
			time.sleep(0.1)

		# Wait for Main to exit
		self.main.join()

		# Cleanup
		self.shutdown()

		# Wait for remaining threads to exit
		self.control.join()
		self.write.join()
		self.read.join()

	def shutdown(self):
		self.write.shutdown()
		self.read.shutdown()
		self.main.shutdown()
		self.trigger.shutdown()
		self.control.shutdown()

		usb.util.dispose_resources(self.dev)

def setup_logger(log_file = False, daemon = False):
	logger = logging.getLogger('ttlcd')
	logger.setLevel(logging.INFO)

	if (daemon and log_file) or log_file:
		print(daemon, log_file)
		print("Streaming to log file")
		fh = logging.FileHandler(log_file)
	else:
		print("Streaming to stdout")
		fh = logging.StreamHandler(sys.stdout)

	fh.setLevel(logging.INFO)

	formatstr = '%(asctime)s %(levelname)s %(message)s'
	formatter = logging.Formatter(formatstr)

	fh.setFormatter(formatter)

	logger.addHandler(fh)
	return(logger)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		prog = "ttlcd",
		description = 'Linux controller for the Thermaltake LCD Panel Kit (Tower 200 Mini Chassis Model)',
		epilog = 'Donations are greatly appreciated and can be made at: https://buymeacoffee.com/bekindpleaserewind'
	)

	parser.add_argument('-c', '--config', action = 'store', dest = 'config', help = 'Configuration file for ttlcd', required = True)
	parser.add_argument('-l', '--log-file', action = 'store', dest = 'logfile', help = 'Log file for ttlcd', required = False)
	parser.add_argument('-d', '--daemon', action = 'store_true', dest = 'daemon', help = 'Run as a system daemon', required = False)
	args = parser.parse_args()

	if not args.config or not os.path.exists(args.config):
		print("ttlcd: no such configuration file '%s'", args.config)
		sys.exit(1)

	config = None
	with open(args.config, "r") as fd:
		config = yaml.safe_load(fd.read())

	log_file = False
	if args.logfile:
		log_file =  args.logfile
	else:
		if config.get('log_file', False):
			log_file = config.get('log_file')

	if config.get('daemon', False) or args.daemon:
		with daemon.DaemonContext(umask = 0o077, ):
			logger = setup_logger(log_file, config.get('daemon', False))
			lcd = LcdController(config, logger)
			lcd.setup()
			lcd.run()
			lcd.shutdown()
	else:
		logger = setup_logger(config.get('log_file', False), config.get('daemon', False))
		try:
			lcd = LcdController(config, logger)
			lcd.setup()
			lcd.run()
			lcd.shutdown()
		except KeyboardInterrupt:
			logger.info("Shutting down...")
			lcd.shutdown()
		
	sys.exit(0)