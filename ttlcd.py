import usb.core
import usb.util
import tempfile
import shutil
import struct
import time
import math
import threading
import os
import sys

from PIL import Image

import headers
 
GLOBAL_INIT_LOCK = 0
MAX_GLOBAL_INIT = 15

GLOBAL_STAT = False
GLOBAL_RUNNING = False

CLASS_FIRST = "first"
CLASS_SECOND = "second"
CLASS_THIRD = "third"
CLASS_FOURTH = "fourth"

IMAGE="image.jpg"
IMAGE_PACKET_SIZE = 1020
IMAGE_CMD_SIZE = 4

class TemporaryDirectory(object):
	background = None

	"""Context manager for tempfile.mkdtemp() so it's usable with "with" statement."""
	def __init__(self):
		self.name = tempfile.mkdtemp()
		self.background = os.path.join(self.name, 'background.jpg')

	def __del__(self):
		shutil.rmtree(self.name)

class PreProcessor:
	def __init__(self, image_path):
		self.td = TemporaryDirectory()
		self.image_path = image_path
	
	def init(self):
		self.im = Image.open(self.image_path)
	
	def process(self, dpi = (300,300,), quality = 50, optimize = True):
		self.im.save(self.td.background, dpi = dpi, quality = quality, optimize = optimize)
		return(self.td.background)

class USBControl:
	def __init__(self, dev, endpoint = None):
		self.device = dev
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
			print("Failed to get data for endpoint {}".format(self.endpoint))
		finally:
			self.lock.release()

	def write(self, data = ""):
		try:
			self.lock.acquire()
			self.endpoint.write(data)
		except:
			print("Failed to send data for endpoint {}".format(self.endpoint))
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
			print("Failed to perform control transfer")
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
			a = time.time()
			data = struct.pack(packstr % (len(padding),), *args, padding)
			b = time.time()
			print("Time was {}ms".format(b - a))
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

class First(threading.Thread):
	def __init__(self, dev, endpoint):
		self.device = dev
		self.endpoint = endpoint
		self.classes = {}
		self.running = False
		print("Loaded First Driver")
		threading.Thread.__init__(self)
	
	def set_class(self, class_index, cls):
		self.classes[class_index] = cls

	def run(self):
		global GLOBAL_INIT_LOCK, MAX_GLOBAL_INIT, GLOBAL_RUNNING
		self.running = True
		self.control = USBControl(self.device, self.endpoint)

		self.init()

		while self.running:
			if GLOBAL_INIT_LOCK >= 14 and GLOBAL_INIT_LOCK < 15 and GLOBAL_RUNNING:
				time.sleep(2)
				pkt = self.control.build(436, 0x82, 0x01, 0x00, 0x80)
				self.control.write(pkt)
	
		self.control.write()
	def init(self):
		global GLOBAL_INIT_LOCK, MAX_GLOBAL_INIT

		while GLOBAL_INIT_LOCK < MAX_GLOBAL_INIT:
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
			#if GLOBAL_INIT_LOCK >= 13 and GLOBAL_INIT_LOCK < 14:
			#	for i in range(6):
			#		self.control.write(self.control.build(435, 0x12, 0x01, 0x00, 0x80, 0x64))

			#	self.control.write(self.control.build(435, 0x1a, 0x01, 0x00, 0x80, 0x01))
			#	self.control.write(self.control.build(436, 0x82, 0x01, 0x00, 0x80))

			#	GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1

	def write(self, packet):
		self.control.write(packet)

	def flip(self, orientation):
		print("Changing orientation... ", end="")
		self.classes[CLASS_THIRD]._pause()
		self.control.write(self.control.build(440 - len(headers.FLIP_INIT), *headers.FLIP_INIT))
		self.control.write(self.control.build(440 - len(orientation), *orientation))
		self.classes[CLASS_THIRD]._continue()
		print("done.")
	
	def flip_right(self):
		self.flip(headers.FLIP_RIGHT)

	def flip_left(self):
		self.flip(headers.FLIP_LEFT)

	def flip_up(self):
		self.flip(headers.FLIP_UP)

	def flip_down(self):
		self.flip(headers.FLIP_DOWN)

