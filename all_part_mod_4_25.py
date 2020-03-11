from mysql.connector import (connection)
import time
import serial
import RPi.GPIO as GPIO
import os
import datetime
from ftplib import FTP
import sys
import smbus

# BARCODE_DEV = '/dev/ttyUSB2'
CARD_DEV = '/dev/ttyUSB1'
DISPLAY_DEV = '/dev/ttyUSB0'

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


I2C_ADDRESS = 0x20
bus = smbus.SMBus(1)
bus.write_byte_data(I2C_ADDRESS, 0x00, 0x00)

Barrier1 = 0x80
Barrier2 = 0x40
LPR_CONTROL = 0x04		# LPR Control
DENYLED = 0x08
BUTTON_LIGHT = 0x10

relay_status = 0x00

# define messages
lprcode_msg = "No Plate"
MySqlStatusOn_msg = "MySql is connected"
MySqlStatusOff_msg = "MySql is disconnected"
ParkingLot_msg = "PARKING P8"
Welcome_msg = "PARKING P8"
LprNotDetected_msg = "Camera not detected"

# define ftp 
SERVER = '192.168.0.158'
PORT = '21'
USERNAME = 'parking'
PASS = 'parking'

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

picture_status = 1
initial_time = datetime.datetime.now().second

def set_picture(a):
	global picture_status
	picture_status = a

def set_initialtime(a):
	global initial_time
	initial_time = a

#define display funtionton
def displayMsg(displayvalue, eachimage):
	global picture_status
	global initial_time
	if displayvalue == "":
		return
	image_path = eachimage

	if displayvalue == 'screensaver':
		print('screensaver')
		if initial_time - datetime.datetime.now().second > 3:
			image_path = 'screensaver.png'
		elif datetime.datetime.now().second - initial_time > 3:
			image_path = 'screensaver.png'
		else:
			return
	os.system('python createUI.py ' + image_path + ' ' + displayvalue)
	#print('python createUI.py ' + image_path + ' ' + displayvalue)

# displayMsg("test")
connctionState = 0;

historyFile = open('histroyInfo.txt', 'a')
historyFile.write('^XA^FO25,50^XGE:LOGO1.GRF ^FS\n')
tick_minute = datetime.datetime.now().minute

query = "select PythonVariable, Message from DisplayMessages"
try:
	cnx = connection.MySQLConnection(user='parking_user', password='XxUl4T8S0Eka6pzJ',
		                                 host='192.168.0.158',
		                                 database='parking')
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
		elif variable == 'PARKING P9':
			Welcome_msg = row[1]
		elif variable == 'LprNotDetected':
			LprNotDetected_msg = row[1]
