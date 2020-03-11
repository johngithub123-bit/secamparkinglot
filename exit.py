from mysql.connector import (connection)
import time
import serial
import RPi.GPIO as GPIO
import os
import datetime
from ftplib import FTP
import sys
import smbus

CARD_DEV = '/dev/ttyUSB0'
DISPLAY_DEV = '/dev/ttyUSB1'
BARCODE_DEV = '/dev/ttyUSB2'

reader = serial.Serial(   
    port=CARD_DEV,
    baudrate = 9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

display = serial.Serial(   
    port=DISPLAY_DEV,
    baudrate = 9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

barcode_reader = serial.Serial(   
    port=BARCODE_DEV,
    baudrate = 9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)


I2C_ADDRESS = 0x20
bus = smbus.SMBus(1)
bus.write_byte_data(I2C_ADDRESS, 0x00, 0x00)

Barrier1 = 0x80
Barrier2 = 0x40
LPR_CONTROL = 0x04		# LPR Control
DENYLED = 0x08

relay_status = 0x00

# define messages
lprcode_msg = "No Plate"
MySqlStatusOn_msg = "MySql is connected"
MySqlStatusOff_msg = "MySql is disconnected"
ParkingLot_msg = "PARKING P7"
Welcome_msg = "Welcome"
LprNotDetected_msg = "Camera not detected"

# define ftp 
SERVER = '192.168.0.160'
PORT = '21'
USERNAME = 'admin'
PASS = 'admin'

Loop0 = 22		# GPIO22
Loop1 = 04		# GPIO04
Loop2 = 17		# GPIO17
Loop3 = 27		# GPIO27
# B1STATELED = 21		# GPIO21 control barrier 1
# L2STATELED = 20		# GPIO20 LOOP2 Signal
# B2STATELED = 16		# GPIO16 ACEPTED (RFID, or Ticket or Plate) this is conected like Barrier2
# DENYLED = 26  		# GPIO26 NOT ACEPTED(RFID, or Ticket or Plate) Access Denay
BUTTON = 23			# GPI23 PRINTING
LPR_TRIGGER = 24	# LPR Trigger singal

GPIO.setmode(GPIO.BCM)
GPIO.setup(Loop0,GPIO.IN)
GPIO.setup(Loop1,GPIO.IN)
GPIO.setup(Loop2,GPIO.IN)
GPIO.setup(Loop3,GPIO.IN)
GPIO.setup(BUTTON,GPIO.IN)
GPIO.setup(LPR_TRIGGER,GPIO.IN)
#State led init
# GPIO.setup(B1STATELED, GPIO.OUT) NO NEED
# GPIO.setup(L2STATELED, GPIO.OUT)NO NEED
# GPIO.setup(B2STATELED, GPIO.OUT)NO NEED
# GPIO.setup(DENYLED, GPIO.OUT)

DIR_PATH = '/home/pi/FTP/home/pi/FTP/PARKING_07/'

#define display funtionton
def displayMsg(displayvalue):
	command = bytearray([0x52, 0x52, 0xB2])
	display.write(command)
	command = bytearray(displayvalue, encoding = "utf-8")
	display.write(command)

connctionState = 0;

historyFile = open('histroyInfo.txt', 'a')
historyFile.write('^XA^FO25,50^XGE:LOGO1.GRF ^FS\n')
tick_minute = datetime.datetime.now().minute

query = "select PythonVariable, Message from DisplayMessages"
try:
	cnx = connection.MySQLConnection(user='ZKAgent', password='Loka123',
		                                 host='192.168.0.160',
		                                 database='zk_parking')
	cursor = cnx.cursor()
	cursor.execute(query)
	rows = cursor.fetchall()
	connctionState = 1
	for row in rows:
		variable = row[0]
		msg = row[1]
		if variable == 'lprcode':
			lprcode_msg = row[1]
		elif variable == 'MySqlStatusOn':
			MySqlStatusOn_msg = row[1]
		elif variable == 'MySqlStatusOff':
			MySqlStatusOff_msg = str(row[1])
		elif variable == 'ParkingLot':
			ParkingLot_msg = row[1]
		elif variable == 'Welcome':
			Welcome_msg = row[1]
		elif variable == 'LprNotDetected':
			LprNotDetected_msg = row[1]
except Exception as e:
	displayMsg(MySqlStatusOff_msg)
	connctionState = 0

lprcode = "No Plate"
lpr_filepath = ''
ftp_file_case = ''
# variables for image url
compared_option = 0			# 0 - no, 1 - log table, 2 - ticket table
compared_value = ''			# compared, 1 - vehicle id , 2 -barcode
while 1:
	relay_status = relay_status & (~DENYLED)
	bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
	# GPIO.output(DENYLED, GPIO.LOW)

	# FTP
	if lpr_filepath != '':
		ftp = FTP(SERVER, USERNAME, PASS)
		timestamp = "%04d%02d%02d"%(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)
		try:
			ftp.cwd('/PARKING_07/' + timestamp)
		except Exception as ex:
			ftp.mkd('/PARKING_07/' + timestamp)
			ftp.cwd('/PARKING_07/' + timestamp)

		lpr_file = open(DIR_PATH + lpr_filepath, 'rb')
		print("To ftp: " + timestamp + '/' + ftp_file_case)
		ftp.storbinary('STOR ' + ftp_file_case, lpr_file)
		ftp.quit()
		ftp.close()
		lpr_filepath = ''

		# Image url
		if compared_option == 1:
			query = "update log set ImageURL = \'" + timestamp + '/' + ftp_file_case+ "\' where VehicleID = \'" + compared_value + "\'"
		elif compared_option == 2:
			query = "update ticket set ImageURLexit = \'" + timestamp + '/' + ftp_file_case+ "\' where BarCode = " + compared_value
		
		if compared_option != 0:
			try:
				cursor.execute(query)
				cnx.commit()		
			except Exception as exc:
				print("MySql is disconnected")			
				# displayMsg("MySql is disconnected")
				time.sleep(0.02)
				displayMsg("")
				time.sleep(0.02)
				displayMsg(MySqlStatusOff_msg)
				connctionState = 0
				# GPIO.output(DENYLED, GPIO.HIGH)
				relay_status = relay_status | DENYLED
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				time.sleep(0.3)
				continue
		compared_option = 0
		compared_value = ''

	if connctionState == 0:
		# GPIO.output(Barrier1, GPIO.HIGH)	# close the barrier1 and barrier2
		# GPIO.output(Barrier2, GPIO.LOW)
		# GPIO.output(B1STATELED, GPIO.HIGH)
		relay_status = relay_status | Barrier1
		relay_status = relay_status & (~Barrier2)
		bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

		try:
			cnx = connection.MySQLConnection(user='ZKAgent', password='Loka123',
			                                 host='192.168.0.160',
			                                 database='zk_parking')
			cursor = cnx.cursor()
			# displayMsg("MySql is connected")
			time.sleep(0.02)
			displayMsg("")
			time.sleep(0.02)
			displayMsg(MySqlStatusOn_msg)
			connctionState = 1

			today = datetime.datetime.now()
			historyFile = open('histroyInfo.txt', 'a')
			str1 = 'Connected: %d. %s. %d \&\n'%(today.day, today.strftime('%B')[0:3], today.year)
			historyFile.write(str1)
			str1 = ' TIME: %02d:%02d:%02d^FS\n'%(today.hour, today.minute, today.second)
			historyFile.write(str1)
			historyFile.close()

		except Exception as ex:
			connctionState = 0
			# displayMsg("MySql is disconnected")
			time.sleep(0.02)
			displayMsg("")
			time.sleep(0.02)
			displayMsg(MySqlStatusOff_msg)
			time.sleep(3)
			# GPIO.output(L2STATELED, ~(GPIO.input(Loop2)))
			if GPIO.input(Loop1) == 0 or GPIO.input(Loop2) == 0:
				# GPIO.output(Barrier1, GPIO.HIGH)		# Barrier1 is open
				# GPIO.output(Barrier2, GPIO.LOW)			# Barrier2 is close
				relay_status = relay_status | Barrier1
				relay_status = relay_status & (~Barrier2)
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				# GPIO.output(B1STATELED, GPIO.HIGH)
			else:
				# GPIO.output(Barrier1, GPIO.LOW)		# Barrier1 is open
				# GPIO.output(Barrier2, GPIO.LOW)			# Barrier2 is close
				relay_status = relay_status & (~Barrier1)
				relay_status = relay_status & (~Barrier2)
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				# GPIO.output(B1STATELED, GPIO.LOW)

			today = datetime.datetime.now()
			historyFile = open('histroyInfo.txt', 'a')
			str1 = 'Disconnected: %d. %s. %d \&\n'%(today.day, today.strftime('%B')[0:3], today.year)
			historyFile.write(str1)
			str1 = ' TIME: %02d:%02d:%02d^FS\n'%(today.hour, today.minute, today.second)
			historyFile.write(str1)
			historyFile.close()

			continue

	# check the mysql state
	if tick_minute != datetime.datetime.now().minute:
		tick_minute = datetime.datetime.now().minute
		query = "SELECT NOW() as reply"
		try:
			cursor.execute(query)
			cursor.fetchall()
		except Exception as exc:
			connctionState = 0;
			# displayMsg("MySql is disconnected")
			time.sleep(0.02)
			displayMsg("")
			time.sleep(0.02)
			displayMsg(MySqlStatusOff_msg)
			continue

	# Initial state
	print("\n ----- Initial State, waiting for the car ------")
	# displayMsg("PARKING P7")
	time.sleep(0.02)
	displayMsg("")
	time.sleep(0.02)
	displayMsg(ParkingLot_msg)
	# GPIO.output(Barrier1, GPIO.HIGH)		# Barrier1 is open
	# GPIO.output(Barrier2, GPIO.LOW)			# Barrier2 is close
	# GPIO.output(LPR_CONTROL, GPIO.LOW)		# Stop LPR

	relay_status = relay_status | Barrier1
	relay_status = relay_status & (~Barrier2)
	relay_status = relay_status & (~LPR_CONTROL)
	bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

	# GPIO.output(B1STATELED, GPIO.HIGH)
	while GPIO.input(Loop1) == 1:
		continue

	time.sleep(0.02)
	displayMsg("")
	time.sleep(0.02)
	displayMsg(Welcome_msg)

	# when the car is in Loop2
	# GPIO.output(L2STATELED, ~(GPIO.input(Loop2)))
	while GPIO.input(Loop2) == 1:
		continue
	# GPIO.output(L2STATELED, ~(GPIO.input(Loop2)))
	time.sleep(0.02)
	displayMsg("")
	time.sleep(0.02)
	print("The car is in loop2")	
	displayMsg("Skeniranje tablica ...")

	# GPIO.output(Barrier1, GPIO.LOW)	# close the barrier1 and barrier2
	# GPIO.output(Barrier2, GPIO.LOW)
	relay_status = relay_status & (~Barrier1)
	relay_status = relay_status & (~Barrier2)
	bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

	# processing lpr
	files = os.listdir(DIR_PATH)
	for file in files:
		if file != "test":
			path = DIR_PATH + file
			os.remove(path)

	# GPIO.output(LPR_CONTROL, GPIO.HIGH)		# enable the lpr
	relay_status = relay_status | LPR_CONTROL
	bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

	tick_camera = datetime.datetime.now().second
	camera_broken = 0
	while GPIO.input(LPR_TRIGGER) == 1:		
		now_camera = datetime.datetime.now().second
		if now_camera >= tick_camera:
			difference_camera = now_camera - tick_camera
		else:
			difference_camera = now_camera + 60 - tick_camera
		if difference_camera > 5:
			camera_broken = 1
			break
		pass
		
	if camera_broken == 0:				
		print "Car is detected"
		lprcode = "No Plate"
		tick_camera = datetime.datetime.now().second
		lpr_filepath = ''
		while lprcode == "No Plate":
			files = os.listdir(DIR_PATH)
			if len(files) > 1:
				for file in files:
					camera_value = file.split("_")[0]
					if camera_value != 'test':
						lpr_filepath = file
						if camera_value != "No Plate":
							lprcode = camera_value
							break
			now_camera = datetime.datetime.now().second
			if now_camera >= tick_camera:
				difference_camera = now_camera - tick_camera
			else:
				difference_camera = now_camera + 60 - tick_camera
			if difference_camera > 7:
				camera_broken = 1
				break
		
	if camera_broken == 0:
		time.sleep(0.02)
		displayMsg("")
		time.sleep(0.02)
		print(lprcode + " is detected.")
		displayMsg(lprcode)
		ftp_file_case = lprcode + '.jpg'
	else:
		lprcode = "No Plate"
		# time.sleep(0.02)
		# displayMsg("")
		# time.sleep(0.02)
		print("Camera not detect")
		# displayMsg("Camera not detect")
		# displayMsg(LprNotDetected_msg)
		ftp_file_case = 'noplate.jpg'

	# GPIO.output(LPR_CONTROL, GPIO.LOW)
	relay_status = relay_status & (~LPR_CONTROL)
	bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

	if GPIO.input(Loop1) == 0 or GPIO.input(Loop0) == 0:				#vlada test
		print("barrier1 is open waiting to close. move your vehicle little forward or another vehicle is on the barrier1")
		time.sleep(0.02)
		displayMsg("")
		time.sleep(0.02)
		displayMsg("Until car is entered, leave loop1")
		while GPIO.input(Loop1) == 0 or GPIO.input(Loop0) == 0:			# if another car is in loop 1
			continue
		# while GPIO.input(Loop0) == 0:
		# 	continue

	# time.sleep(0.02)
	# displayMsg("")
	# time.sleep(0.02)
	print ("Ready. All barriers are closing.")
	# displayMsg("Ready. Checking the database.")
	# GPIO.output(B1STATELED, GPIO.LOW)

	# LPR state decide for car
	if lprcode != "No Plate":
		query = "select status, name from vehicles where licencePlates = \'" + lprcode + "\'"
		try:
			cursor.execute(query)
			rows = cursor.fetchall()
		except Exception as exc:
			print("MySql is disconnected")
			# displayMsg("MySql is disconnected")
			time.sleep(0.02)
			displayMsg("")
			time.sleep(0.02)
			displayMsg(MySqlStatusOff_msg)
			connctionState = 0
			# GPIO.output(DENYLED, GPIO.HIGH)
			relay_status = relay_status | DENYLED
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
			time.sleep(1)
			continue

		if cursor.rowcount == 0:
			# time.sleep(0.02)
			# displayMsg("")
			# time.sleep(0.02)
			print(lprcode + " is not existed in database.")		# go to the button for thermal printer
			# displayMsg(lprcode + " is not existed in database.")
			# GPIO.output(DENYLED, GPIO.HIGH)
			relay_status = relay_status | DENYLED
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

			time.sleep(0.3)
		else:
			row = rows[0]
			status = row[0]
			vehicle_name = row[1]
			print("Status value is " + str(status))
			if status == 0:
				print("This car is already out. Please try another card or get the ticket from the service.")		# go to the button for thermal printer
				# time.sleep(0.02)
				# displayMsg("")
				# time.sleep(0.02)
				# displayMsg("Already in. Please try another card or get the ticket")
				# GPIO.output(DENYLED, GPIO.HIGH)
				relay_status = relay_status | DENYLED
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

				time.sleep(1)
			else:	
				query = "select v.card, c.MaxParked, c.Inside, c.id from company c inner join vehicles v on v.idDept = c.id where v.licencePlates = \'" + lprcode + "\'"
				try:
					cursor.execute(query)
					row = cursor.fetchone()
				except Exception as exc:
					print("MySql is disconnected")
					# displayMsg("MySql is disconnected")
					time.sleep(0.02)
					displayMsg("")
					time.sleep(0.02)
					displayMsg(MySqlStatusOff_msg)
					connctionState = 0
					# GPIO.output(DENYLED, GPIO.HIGH)
					relay_status = relay_status | DENYLED
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

					time.sleep(0.3)
					continue

				MaxParked = row[1]
				Inside = row[2]
				companyId = row[3]
				print("MaxParked: " + str(MaxParked) + "  Inside: " + str(Inside))
	
				time.sleep(0.02)
				displayMsg("")
				time.sleep(0.02)
				print("You can exit your car")
				displayMsg(lprcode + ": Mzete proci")
				query = "update vehicles set status = 0 where licencePlates = '" + lprcode + "'"
				print("updating the status")
				try:
					cursor.execute(query)
					cnx.commit()		
				except Exception as exc:
					print("MySql is disconnected")			
					# displayMsg("MySql is disconnected")
					time.sleep(0.02)
					displayMsg("")
					time.sleep(0.02)
					displayMsg(MySqlStatusOff_msg)
					connctionState = 0
					# GPIO.output(DENYLED, GPIO.HIGH)
					relay_status = relay_status | DENYLED
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

					time.sleep(0.3)
					continue

				query = "update company set Inside = " + str(Inside - 1) + " where id = '" + str(companyId) + "'"
				print("upddating the Inside")
				try:
					cursor.execute(query)
					cnx.commit()		
				except Exception as exc:
					print("MySql is disconnected")		
					# displayMsg("MySql is disconnected")
					time.sleep(0.02)
					displayMsg("")
					time.sleep(0.02)
					displayMsg(MySqlStatusOff_msg)
					connctionState = 0
					# GPIO.output(DENYLED, GPIO.HIGH)
					relay_status = relay_status | DENYLED
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

					time.sleep(0.3)
					continue

								# saving log
				today = datetime.datetime.now()
				CheckTime = "%04d-%02d-%02d %02d:%02d:%02d"%(today.year, today.month, today.day, today.hour, today.minute, today.second)
				query = "INSERT INTO log (CheckTime, VehicleID, CheckType, ParkingLot, VerificationType) VALUES (\'" + CheckTime + "\', \'" + vehicle_name + "\', 1, \'P7\', 1);"
				print("inserting the log")
				try:
					cursor.execute(query)
					cnx.commit()		
				except Exception as exc:			
					displayMsg("MySql is disconnected")
					print("MySql is disconnected")
					# displayMsg("MySql is disconnected")
					time.sleep(0.02)
					displayMsg("")
					time.sleep(0.02)
					displayMsg(MySqlStatusOff_msg)
					connctionState = 0
					# GPIO.output(DENYLED, GPIO.HIGH)
					relay_status = relay_status | DENYLED
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

					time.sleep(0.3)
					continue

				# GPIO.output(Barrier2,GPIO.HIGH)
				relay_status = relay_status | Barrier2
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				# GPIO.output(B2STATELED, GPIO.HIGH)
				time.sleep(0.02)
				displayMsg("")
				time.sleep(0.02)
				print("Waiting for passing the barrier2...")
				displayMsg("Waiting for passing the barrier2...")
				time.sleep(3)
				while GPIO.input(Loop2) == 0:
					print "."
					time.sleep(1)
				while GPIO.input(Loop3) == 1:
					print "."
					time.sleep(1)
				while GPIO.input(Loop3) == 0:
					print "."
					time.sleep(1)
				# GPIO.output(L2STATELED, ~(GPIO.input(Loop2)))
				time.sleep(0.02)
				displayMsg("")
				time.sleep(0.02)
				print("Successfully Exited!")
				displayMsg("Successfully Exited!")
				ftp_file_case = "%04d%02d%02d_%s"%(today.year, today.month, today.day, ftp_file_case)
				compared_option = 1
				compared_value = vehicle_name
				continue		

	time.sleep(3.02)
	displayMsg("")
	time.sleep(0.02)
	
	print("Please attach card to the reader or check barcode")
	displayMsg("Prinesite karticu ili uzmite TIKET")
	# now car is in loop2 and checkng the rfid card
	while 1:
		x0 = ""
		barcode = ''
		x0 = reader.readline()
		barcode = barcode_reader.readline()
		# waiting for no card data or no button
		if GPIO.input(Loop2) == 1:
			break
		while len(x0) == 0 and len(barcode) == 0:
			x0 = reader.readline()
			barcode = barcode_reader.readline()

		# When punch the card
		if len(x0) != 0:
			strX0 = "%08x" % int(x0, 10)
			strX0 = strX0[6:8] + strX0[4:6] + strX0[2:4] + strX0[0:2]
			strX0 = "%010d" % int(strX0, 16)
			print("Card Number: " + strX0)
			# displayMsg("Card Number: " + strX0)

			# check in database
			query = "select status, name from vehicles where card = " + strX0
			try:
				cursor.execute(query)
				rows = cursor.fetchall()
			except Exception as exc:
				rows = []
				displayMsg("MySql is disconnected")
				# displayMsg("MySql is disconnected")
				displayMsg(MySqlStatusOff_msg)
				connctionState = 0
				# GPIO.output(DENYLED, GPIO.HIGH)
				relay_status = relay_status | DENYLED
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				time.sleep(1)
				break

			if cursor.rowcount != 1:
				print("The card " + strX0 + " is not existed. Please try another card or get the ticket from the service.")		# go to the button for thermal printer
				displayMsg("CARD NOT VALID get the ticket")
				# GPIO.output(DENYLED, GPIO.HIGH)
				relay_status = relay_status | DENYLED
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				time.sleep(0.3)
				# GPIO.output(Barrier1, GPIO.HIGH)
				relay_status = relay_status | Barrier1
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				continue
			else:
				row = rows[0]
				status = row[0]
				vehicle_name = row[1]
				print("Status value is " + str(status))
				if status == 0:
					print("This car is already out. Please try another card or get the ticket from the service.")		# go to the button for thermal printer
					displayMsg("Vozilo je vec registrovano. Pokusajte sa drugom karticom ili uzmite TIKET")
					# GPIO.output(DENYLED, GPIO.HIGH)
					relay_status = relay_status | DENYLED
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
					time.sleep(1)
					# GPIO.output(Barrier1, GPIO.HIGH)
					relay_status = relay_status | Barrier1
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
					continue
				else:					
					query = "select v.card, c.MaxParked, c.Inside, c.id from company c inner join vehicles v on v.idDept = c.id where v.card = " + strX0
					try:
						cursor.execute(query)
						row = cursor.fetchone()
					except Exception as exc:
						# displayMsg("MySql is disconnected")
						displayMsg(MySqlStatusOff_msg)
						print("MySql is disconnected")
						connctionState = 0
						# GPIO.output(DENYLED, GPIO.HIGH)
						relay_status = relay_status | DENYLED
						bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
						time.sleep(0.3)
						break

					MaxParked = row[1]
					Inside = row[2]
					companyId = row[3]
					print("MaxParked: " + str(MaxParked) + "  Inside: " + str(Inside))

					query = "update vehicles set status = 0 where card = '" + strX0 + "'"
					
					try:
						cursor.execute(query)
						cnx.commit()		
					except Exception as exc:			
						# displayMsg("MySql is disconnected")
						displayMsg(MySqlStatusOff_msg)
						print("MySql is disconnected")
						connctionState = 0
						# GPIO.output(DENYLED, GPIO.HIGH)
						relay_status = relay_status | DENYLED
						bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
						time.sleep(0.3)
						break

					query = "update company set Inside = " + str(Inside - 1) + " where id = '" + str(companyId) + "'"
					
					try:
						cursor.execute(query)
						cnx.commit()		
					except Exception as exc:			
						# displayMsg("MySql is disconnected")
						displayMsg(MySqlStatusOff_msg)
						print("MySql is disconnected")
						connctionState = 0
						# GPIO.output(DENYLED, GPIO.HIGH)
						relay_status = relay_status | DENYLED
						bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
						time.sleep(0.3)
						break

					# saving log
					today = datetime.datetime.now()
					CheckTime = "%04d-%02d-%02d %02d:%02d:%02d"%(today.year, today.month, today.day, today.hour, today.minute, today.second)
					query = "INSERT INTO log (CheckTime, VehicleID, CheckType, ParkingLot, VerificationType) VALUES (\'" + CheckTime + "\', \'" + vehicle_name + "\', 1, \'P7\', 0)"
					print(query)
					try:
						cursor.execute(query)
						cnx.commit()		
					except Exception as exc:			
						# displayMsg("MySql is disconnected")
						displayMsg(MySqlStatusOff_msg)
						print("MySql is disconnected")
						connctionState = 0
						# GPIO.output(DENYLED, GPIO.HIGH)
						relay_status = relay_status | DENYLED
						bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
						time.sleep(0.3)
						break

					# GPIO.output(Barrier1,GPIO.LOW)
					# GPIO.output(Barrier2,GPIO.HIGH)
					relay_status = relay_status & (~Barrier1)
					relay_status = relay_status | Barrier2
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
					# GPIO.output(B2STATELED, GPIO.HIGH)
					print("Waiting for passing the barrier2...")
					displayMsg("OK ! Slobodan prolaz Hvala.  Napustite zonu rampe ...")
					time.sleep(3)
					while GPIO.input(Loop2) == 0:
						print "."
						time.sleep(1)
					while GPIO.input(Loop3) == 1:
						print "."
						time.sleep(1)
					while GPIO.input(Loop3) == 0:
						print "."
						time.sleep(1)
					# GPIO.output(L2STATELED, ~(GPIO.input(Loop2)))
					print("Successfully Exited!")
					displayMsg("Successfully Exited!")

					ftp_file_case = "%04d%02d%02d_%s"%(today.year, today.month, today.day, ftp_file_case)
					compared_option = 1
					compared_value = vehicle_name
					# GPIO.output(B2STATELED, GPIO.LOW)
					break		
					
		if len(barcode) != 0:
			barcode = barcode.rstrip()
			print(barcode)

			query = "select StatusTicket_pay, StatusCar_in from ticket where barcode = " + barcode
			try:
				cursor.execute(query)
				rows = cursor.fetchall()
			except Exception as exc:			
				# displayMsg("MySql is disconnected")
				displayMsg(MySqlStatusOff_msg)
				print("MySql is disconnected")
				connctionState = 0
				# GPIO.output(DENYLED, GPIO.HIGH)
				relay_status = relay_status | DENYLED
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				time.sleep(0.3)
				break
			# the button is pressed
			print("barcode is checking....")
			displayMsg(barcode)

			if cursor.rowcount != 1:
				print("NO EXIST TICKET GO BACK OR PUNCH ANOTHER TICKET")
				displayMsg("NO EXIST TICKET GO BACK OR PUNCH ANOTHER TICKET")
				# GPIO.output(Barrier1, GPIO.HIGH)
				relay_status = relay_status | Barrier1
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				continue


			row = rows[0]
			StatusTicket_pay = row[0]
			StatusCar_in = row[1]
			if StatusTicket_pay == 0 or StatusCar_in == 0:
				print("Already out or Not Paid. please go back")
				displayMsg("Already out. please go back")
				# GPIO.output(Barrier1, GPIO.HIGH)
				relay_status = relay_status | Barrier1
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

				continue
			today = datetime.datetime.now()
			print("Updating database")
			LeaveTime = "%04d-%02d-%02d %02d:%02d:%02d"%(today.year, today.month, today.day, today.hour, today.minute, today.second)
			query = "update ticket set StatusCar_in = 0, LeaveTime = \'" + LeaveTime + "\' where BarCode = " + barcode
			
			try:
				cursor.execute(query)
				cnx.commit()		
			except Exception as exc:			
				print str(exc)
				# displayMsg("MySql is disconnected")
				displayMsg(MySqlStatusOff_msg)
				print("MySql is disconnected")
				connctionState = 0
				# GPIO.output(DENYLED, GPIO.HIGH)
				relay_status = relay_status | DENYLED
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

				time.sleep(0.3)
				break

			print("******* Sucessfully passed *******")
			
			# GPIO.output(Barrier1,GPIO.LOW)
			# GPIO.output(Barrier2,GPIO.HIGH)
			relay_status = relay_status & (~Barrier1)
			relay_status = relay_status | Barrier2
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

			# GPIO.output(B2STATELED, GPIO.HIGH)
			print("Waiting for passing the barrier2...")
			displayMsg("Slobodan Prolaz HVALA. Napustite zonu rampe !")
			time.sleep(3)
			while GPIO.input(Loop2) == 0:
				print "."
				time.sleep(1)
			while GPIO.input(Loop3) == 1:
				print "."
				time.sleep(1)
			while GPIO.input(Loop3) == 0:
				print "."
				time.sleep(1)
			# GPIO.output(L2STATELED, ~(GPIO.input(Loop2)))
			print("Successfully Exited!")
			displayMsg("AIRPORT BELGRADE")

			ftp_file_case = "%s_%s"%(barcode, ftp_file_case)
			compared_option = 2
			compared_value = barcode
			break
			# GPIO.output(B2STATELED, GPIO.LOW)

	