class Second(threading.Thread):
	def __init__(self, dev, endpoint):
		self.device = dev
		self.endpoint = endpoint
		self.running = False
		print("Loaded Second Driver")
		threading.Thread.__init__(self)
	
	def run(self):
		global GLOBAL_INIT_LOCK, MAX_GLOBAL_INIT, GLOBAL_RUNNING
		self.running = True
		self.control = USBControl(self.device, self.endpoint)

		self.init()

		while self.running:
			if GLOBAL_INIT_LOCK >= 15 and GLOBAL_INIT_LOCK < 16 and GLOBAL_RUNNING:
				time.sleep(2)
				data = self.control.read(440)
	
	def init(self):
		global GLOBAL_INIT_LOCK, MAX_GLOBAL_INIT
		while GLOBAL_INIT_LOCK < MAX_GLOBAL_INIT:
			if GLOBAL_INIT_LOCK >= 2 and GLOBAL_INIT_LOCK < 3:
				data = self.control.read(440)
				print("Second Step 2 data 0x%x 0x%x 0x%x 0x%x 0x%x" % (data[0], data[1], data[2], data[3], data[4]))
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 4 and GLOBAL_INIT_LOCK < 5:
				data = self.control.read(440)
				print("Second Step 4 data 0x%x 0x%x 0x%x 0x%x 0x%x" % (data[0], data[1], data[2], data[3], data[4]))
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 6 and GLOBAL_INIT_LOCK < 7:
				data = self.control.read(440)
				print("Second Step 6 data again 0x%x 0x%x 0x%x 0x%x 0x%x" % (data[0], data[1], data[2], data[3], data[4]))
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 8 and GLOBAL_INIT_LOCK < 9:
				data = self.control.read(440)
				print("Second Step 8 data again 0x%x 0x%x 0x%x 0x%x 0x%x" % (data[0], data[1], data[2], data[3], data[4]))
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 10 and GLOBAL_INIT_LOCK < 11:
				data = self.control.read(440)
				print("Second Step 10 data again 0x%x 0x%x 0x%x 0x%x 0x%x" % (data[0], data[1], data[2], data[3], data[4]))
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			if GLOBAL_INIT_LOCK >= 12 and GLOBAL_INIT_LOCK < 13:
				data = self.control.read(440)
				print("Second Step 12 data 0x%x 0x%x 0x%x 0x%x 0x%x" % (data[0], data[1], data[2], data[3], data[4]))
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			#if GLOBAL_INIT_LOCK >= 14 and GLOBAL_INIT_LOCK < 15:
			#	data = self.control.read(440)
			#	print("Second Step 14 data 0x%x 0x%x 0x%x 0x%x 0x%x" % (data[0], data[1], data[2], data[3], data[4]))
			#	GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1

class Third(threading.Thread):
	def __init__(self, dev, endpoint, first_endpoint):
		self.device = dev
		self.endpoint = endpoint
		self.first_endpoint = first_endpoint
		self.running = False
		self.block = False
		print("Loaded Third Driver")
		threading.Thread.__init__(self)
	
	def _pause(self):
		self.block = True
	
	def _continue(self):
		self.block = False


	def run(self):
		global GLOBAL_INIT_LOCK, GLOBAL_STAT, IMAGE
		self.running = True
		self.control = USBControl(self.device, self.endpoint)

		first = 0
		self.init()

		while self.running:
			blocked = False

			if GLOBAL_INIT_LOCK >= 13 and GLOBAL_INIT_LOCK < 14 and not GLOBAL_STAT: 
				#if first == 0 or first == 1:
				if first == 0:
					print("!!!!!!!!!!!!!!!!! WRITING UPLOAD PACKET")
					self.first_endpoint.write(self.control.build(435, 0x12, 0x01, 0x00, 0x80, 0x64))
					if first >= 1:
						first = 2
					else:
						first = 1

				print("!!!!!!!!!!!!!!!!!!!! Opening Image {}".format(IMAGE))

				with open(IMAGE, "rb") as rd:
					index = 0
					start = 0
					pkt_index = 1


					raw_data = rd.read().hex()
					bbytes = list(map(''.join, zip(*[iter(raw_data)]*2)))
					bbytes = ['0x' + x for x in bbytes]
					bbytes = [int(i, 0) for i in bbytes]
					iterations = math.ceil(len(bbytes) / (IMAGE_PACKET_SIZE))

					print("Read in {} bytes from {} for a total of {} packets".format(len(bbytes), IMAGE, iterations))

					total_bytes = 0

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
								print("Blocking writing packets")
								blocked = True
								time.sleep(0.1)

							if not blocked:
								self.control.write(packet)

							blocked = False

						if index > 0:
							pkt_index = pkt_index + 1

						index = index + 1
						start = start + IMAGE_PACKET_SIZE

				print("Writing {} image packets".format(len(packets)))
				print("Processed a total of {} bytes".format(total_bytes))

				#while True:
				#	time.sleep(0.1)

				
				GLOBAL_STAT = True
	
	def init(self):
		pass