except Exception as e:
	displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
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
		try:
			ftp = FTP(SERVER, USERNAME, PASS)
			timestamp = "%04d%02d%02d"%(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)
			try:
				ftp.cwd('/PARKING_08_ul/' + timestamp)
			except Exception as ex:
				ftp.mkd('/PARKING_08_ul/' + timestamp)
				ftp.cwd('/PARKING_08_ul/' + timestamp)

			lpr_file = open(DIR_PATH + lpr_filepath, 'rb')
			print("To ftp: " + timestamp + '/' + ftp_file_case)
			ftp.storbinary('STOR ' + ftp_file_case, lpr_file)
			ftp.quit()
			ftp.close()
		except Exception as ex:
			displayMsg("FTP Error", "ftp_error.jpg")
			print("FTP error")
			lpr_filepath = ''
			continue

		lpr_filepath = ''

		# Image url
		if compared_option == 1:
			# query = "update log set ImageURL = \'" + timestamp + '/' + ftp_file_case+ "\' where VehicleID = \'" + compared_value + "\'"
			query = "UPDATE card_logs SET enter_image_url = \'slike/PARKING_08_ul/" + timestamp + '/' + ftp_file_case+ "\' WHERE card_id_number =  \'" + compared_value + "\' order by id desc LIMIT 1 "
			# print("card")
		elif compared_option == 2:
			# query = "update ticket set LeaveTIme = null, ImageURL = \'" + timestamp + '/' + ftp_file_case+ "\' where BarCode = \'" + compared_value + "\'"
			query = "UPDATE tickets SET enter_image_url = \'slike/PARKING_08_ul/" + timestamp + '/' + ftp_file_case+ "\' WHERE barcode = \'" + compared_value + "\' order by id desc LIMIT 1"
		if compared_option != 0:
			try:
				cursor.execute(query)
				cnx.commit()		
			except Exception as exc:
				print("MySql is disconnected")			
				# displayMsg("MySql is disconnected")
				time.sleep(0.02)
				# displayMsg("")
				time.sleep(0.02)
				displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
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
			cnx = connection.MySQLConnection(user='parking_user', password='XxUl4T8S0Eka6pzJ',
			                                 host='192.168.0.158',
			                                 database='parking')
			cursor = cnx.cursor()
			# displayMsg("MySql is connected")
			time.sleep(0.02)
			# displayMsg("")
			time.sleep(0.02)
			displayMsg(MySqlStatusOn_msg, "mysql_is_disonnected.jpg")
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
			# displayMsg("")
			time.sleep(0.02)
			displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
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
			# displayMsg("")
			time.sleep(0.02)
			displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
			continue


	relay_status = relay_status & (~Barrier1)
	relay_status = relay_status & (~Barrier2)
	relay_status = relay_status & (~LPR_CONTROL)
	bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
	time.sleep(0.2)

	# check the loop0
	if GPIO.input(Loop0) == 1:
		time.sleep(0.02)
		# displayMsg("")
		time.sleep(0.02)
		displayMsg("Rampe nisu zatvorene", "initial_state.jpg")
		print("car is in loop1")		
		# GPIO.output(Barrier1, GPIO.LOW)		# Barrier1 is open
		# GPIO.output(Barrier2, GPIO.LOW)			# Barrier2 is close
		# GPIO.output(LPR_CONTROL, GPIO.LOW)		# Stop LPR
		# relay_status = relay_status & (~Barrier1)
		# relay_status = relay_status & (~Barrier2)
		# relay_status = relay_status & (~LPR_CONTROL)
		# bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
        
        
		relay_status = relay_status | Barrier2
		bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
		time.sleep(1)
		# GPIO.output(Barrier2,GPIO.HIGH)				
		relay_status = relay_status & (~Barrier2)
		bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
		time.sleep(1)
		relay_status = relay_status | Barrier1
		bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
		# time.sleep(3)
		# GPIO.output(Barrier2,GPIO.HIGH)				
		relay_status = relay_status & (~Barrier1)
		bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
		time.sleep(3)

	while GPIO.input(Loop0) == 1:
		continue

	#print("car is not in loop1")
	# Initial state
	print("\n ----- Initial State, waiting for the car ------")
	set_picture(1)
	set_initialtime(datetime.datetime.now().second)
	# displayMsg("PARKING P7")
	time.sleep(0.02)
	# displayMsg("")
	time.sleep(0.02)
	displayMsg(ParkingLot_msg, "initial_state.jpg")

	# GPIO.output(Barrier1, GPIO.HIGH)		# Barrier1 is open
	# GPIO.output(Barrier2, GPIO.LOW)			# Barrier2 is close
	# GPIO.output(LPR_CONTROL, GPIO.LOW)		# Stop LPR

	relay_status = relay_status & (~Barrier2)
	bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
	time.sleep(0.5)

	relay_status = relay_status | Barrier1
	relay_status = relay_status & (~LPR_CONTROL)
	bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
	
	# GPIO.output(B1STATELED, GPIO.HIGH)
	while GPIO.input(Loop1) == 0:
		continue

	time.sleep(0.02)
	# displayMsg("")
	time.sleep(0.02)
	displayMsg(Welcome_msg, "initial_state.jpg")

	# when the car is in Loop2
	# GPIO.output(L2STATELED, ~(GPIO.input(Loop2)))
	while GPIO.input(Loop2) == 1:
		displayMsg("screensaver", "screensaver.jpg")
		time.sleep(0.5)
		continue
	# GPIO.output(L2STATELED, ~(GPIO.input(Loop2)))
	time.sleep(0.02)
	# displayMsg("")
	time.sleep(0.02)
	print("The car is in loop2")	
	displayMsg("Skeniranje tablica...", "initial_state.jpg")

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
			if difference_camera > 5:
				camera_broken = 1
				break
		
	if camera_broken == 0:
		time.sleep(0.02)
		# displayMsg("")
		# time.sleep(0.02)
		print(lprcode + " is detected.")
		# displayMsg(lprcode)
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

	if GPIO.input(Loop1) == 0:				#vlada test
		print("barrier1 is open waiting to close. move your vehicle little forward or another vehicle is on the barrier1")
		time.sleep(0.02)
		# displayMsg("")
		time.sleep(0.02)
		displayMsg("Rampa nije zatvorena", "initial_state.jpg")
		while GPIO.input(Loop1) == 0:			# if another car is in loop 1
			continue
		# while GPIO.input(Loop0) == 1:
		# 	continue

	while GPIO.input(Loop0) == 1:
		time.sleep(0.02)
		displayMsg("Rampa je otvorena", "scanning_plate.jpg")
		print("barriers are open. loop0 = 1.")	
		#GPIO.output(barrier1, GPIO.LOW)
		relay_status = relay_status | (Barrier1)
		bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
		time.sleep(0.5)
		#GPIO.output(barrier1, GPIO.HIGH)
		relay_status = relay_status & (~Barrier1)
		bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
		time.sleep(5)

	# time.sleep(0.02)
	# displayMsg("")
	# time.sleep(0.02)
	print ("Ready. All barriers are closing.")
	# displayMsg("Ready. Checking the database.")
	# GPIO.output(B1STATELED, GPIO.LOW)

	# LPR state decide for car
	if lprcode != "No Plate":		
		set_picture(3)
		# query = "select status, name from vehicles where licencePlates = \'" + lprcode + "\'"
		query = "SELECT COALESCE(c.parked_at, 0) as status, c.card_id_number  FROM cards c  INNER JOIN card_vehicles cv ON c.id = cv.card_id WHERE cv.licence_plates LIKE \'" + lprcode + "\'"
		try:
			cursor.execute(query)
			rows = cursor.fetchall()
		except Exception as exc:
			print("MySql is disconnected")
			# displayMsg("MySql is disconnected")
			time.sleep(0.02)
			# displayMsg("")
			time.sleep(0.02)
			displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
			connctionState = 0
			# GPIO.output(DENYLED, GPIO.HIGH)
			relay_status = relay_status | DENYLED
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
			time.sleep(1)
			break # continue

		if cursor.rowcount == 0:
			# time.sleep(0.02)
			# displayMsg("")
			# time.sleep(0.02)
			print(lprcode + " is not existed in database.")		# go to the button for thermal printer
			# displayMsg(lprcode + " is not existed in database.")
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
			if status > 0:
				print("This car is already in. Please try another card or get the ticket from the service.")		# go to the button for thermal printer
				# time.sleep(0.02)
				# displayMsg("")
				# time.sleep(0.02)
				# displayMsg("Already in. Please try another card or get the ticket")
				
				# GPIO.output(DENYLED, GPIO.HIGH)
				relay_status = relay_status | DENYLED
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

				time.sleep(1)
			else:	
				# query = "select v.card, c.MaxParked, c.Inside, c.id from company c inner join vehicles v on v.idDept = c.id where v.licencePlates = \'" + lprcode + "\'"
				query = "SELECT DISTINCT c.card_number, cop.rented_spaces, cop.used_spaces, (cop.rented_spaces-cop.used_spaces) as ifFree FROM card_vehicles cv INNER JOIN cards c ON cv.card_id = c.id INNER JOIN card_parking cp ON cp.card_id = c.id INNER JOIN company_parking cop ON cp.company_id = cop.company_id AND cp.parking_id = cop.parking_id WHERE cp.parking_id = 4 AND cv.licence_plates = \'" + lprcode + "\'" 
				# query = "select c.card_number, cop.rented_spaces, cop.used_spaces, (cop.rented_spaces-cop.used_spaces) as ifFree FROM card_vehicles cv INNER JOIN cards c ON cv.card_id = c.id INNER JOIN card_parking cp ON cp.card_id = c.id INNER JOIN company_parking cop ON cp.company_id = cp.company_id AND cp.parking_id = cop.parking_id WHERE cv.licence_plates = \'" + lprcode + "\' AND cp.parking_id = 3"
				try:
					cursor.execute(query)
					row = cursor.fetchone()
				except Exception as exc:
					print("MySql is disconnected")
					# displayMsg("MySql is disconnected")
					time.sleep(0.02)
					# displayMsg("")
					time.sleep(0.02)
					displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
					connctionState = 0
					
					# GPIO.output(DENYLED, GPIO.HIGH)
					relay_status = relay_status | DENYLED
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

					time.sleep(0.3)
					break
				if cursor.rowcount != 1:
						print("this car is already in. please try another card or get the ticket from card!")
						displayMsg("Kartica nije aktivna za ovaj parking! Ocitajte drugu karticu.", "user_cant_enter_to_the_parkinglot_over_lpr.jpg")
				else:
					MaxParked = row[1]
					Inside = row[2]
					companyId = row[3]
					print("MaxParked: " + str(MaxParked) + "  Inside: " + str(Inside))
		
					if Inside < MaxParked:
						time.sleep(0.02)
						#displayMsg("")
						time.sleep(0.02)
						print("You can park your car")
						displayMsg("Mozete proci", "user_can_enter_to_the_parkinglot_over_lpr.jpg")
						# displayMsg(lprcode + ": Mozete proci")
						# query = "update vehicles set status = 1 where licencePlates = '" + lprcode + "'"
						query = "UPDATE cards c INNER JOIN card_vehicles cv ON c.id =cv.card_id SET c.parked_at = 4 WHERE cv.licence_plates LIKE '" + lprcode + "'"
						print("updating the status")
						try:
							cursor.execute(query)
							cnx.commit()		
						except Exception as exc:
							print("MySql is disconnected")			
							# displayMsg("MySql is disconnected")
							time.sleep(0.02)
							# displayMsg("")
							time.sleep(0.02)
							displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
							connctionState = 0
							# GPIO.output(DENYLED, GPIO.HIGH)
							relay_status = relay_status | DENYLED
							bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
							time.sleep(0.3)
							continue

						# query = "update company set Inside = " + str(Inside + 1) + " where id = '" + str(companyId) + "'"
						print("upddating the Inside")
						try:
							cursor.execute(query)
							cnx.commit()		
						except Exception as exc:
							print("MySql is disconnected")		
							# displayMsg("MySql is disconnected")
							time.sleep(0.02)
							# displayMsg("")
							time.sleep(0.02)
							displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
							connctionState = 0
							# GPIO.output(DENYLED, GPIO.HIGH)
							relay_status = relay_status | DENYLED
							bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
							time.sleep(0.3)
							continue

									# saving log
						today = datetime.datetime.now()
						CheckTime = "%04d-%02d-%02d %02d:%02d:%02d"%(today.year, today.month, today.day, today.hour, today.minute, today.second)
						# query = "INSERT INTO log (VehicleID, CheckTime, CheckType, ParkingLot, VerificationType) VALUES (\'" + vehicle_name + "\', NOW(), 0, \'P7\', 1);"
						query = "INSERT INTO card_logs (card_id_number, licence_plates, enter_time, check_type,parking_id) VALUES (\'" + vehicle_name + "\',\'" + lprcode +"\', NOW(), 1, 4);"
						print("inserting the log")
						try:
							cursor.execute(query)
							cnx.commit()		
						except Exception as exc:
							print("MySql is disconnected")
							# displayMsg("MySql is disconnected")
							time.sleep(0.02)
							# displayMsg("")
							time.sleep(0.02)
							displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
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
						# displayMsg("")
						time.sleep(0.02)
						print("Waiting for passing the barrier2...")
						displayMsg("Tablica ocitana parkirajte vozilo", "user_can_enter_to_the_parkinglot_over_lpr.jpg")
						time.sleep(0.2) # time.sleep(3)
						# while GPIO.input(Loop2) == 0:
						#	print "."
						# 	time.sleep(1)
						while GPIO.input(Loop3) == 1:
							print "."
							time.sleep(0.2)
						while GPIO.input(Loop3) == 0:
							print "."
							time.sleep(0.2)

						while GPIO.input(Loop0) == 1:
							time.sleep(0.02)
							displayMsg("Rampa je otvorena", 'user_can_enter_to_the_parkinglot_over_lpr.jpg')
							print("barriers are open. loop0 = 1.")	
							#GPIO.output(barrier1, GPIO.LOW)
							relay_status = relay_status | (Barrier2)
							bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
							time.sleep(0.5)
							#GPIO.output(barrier1, GPIO.HIGH)
							relay_status = relay_status & (~Barrier2)
							bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
							time.sleep(5)

						# GPIO.output(L2STATELED, ~(GPIO.input(Loop2)))
						time.sleep(0.02)
						# displayMsg("")
						time.sleep(0.02)
						print("Successfully Entered!")
						# displayMsg("Successfully Entered!")
						ftp_file_case = "%04d%02d%02d_%s"%(today.hour, today.minute, today.second, ftp_file_case)
						compared_option = 1
						compared_value = vehicle_name
						continue
					else:
						time.sleep(0.02)
						# displayMsg("")
						time.sleep(0.02)
						print("The parkinglot for this company is alreay full.")
						print("Please try card or get the ticket from the service.")
						displayMsg("Parking je popunjen za vasu kompaniju,uzmite tiket", "parking_is_full_for_users_company.jpg")
						
						# GPIO.output(DENYLED, GPIO.HIGH)
						relay_status = relay_status | DENYLED
						bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

						time.sleep(0.3)			

	time.sleep(3.02)
	# displayMsg("")
	time.sleep(0.02)
	
	print("Please attach card to the reader or press button")
	displayMsg("Prinesite karticu ili uzmite TIKET", "press_button_or_get_ticket.jpg")


	# now car is in loop2 and checkng the rfid card
	button_pressed = 0
	leave_loop2 = 1
	vehicle_name = ''
	while 1:
		current_time = datetime.datetime.now()
		if current_time.second % 2 == 0:			
			# turn on the button light
			relay_status = relay_status | BUTTON_LIGHT
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
		else:
			# turn off the button light
			relay_status = relay_status & (~BUTTON_LIGHT)
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)


		x0 = ""
		x0 = reader.readline()
		# waiting for no card data or no button
		# while len(x0) == 0 and GPIO.input(BUTTON) == 1:
	#		x0 = reader.readline()

		# When punch the card
		print('Checking card')
		if len(x0) != 0:
			set_picture(3)
			print(x0)
			strX0 = x0 # "%08x" % int(x0, 10)
			#strX0 = strX0[6:8] + strX0[4:6] + strX0[2:4] + strX0[0:2]
			#strX0 = "%010d" % int(strX0, 16)
			print("Card Number: " + strX0)
			# displayMsg("Card Number: " + strX0)

			# query = "UPDATE tickets SET status = 0 WHERE 'barcode' = 'dummy'"
			query = "UPDATE `ql` SET `time` = NOW() WHERE `id` = 1"
			cursor.execute(query)
			cnx.commit()
			# check in database
			# query = "select status, name from vehicles where card = " + strX0
			query = "SELECT COALESCE(parked_at,0) as status, card_id_number FROM cards WHERE card_number = " + strX0
			try:
				cursor.execute(query)
				rows = cursor.fetchall()
			except Exception as exc:
				rows = []
				# displayMsg("MySql is disconnected")
				# displayMsg("MySql is disconnected")
				displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
				connctionState = 0
				
				# GPIO.output(DENYLED, GPIO.HIGH)
				relay_status = relay_status | DENYLED
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

				time.sleep(1)
				break

			if cursor.rowcount != 1:
				print("The card " + strX0 + " is not existed. Please try another card or get the ticket from the service.")		# go to the button for thermal printer
				displayMsg("Kartica nevazeca uzmite TIKET", "punched_card_not_exist.jpg")
				
				# GPIO.output(DENYLED, GPIO.HIGH)
				relay_status = relay_status | DENYLED
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

				time.sleep(0.3)
			else:
				row = rows[0]
				status = row[0]
				vehicle_name = row[1]
				print("Status value is " + str(status))
				if status > 0:
					print("This car is already in. Please try another card or get the ticket from the service.")		# go to the button for thermal printer
					displayMsg("Vozilo je vec unutra, uzmite TIKET", "punched_card_not_have_right_to_enter.jpg")
					
					# GPIO.output(DENYLED, GPIO.HIGH)
					relay_status = relay_status | DENYLED
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

					time.sleep(1)
				else:					
					# query = "select v.card, c.MaxParked, c.Inside, c.id from company c inner join vehicles v on v.idDept = c.id where v.card = " + strX0
					query = "SELECT DISTINCT c.card_number, cop.rented_spaces, cop.used_spaces, (cop.rented_spaces-cop.used_spaces) as ifFree FROM card_vehicles cv INNER JOIN cards c ON cv.card_id = c.id INNER JOIN card_parking cp ON cp.card_id = c.id INNER JOIN company_parking cop ON cp.company_id = cop.company_id AND cp.parking_id = cop.parking_id WHERE cp.parking_id = 4 AND c.card_number = " + strX0 
					try:
						cursor.execute(query)
						row = cursor.fetchone()
					except Exception as exc:
						# displayMsg("MySql is disconnected")
						displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
						print("MySql is disconnected")
						connctionState = 0
						
						# GPIO.output(DENYLED, GPIO.HIGH)
						relay_status = relay_status | DENYLED
						bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

						time.sleep(0.3)
						break
					if cursor.rowcount != 1:
						print("this car is already in. please try another card or get the ticket from card!")
						displayMsg("Kartica nije aktivna za ovaj parking! Ocitajte drugu karticu.", "user_cant_enter_to_the_parkinglot_over_rfid.jpg")
					else:
						MaxParked = row[1]
						Inside = row[2]
						companyId = row[3]
						print("MaxParked: " + str(MaxParked) + "  Inside: " + str(Inside))
			
						if Inside < MaxParked:
							print("You can park your car")
							displayMsg("Parkirajte vozilo", "user_can_enter_to_the_parkinglot_over_rfid.jpg")
							set_picture(2)
							break
						else:
							print("The parkinglot for this company is alreay full.")
							displayMsg("Parking je popunjen za vasu kompaniju, uzmite TIKET", "parking_is_full_for_users_company.jpg")
							print("Please try another card or get the ticket from the service.")
							
							# GPIO.output(DENYLED, GPIO.HIGH)
							relay_status = relay_status | DENYLED
							bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

							time.sleep(0.3)
		print('Checking button')
		if GPIO.input(BUTTON) == 0:
			# checking it is not noise
			time.sleep(0.02)
			print("button is pressed in while loop")
			button_pressed = 1
			set_picture(3)
			if GPIO.input(BUTTON) == 0:
				break

		# if the car leaves loop2
		if GPIO.input(Loop2) == 1:
			leave_loop2 = 0
			break


	# turn off the button light
	relay_status = relay_status & (~BUTTON_LIGHT)
	bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

	# if the car leaves the loop2
	if leave_loop2 == 0:
		print('Leave Loop2')
		continue
	#if the button is pressed.
	if button_pressed == 1:				# if GPIO.input(BUTTON) == 0:
		query = "SELECT NOW() as reply"
		try:
			cursor.execute(query)
			rows = cursor.fetchall()
		except Exception as exc:			
			# displayMsg("MySql is disconnected")
			displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
			print("MySql is disconnected")
			connctionState = 0
			
			# GPIO.output(DENYLED, GPIO.HIGH)
			relay_status = relay_status | DENYLED
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

			time.sleep(0.3)
			continue
		row = rows[0]
		today1 = str(row[0])
		year1 = today1[0:4]
		month1 = today1[5:7]
		day1 = today1[8:10]
		hour1 = today1[11:13]
		minute1 = today1[14:16]
		second1 = today1[17:19]
		
		# the button is pressed
		print("button is pressed, and the ticket is printing....")
		displayMsg("Stampa...", "user_press_button_for_ticket.jpg")
		fob = open('raw.zpl', 'w')
		fob.write('^XA^FO25,50^XGE:LOGO1.GRF ^FS\n')
		fob.write('^CF0,30,30^FO25,230\n')
		fob.write('^FB400,5,,\n')
		fob.write('^FD --------------\&\n')
		fob.write('PARKING P8\&\n')
		str1 = 'DATE: %s. %s. %s \&\n'%(day1, month1, year1)
		fob.write(str1)
		str1 = ' TIME: %s:%s:%s\&\n'%(hour1, minute1, second1)
		fob.write(str1)
		# Print Barcode
		str1 = 'Car Plate: %s^FS\n'%(lprcode)
		fob.write(str1)
		fob.write('\n')

		today = datetime.datetime.now()
		fob.write('^FO50,390^BY2\n')
		fob.write('^BCN,110,Y,N,N\n')
		str1 = "^FD%s%s%s%s%s%s%1d^FS\n"%(year1[2:4], month1, day1, hour1, minute1, second1, 8)
		barcode = "%s%s%s%s%s%s%1d"%(year1[2:4], month1, day1, hour1, minute1, second1, 8)
		fob.write(str1)
		fob.write('\n')

		fob.write('^CF0,30,25^FO25,550\n')
		fob.write('^FB520,4,,\n')
		fob.write('^FD Emergency Phone:+381 60 8301375^FS\n')
		fob.write('^XZ\n')
		fob.close()

		os.system("/usr/bin/lpr -P Zebra_Technologies_ZTC_KR403 -o raw /home/pi/parkinglot/all_part/raw.zpl")
		
		print("Updating database")
		PickupTime = "%04d-%02d-%02d %02d:%02d:%02d"%(today.year, today.month, today.day, today.hour, today.minute, today.second)
		# query = "INSERT INTO ticket(ParkingLot, CarPlate, PickupTime, BarCode, ImageURL, StatusTicket_pay, StatusCar_in, ImageURLexit) VALUES (\'P7\', \'" + lprcode +"\', \'" + PickupTime + "\', \'" + barcode + "\', NULL, 1, 1, null)"
		query = "INSERT INTO tickets (parking_id, barcode, licence_plates, enter_time, created_at, enter_image_url, exit_image_url, status) VALUES ('4', \'" + barcode + "\', \'" + lprcode +"\', NOW(),NOW(), NULL, NULL, 1)"
		try:
			cursor.execute(query)
			cnx.commit()		
		except Exception as exc:			
			print str(exc)
			# displayMsg("MySql is disconnected")
			displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
			print("MySql is disconnected")
			connctionState = 0
			
			# GPIO.output(DENYLED, GPIO.HIGH)
			relay_status = relay_status | DENYLED
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

			time.sleep(0.3)
			continue

		print("******* Sucessfully printed *******")
		while GPIO.input(BUTTON) == 0:
			# GPIO.output(Barrier2, GPIO.LOW)
			relay_status = relay_status & (~Barrier2)
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
		# GPIO.output(Barrier2,GPIO.HIGH)		
		relay_status = relay_status | Barrier2
		bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

		# GPIO.output(B2STATELED, GPIO.HIGH)
		print("Waiting for passing the barrier2...")
		displayMsg("Slobodan prolaz hvala. Napustite zonu rampe!", "user_can_enter_to_the_parkinglot_over_rfid.jpg")
		time.sleep(3) # time.sleep(3)
		# while GPIO.input(Loop2) == 0:
		#	print "."
		#	time.sleep(1)
		while GPIO.input(Loop3) == 1:
			print "."
			time.sleep(0.2)
		while GPIO.input(Loop3) == 0:
			print "."
			time.sleep(0.2)


		while GPIO.input(Loop0) == 1:
			time.sleep(0.02)
			displayMsg("Rampa je otvorena", "user_can_enter_to_the_parkinglot_over_rfid.jpg")
			print("barriers are open. loop0 = 1.")	
			#GPIO.output(barrier1, GPIO.LOW)
			relay_status = relay_status | (Barrier2)
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
			time.sleep(0.5)
			#GPIO.output(barrier1, GPIO.HIGH)
			relay_status = relay_status & (~Barrier2)
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
			time.sleep(5)
						
		# GPIO.output(L2STATELED, ~(GPIO.input(Loop2)))
		print("Successfully Entered!")
		#displayMsg("AIRPORT BELGRADE")

		ftp_file_case = "%s_%s"%(barcode, ftp_file_case)
		compared_option = 2
		compared_value = barcode
		# GPIO.output(B2STATELED, GPIO.LOW)

	# if the card is right
	else:
		# query = "update vehicles set status = 1 where card = '" + strX0 + "'"
		query = "UPDATE `cards` SET `parked_at` = 4 WHERE `card_number` = '" + strX0 + "'"
		try:
			cursor.execute(query)
			cnx.commit()		
		except Exception as exc:			
			# displayMsg("MySql is disconnected")
			displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
			print("MySql is disconnected")
			connctionState = 0
			
			# GPIO.output(DENYLED, GPIO.HIGH)
			relay_status = relay_status | DENYLED
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

			time.sleep(0.3)
			continue

		# query = "update company set Inside = " + str(Inside + 1) + " where id = '" + str(companyId) + "'"
		
		try:
			cursor.execute(query)
			cnx.commit()		
		except Exception as exc:			
			# displayMsg("MySql is disconnected")
			displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
			print("MySql is disconnected")
			connctionState = 0
			
			# GPIO.output(DENYLED, GPIO.HIGH)
			relay_status = relay_status | DENYLED
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

			time.sleep(0.3)
			continue

		# saving log
		today = datetime.datetime.now()
		CheckTime = "%04d-%02d-%02d %02d:%02d:%02d"%(today.year, today.month, today.day, today.hour, today.minute, today.second)
		# query = "INSERT INTO log (CheckTime, VehicleID, CheckType, ParkingLot, VerificationType) VALUES (\'" + CheckTime + "\', \'" + vehicle_name + "\', 0, \'P7\', 0)"
		query = "INSERT INTO card_logs (card_id_number, licence_plates, enter_time, check_type,parking_id) VALUES (\'" + vehicle_name + "\',\'" + lprcode +"\', NOW(), 1, 4);"
		print(query)
		try:
			cursor.execute(query)
			cnx.commit()		
		except Exception as exc:			
			# displayMsg("MySql is disconnected")
			displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.jpg")
			print("MySql is disconnected")
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
		print("Waiting for passing the barrier2...")
		displayMsg("Slobodan prolaz hvala. Napustite zonu rampe", "user_can_enter_to_the_parkinglot_over_rfid.jpg")
		time.sleep(0.2) # time.sleep(3)
		# while GPIO.input(Loop2) == 0:
		#	print "."
		#	time.sleep(1)
		while GPIO.input(Loop3) == 1:
			print "."
			time.sleep(0.2)
		while GPIO.input(Loop3) == 0:
			print "."
			time.sleep(0.2)


		while GPIO.input(Loop0) == 1:
			time.sleep(0.02)
			displayMsg("Rampa je otvorena", "user_can_enter_to_the_parkinglot_over_rfid.jpg")
			print("barriers are open. loop0 = 1.")	
			#GPIO.output(barrier1, GPIO.LOW)
			relay_status = relay_status | (Barrier2)
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
			time.sleep(0.5)
			#GPIO.output(barrier1, GPIO.HIGH)
			relay_status = relay_status & (~Barrier2)
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
			time.sleep(5)
			

		# GPIO.output(L2STATELED, ~(GPIO.input(Loop2)))
		print("Successfully Entered!")
		# displayMsg("Successfully Entered!")

		ftp_file_case = "%04d%02d%02d_%s"%(today.hour, today.minute, today.second, ftp_file_case)
		compared_option = 1
		compared_value = vehicle_name
		# GPIO.output(B2STATELED, GPIO.LOW)
		continue