class Fourth(threading.Thread):
	def __init__(self, dev, endpoint):
		self.device = dev
		self.endpoint = endpoint
		self.running = False
		print("Loaded Fourth Driver")
		threading.Thread.__init__(self)
	
	def run(self):
		global GLOBAL_INIT_LOCK, GLOBAL_STAT, GLOBAL_RUNNING
		self.running = True
		self.control = USBControl(self.device, self.endpoint)

		self.init()

		while self.running:
			if GLOBAL_INIT_LOCK >= 13 and GLOBAL_INIT_LOCK < 14 and GLOBAL_STAT:
				print("READ FOURTH PACKET")
				data = self.control.read(16)
				GLOBAL_STAT = False
				GLOBAL_RUNNING = True

	def init(self):
		pass

class Control(threading.Thread):
	def __init__(self, dev):
		self.device = dev
		self.running = False
		print("Loaded Control Driver")
		threading.Thread.__init__(self)
	
	def run(self):
		self.running = True
		self.control = USBControl(self.device)

		self.init()

		while self.running:
			#self.control.write()
			time.sleep(2)
	
	def init(self):
		global GLOBAL_INIT_LOCK, MAX_GLOBAL_INIT

		while GLOBAL_INIT_LOCK < MAX_GLOBAL_INIT:
			if GLOBAL_INIT_LOCK >= 0 and GLOBAL_INIT_LOCK < 1:
				for index in [0x02, 0x03, 0x02, 0x03, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02]:
					self.control.descriptor(index, 0x0409)	# 0x0409 == English (United States)
				GLOBAL_INIT_LOCK = GLOBAL_INIT_LOCK + 1
			#time.sleep(0.1)

class LcdController:
	def __init__(self):
		self.dev = usb.core.find(idVendor=0x264a, idProduct=0x233d)
		self.background = None

		if self.dev is None:
			raise ValueError('Device not found')

	def setup(self):
		self.configuration = self.dev.get_active_configuration()

		if self.dev.is_kernel_driver_active(0):
			try:
				self.dev.detach_kernel_driver(0)
			except usb.core.USBError as e:
				sys.exit("Could not detatch kernel driver from interface: {0}".format(str(e)))

		if self.dev.is_kernel_driver_active(1):
			try:
				self.dev.detach_kernel_driver(1)
			except usb.core.USBError as e:
				sys.exit("Could not detatch kernel driver from interface: {0}".format(str(e)))

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
		# Initialize background image
		#self.pp = PreProcessor(IMAGE)
		#self.pp.init()
		#self.background = self.pp.process()
		pass


	def run(self):
		global GLOBAL_RUNNING, IMAGE

		#IMAGE = self.background

		control = Control(self.dev)
		first = First(self.dev, self.endpoints[0])
		second = Second(self.dev, self.endpoints[1])
		third = Third(self.dev, self.endpoints[2], first)
		fourth = Fourth(self.dev, self.endpoints[3])

		first.set_class(CLASS_SECOND, second)
		first.set_class(CLASS_THIRD, third)
		first.set_class(CLASS_FOURTH, fourth)

		control.start()
		first.start()
		second.start()
		third.start()
		fourth.start()

		while not GLOBAL_RUNNING:
			time.sleep(0.1)

		#time.sleep(5)
		#first.flip_up()
		#time.sleep(5)
		#first.flip_down()
		#time.sleep(5)
		#first.flip_left()
		#time.sleep(5)
		#first.flip_right()
		#time.sleep(5)
		#first.flip_up()

		control.join()
		first.join()
		second.join()
		third.join()
		fourth.join()


if __name__ == "__main__":
	fuzzer = LcdController()
	fuzzer.setup()
	fuzzer.run()
