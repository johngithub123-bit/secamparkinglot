from mysql.connector import (connection)
import time
import serial
import RPi.GPIO as GPIO
import os
import datetime
from ftplib import FTP_TLS
import sys
import smbus

CARD_DEV = '/dev/ttyUSB1'
DISPLAY_DEV = '/dev/ttyUSB0'
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
ParkingLot_msg = "PARKING P8"
Welcome_msg = "PARKING P8"
LprNotDetected_msg = "Camera not detected"

# define ftp 
SERVER = '192.168.0.200'
PORT = '21'
USERNAME = 'vlada'
PASS = 'raspberry2018'

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

connctionState = 0;

historyFile = open('histroyInfo.txt', 'a')
historyFile.write('^XA^FO25,50^XGE:LOGO1.GRF ^FS\n')
tick_minute = datetime.datetime.now().minute

query = "select PythonVariable, Message from DisplayMessages"
try:
	cnx = connection.MySQLConnection(user='parking_user', password='XxUl4T8S0Eka6pzJ',
		                                 host='192.168.0.200',
		                                 database='parking')
	cnx.autocommit(false)
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
		elif variable == 'PARKING P7':
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
			ftp = FTP_TLS('192.168.0.200')
			ftp.sendcmd('USER vlada')
			ftp.sendcmd('PASS raspberry2018')
			timestamp = "%04d%02d%02d"%(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)
			try:
				ftp.cwd('/PARKING_08_iz/' + timestamp)
			except Exception as ex:
				ftp.mkd('/PARKING_08_iz/' + timestamp)
				ftp.cwd('/PARKING_08_iz/' + timestamp)

			lpr_file = open(DIR_PATH + lpr_filepath, 'rb')
			print("To ftp: " + timestamp + '/' + ftp_file_case)
			ftp.storbinary('STOR ' + ftp_file_case, lpr_file)
			ftp.quit()
			ftp.close()
		except Exception as exc:
			displayMsg("FTP Error", "ftp_error.jpg")
			print("FTP error")
			lpr_filepath = ''
			continue

		lpr_filepath = ''

		# Image url
		if compared_option == 1:
			# stari upit koji radi sa starom bazom
			# query = "update log set ImageURL = \'" + timestamp + '/' + ftp_file_case+ "\' where VehicleID = \'" + compared_value + "\'"
			query = "UPDATE card_logs SET exit_image_url = \'slike/PARKING_08_iz/" + timestamp + '/' + ftp_file_case+ "\' WHERE card_id_number =  \'" + compared_value + "\' order by id desc LIMIT 1"
		elif compared_option == 2:
			# stari upit koji radi sa starom bazom
			# query = "update ticket set ImageURLexit = \'" + timestamp + '/' + ftp_file_case+ "\' where BarCode = " + compared_value
			query = "UPDATE tickets SET exit_image_url = \'slike/PARKING_08_iz/" + timestamp + '/' + ftp_file_case+ "\' WHERE barcode = \'" + compared_value + "\' order by id desc LIMIT 1"
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
		                                 host='192.168.0.200',
		                                 database='parking')
			# cnx.autocommit(false)
			cursor = cnx.cursor()
			# displayMsg("MySql is connected")
			time.sleep(0.02)
			#displayMsg("")
			time.sleep(0.02)
			displayMsg(MySqlStatusOn_msg, "mysql_is_disonnected.gif")
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
			displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
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
			displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
			continue


	# check the loop0
	if GPIO.input(Loop0) == 1:
		time.sleep(0.02)
		# displayMsg("")
		time.sleep(0.02)
		displayMsg("Ulazna rampa nije zatvorena!", "initial_state.jpg")
		print("car is loop0")		
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
		# time.sleep(20)
		# GPIO.output(Barrier2,GPIO.HIGH)				
		relay_status = relay_status & (~Barrier1)
		bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
		time.sleep(3)

	while GPIO.input(Loop0) == 1:
		continue

	print("Rampe nisu zatvorene!")

	# Initial state
	print("\n ----- Initial State, waiting for the car ------")
	set_initialtime(datetime.datetime.now().second)
	# displayMsg("PARKING P7")
	time.sleep(0.02)
	# displayMsg("")
	time.sleep(0.02)
	displayMsg(ParkingLot_msg, "initial_state.jpg")
	# GPIO.output(Barrier1, GPIO.HIGH)		# Barrier1 is open
	# GPIO.output(Barrier2, GPIO.LOW)			# Barrier2 is close
	# GPIO.output(LPR_CONTROL, GPIO.LOW)		# Stop LPR

	relay_status = relay_status | Barrier1
	bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
	time.sleep(0.5)
	relay_status = relay_status & (~Barrier2)
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
		continue
	# GPIO.output(L2STATELED, ~(GPIO.input(Loop2)))
	time.sleep(0.02)
	# displayMsg("")
	time.sleep(0.02)
	print("The car is in loop2")	
	displayMsg("Skeniranje tablica...", "scanning_plate.gif")

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
		if difference_camera > 3:
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
			if difference_camera > 3:
				camera_broken = 1
				break
		
	if camera_broken == 0:
		time.sleep(0.02)
		# displayMsg("")
		time.sleep(0.02)
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
		displayMsg("Ulazna rampa nije zatvorena", "initial_state.jpg")
		while GPIO.input(Loop1) == 0:			# if another car is in loop 1
			continue
		# while GPIO.input(Loop0) == 0:
		# 	continue

	while GPIO.input(Loop0) == 1:
		time.sleep(0.02)
		displayMsg("Rampa je otvorena", "scanning_plate.gif")
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
		# stari upit koji radi sa starom bazom
		# query = "select status, name from vehicles where licencePlates = \'" + lprcode + "\'"
		query = "SELECT COALESCE(c.parked_at, 0) as status, c.card_id_number FROM cards c INNER JOIN card_vehicles cv ON c.id = cv.card_id WHERE cv.licence_plates LIKE \'" + lprcode + "\'"
		try:
			cursor.execute(query)
			rows = cursor.fetchall()
		except Exception as exc:
			print("MySql is disconnected")
			# displayMsg("MySql is disconnected")
			time.sleep(0.02)
			# displayMsg("")
			time.sleep(0.02)
			displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
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
				# stari upit koji radi sa starom skriptom	
				# query = "select v.card, c.MaxParked, c.Inside, c.id from company c inner join vehicles v on v.idDept = c.id where v.licencePlates = \'" + lprcode + "\'"
				query = "SELECT DISTINCT c.card_number, cop.rented_spaces, cop.used_spaces, (cop.rented_spaces-cop.used_spaces) as ifFree FROM card_vehicles cv INNER JOIN cards c ON cv.card_id = c.id INNER JOIN card_parking cp ON cp.card_id = c.id INNER JOIN company_parking cop ON cp.company_id = cop.company_id AND cp.parking_id = cop.parking_id WHERE cp.parking_id = 4 AND cv.licence_plates = \'" + lprcode + "\'" 
				try:
					cursor.execute(query)
					row = cursor.fetchone()
				except Exception as exc:
					print("MySql is disconnected")
					# displayMsg("MySql is disconnected")
					time.sleep(0.02)
					# displayMsg("")
					time.sleep(0.02)
					displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
					connctionState = 0
					# GPIO.output(DENYLED, GPIO.HIGH)
					relay_status = relay_status | DENYLED
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

					time.sleep(0.3)
					continue
				if cursor.rowcount != 1:
						print("this car is already in. please try another card or get the ticket from card!")
						displayMsg("Kartica nije aktivna za ovaj parking! Ocitajte drugu karticu.", "user_canot_access_to_the_parkinglot_with_lpr.gif")
						continue
				MaxParked = row[1]
				Inside = row[2]
				companyId = row[3]
				print("MaxParked: " + str(MaxParked) + "  Inside: " + str(Inside))
	
				time.sleep(0.02)
				# displayMsg("")
				time.sleep(0.02)
				print("You can exit your car")
				displayMsg("Mozete proci", "user_canot_access_to_the_parkinglot_with_lpr.jpg")
						
				# stari upit koji radi sa starom bazom
				# query = "update vehicles set status = 0 where licencePlates = '" + lprcode + "'"
				query = "UPDATE cards c INNER JOIN card_vehicles cv ON c.id =cv.card_id SET c.parked_at = NULL WHERE cv.licence_plates LIKE '" + lprcode + "'"
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
					displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
					connctionState = 0
					# GPIO.output(DENYLED, GPIO.HIGH)
					relay_status = relay_status | DENYLED
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

					time.sleep(0.3)
					continue

				# stari upit koji radi sa starom bazom
				# query = "update company set Inside = " + str(Inside - 1) + " where id = '" + str(companyId) + "'"
				print("updating the Inside")
				try:
					cursor.execute(query)
					cnx.commit()		
				except Exception as exc:
					print("MySql is disconnected")		
					# displayMsg("MySql is disconnected")
					time.sleep(0.02)
					# displayMsg("")
					time.sleep(0.02)
					displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
					connctionState = 0
					# GPIO.output(DENYLED, GPIO.HIGH)
					relay_status = relay_status | DENYLED
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

					time.sleep(0.3)
					continue

								# saving log
				today = datetime.datetime.now()
				CheckTime = "%04d-%02d-%02d %02d:%02d:%02d"%(today.year, today.month, today.day, today.hour, today.minute, today.second)
				# stari upit koji radi sa starom skriptom
				# query = "INSERT INTO log (CheckTime, VehicleID, CheckType, ParkingLot, VerificationType) VALUES (\'" + CheckTime + "\', \'" + vehicle_name + "\', 1, \'P7\', 1);"
				query = "update card_logs set exit_time = NOW(), licence_plates = \'" + lprcode +"\' where card_id_number = \'" + vehicle_name + "\'"
				print("inserting the log")
				try:
					cursor.execute(query)
					cnx.commit()		
				except Exception as exc:			
					# displayMsg("MySql is disconnected")
					print("MySql is disconnected")
					# displayMsg("MySql is disconnected")
					time.sleep(0.02)
					# displayMsg("")
					time.sleep(0.02)
					displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
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
				displayMsg("Tablica ocitana, prodjite", "user_can_enter_to_the_parkinglot_over_lpr.gif")
				time.sleep(1)# time.sleep(3)
				# while GPIO.input(Loop2) == 0:
				# 	print "."
				# 	time.sleep(1)
				while GPIO.input(Loop3) == 1:
					print "."
					time.sleep(0.2)
				while GPIO.input(Loop3) == 0:
					print "."
					time.sleep(0.2)


				while GPIO.input(Loop0) == 1:
					time.sleep(0.02)
					displayMsg("Rampa je otvorena!", 'user_can_enter_to_the_parkinglot_over_lpr.gif')
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
				print("Successfully Exited!")
				# displayMsg("Prijatan dan!")
				ftp_file_case = "%04d%02d%02d_%s"%(today.year, today.month, today.day, ftp_file_case)
				compared_option = 1
				compared_value = vehicle_name
				continue		

	time.sleep(3.02)
	# displayMsg("")
	time.sleep(0.02)
	
	print("Please attach card to the reader or check barcode")
	displayMsg("Prinesite karticu ili ocitajte TIKET", "press_button_or_get_ticket.gif")
	# now car is in loop2 and checkng the rfid card
	while 1:
		x0 = ""
		barcode = ''
		x0 = reader.readline()
		leave_loop2 = 1
		barcode = barcode_reader.readline()
		# waiting for no card data or no button
		if GPIO.input(Loop2) == 1:
			break
		while len(x0) == 0 and len(barcode) == 0:
			x0 = reader.readline()
			# if the car leaves loop2
			if GPIO.input(Loop2) == 1:
				leave_loop2 = 0
				break
			# BARCODE OFF Ugasi liniju ispod da neradi USB2
			# barcode = barcode_reader.readline()


		# if the car leaves the loop2
		if leave_loop2 == 0:
			print('Leave Loop2')
			break
		# When punch the card
		if len(x0) != 0:
			strX0 = x0
			# strX0 = "%08x" % int(x0, 10)
			# strX0 = strX0[6:8] + strX0[4:6] + strX0[2:4] + strX0[0:2]
			# strX0 = "%010d" % int(strX0, 16)
			print("Card Number: " + strX0)
			# displayMsg(strX0) # ovde ispisuje broj kartice na displeju

			# check in database
			
			try:
				# query = "UPDATE tickets SET status = 0 WHERE 'barcode' = 'dummy'"
				query = "UPDATE `ql` SET `time` = NOW() WHERE `id` = 1"
				cursor.execute(query)
				cnx.commit()
				# stari upit koji radi sa starom skriptom
				# query = "select status, name from vehicles where card = " + strX0
				query = "SELECT COALESCE(parked_at,0) as status, card_id_number FROM cards WHERE card_number = " + strX0
				cursor.execute(query)
				rows = cursor.fetchall()
			except Exception as exc:
				rows = []
				# displayMsg("MySql is disconnected")
				displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
				connctionState = 0
				# GPIO.output(DENYLED, GPIO.HIGH)
				relay_status = relay_status | DENYLED
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				time.sleep(1)
				break

			if cursor.rowcount != 1:
				print("The card " + strX0 + " is not existed. Please try another card or get the ticket from the service.")		# go to the button for thermal printer
				displayMsg("Kartica ne postoji ocitajte tiket", "punched_card_not_exist.gif")
				# GPIO.output(DENYLED, GPIO.HIGH)
				# relay_status = relay_status | DENYLED
				# bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				# time.sleep(0.3)
				# GPIO.output(Barrier1, GPIO.HIGH)
				# relay_status = relay_status | Barrier1
				# bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				continue
			else:
				row = rows[0]
				status = row[0]
				vehicle_name = row[1]
				print("Status value is " + str(status))
				if status == 0:
					print("This car is already out. Please try another card or get the ticket from the service.")		# go to the button for thermal printer
					displayMsg("Vozilo je van parkinga. Pokusajte sa drugom karticom ili ocitajte TIKET", "punched_card_not_exist.gif")
					# GPIO.output(DENYLED, GPIO.HIGH)
					# relay_status = relay_status | DENYLED
					# bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
					# time.sleep(1)
					# GPIO.output(Barrier1, GPIO.HIGH)
					# relay_status = relay_status | Barrier1
					# bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
					continue
				else:
					# stari upit koji radi sa starom skriptom					
					# query = "select v.card, c.MaxParked, c.Inside, c.id from company c inner join vehicles v on v.idDept = c.id where v.card = " + strX0
					query = "SELECT DISTINCT c.card_number, cop.rented_spaces, cop.used_spaces, (cop.rented_spaces-cop.used_spaces) as ifFree FROM card_vehicles cv INNER JOIN cards c ON cv.card_id = c.id INNER JOIN card_parking cp ON cp.card_id = c.id INNER JOIN company_parking cop ON cp.company_id = cop.company_id AND cp.parking_id = cop.parking_id WHERE cp.parking_id = 4 AND c.card_number = " + strX0 
					try:
						cursor.execute(query)
						row = cursor.fetchone()
					except Exception as exc:
						# displayMsg("MySql is disconnected")
						displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
						print("MySql is disconnected")
						connctionState = 0
						# GPIO.output(DENYLED, GPIO.HIGH)
						relay_status = relay_status | DENYLED
						bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
						time.sleep(0.3)
						break

					if cursor.rowcount != 1:
						print("this car is already in. please try another card or get the ticket from card!")
						displayMsg("Kartica nije aktivna za ovaj parking! Ocitajte drugu karticu.", "user_canot_access_to_the_parkinglot_with_card.gif")
						continue
					MaxParked = row[1]
					Inside = row[2]
					companyId = row[3]
					print("MaxParked: " + str(MaxParked) + "  Inside: " + str(Inside))
					# stari upit koji radi sa starom skriptom
					# query = "update vehicles set status = 0 where card = '" + strX0 + "'"
					query = "UPDATE cards SET parked_at = NULL WHERE card_number = " + strX0 + ""
					try:
						cursor.execute(query)
						cnx.commit()		
					except Exception as exc:			
						# displayMsg("MySql is disconnected")
						displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
						print("MySql is disconnected")
						connctionState = 0
						# GPIO.output(DENYLED, GPIO.HIGH)
						relay_status = relay_status | DENYLED
						bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
						time.sleep(0.3)
						break

					# query = "update company set Inside = " + str(Inside - 1) + " where id = '" + str(companyId) + "'"
					
					try:
						cursor.execute(query)
						cnx.commit()		
					except Exception as exc:			
						# displayMsg("MySql is disconnected")
						displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
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
					# stari upit koji radi sa starom skriptom
					# query = "INSERT INTO log (CheckTime, VehicleID, CheckType, ParkingLot, VerificationType) VALUES (\'" + CheckTime + "\', \'" + vehicle_name + "\', 1, \'P7\', 0)"
					query = "update card_logs set exit_time = NOW(), licence_plates = \'" + lprcode +"\' where card_id_number = \'" + vehicle_name + "\'"
					print(query)
					try:
						cursor.execute(query)
						cnx.commit()		
					except Exception as exc:			
						# displayMsg("MySql is disconnected")
						displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
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
					displayMsg("Slobodan prolaz hvala. Napustite zonu rampe...", "user_can_access_to_the_parkinglot_with_card.gif")
					time.sleep(0.2) # time.sleep(3)
					#while GPIO.input(Loop2) == 0:
					#	print "."
					#	time.sleep(0.2)
					while GPIO.input(Loop3) == 1:
						print "."
						time.sleep(0.2)
					while GPIO.input(Loop3) == 0:
						print "."
						time.sleep(0.2)


					while GPIO.input(Loop0) == 1:
						time.sleep(0.02)
						displayMsg("Izlazna rampa je otvorena", "user_can_access_to_the_parkinglot_with_card.gif")
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
					print("Successfully Exited!")
					# displayMsg("Successfully Exited!")

					ftp_file_case = "%04d%02d%02d_%s"%(today.year, today.month, today.day, ftp_file_case)
					compared_option = 1
					compared_value = vehicle_name
					# GPIO.output(B2STATELED, GPIO.LOW)
					break		
					
		if len(barcode) != 0:
			barcode = barcode.rstrip()
			print(barcode)

			
			
			
			try:
				query = "UPDATE `ql` SET `time` = NOW() WHERE `id` = 1"
				cursor.execute(query)
				cnx.commit()
				# query = "SELECT IF(`paid_until` IS NOT NULL AND `paid_until` > NOW(), 1, 0) as `ifTicketPaid`, IF(`exit_time` IS NULL, 1, 0) as `ifCarIn` FROM `tickets` WHERE `barcode` = "+ barcode 
				# query = "SELECT if(t.`paid_until` IS NOT NULL AND t.`paid_until` > NOW(), 1, 0) as `ifTicketPaid`, if(t.`exit_time` IS NULL, 1, 0) as `ifCarIn`, if(t.`paid_at` IS NOT NULL AND  NOW() < (t.`paid_at` + INTERVAL p.`time_to_leave` MINUTE), 1 , 0) as ifCanLeave FROM `tickets` t INNER JOIN `parkings` p ON t.`parking_id` = p.`id` WHERE t.`barcode` = "+ barcode 
				# query = "SELECT NOW(), t.`enter_time`, p.`exit_time`, (t.`enter_time` + INTERVAL p.`exit_time` MINUTE), if(NOW() < (t.`enter_time` + INTERVAL p.`exit_time` MINUTE), 1 , 0) as ifCanExit FROM `tickets` t INNER JOIN `parkings` p ON t.`parking_id` = p.`id` WHERE t.`barcode` = " + barcode 
				query = "SELECT NOW(), t.`enter_time`, p.`exit_time`, (t.`enter_time` + INTERVAL p.`exit_time` MINUTE), if(t.`exit_time` IS NOT NULL || (NOW() > (t.`enter_time` + INTERVAL p.`exit_time` MINUTE)), 0 , 1) as ifCanExit FROM `tickets` t INNER JOIN `parkings` p ON t.`parking_id` = p.`id` WHERE t.`barcode` =" + barcode
				cursor.execute(query) 
				rows = cursor.fetchall()
			except Exception as exc:			
				# displayMsg("MySql is disconnected")
				displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
				print("MySql is disconnected")
				connctionState = 0
				# GPIO.output(DENYLED, GPIO.HIGH)
				relay_status = relay_status | DENYLED
				bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				time.sleep(0.3)
				break
			# the button is pressed
			# print("barcode is checking....")
			#displayMsg(barcode)

			if cursor.rowcount != 1:
				print("NO EXIST TICKET GO BACK OR PUNCH ANOTHER TICKET")
				displayMsg("Nepostojeci TIKET! Ocitajte drugi TIKET!", "punched_card_not_exist.gif")
				# GPIO.output(Barrier1, GPIO.HIGH)
				# relay_status = relay_status | Barrier1
				# bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
				continue


			row = rows[0]

			PaidOrNot = row[4]
			print(PaidOrNot)
			if PaidOrNot == 1:
				try:
					query = "update tickets set free_exit = 1, exit_time = NOW() where `barcode` = %(barcode)s" 
					cursor.execute(query, {'barcode': barcode})
					cnx.commit()		
				except Exception as exc:			
					print str(exc)
					# displayMsg("MySql is disconnected")
					displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
					print("MySql is disconnected")
					connctionState = 0
					# GPIO.output(DENYLED, GPIO.HIGH)
					relay_status = relay_status | DENYLED
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

					time.sleep(0.3)
					break
			if PaidOrNot == 0:
				#query = "select StatusTicket_pay, StatusCar_in from ticket where barcode = "+ barcode 

				#+ barcode
				#IF(`exit_time` IS NULL, true, false)
				try:
					query = "UPDATE `ql` SET `time` = NOW() WHERE `id` = 1"
					cursor.execute(query)
					cnx.commit()
					# query = "SELECT IF(`paid_until` IS NOT NULL AND `paid_until` > NOW(), 1, 0) as `ifTicketPaid`, IF(`exit_time` IS NULL, 1, 0) as `ifCarIn` FROM `tickets` WHERE `barcode` = "+ barcode 
					# query = "SELECT if(t.`paid_until` IS NOT NULL AND t.`paid_until` > NOW(), 1, 0) as `ifTicketPaid`, if(t.`exit_time` IS NULL, 1, 0) as `ifCarIn`, if(t.`paid_at` IS NOT NULL AND  NOW() < (t.`paid_at` + INTERVAL p.`time_to_leave` MINUTE), 1 , 0) as ifCanLeave FROM `tickets` t INNER JOIN `parkings` p ON t.`parking_id` = p.`id` WHERE t.`barcode` = "+ barcode 
					query = "SELECT if(t.`paid_until` IS NOT NULL AND t.`paid_until`+ INTERVAL p.`time_to_leave` MINUTE > NOW(), 1, 0) as `ifTicketPaid`, if(t.`exit_time` IS NULL, 1, 0) as `ifCarIn`, if(t.`paid_at` IS NOT NULL AND NOW() < (t.`paid_at` + INTERVAL p.`time_to_leave` MINUTE), 1 , 0) as ifCanLeave FROM `tickets` t INNER JOIN `parkings` p ON t.`parking_id` = p.`id` WHERE t.`barcode` = "+ barcode 
					cursor.execute(query) 
					rows = cursor.fetchall()
				except Exception as exc:			
					# displayMsg("MySql is disconnected")
					displayMsg(MySqlStatusOff_msg, "mysql_is_disonnected.gif")
					print("MySql is disconnected")
					connctionState = 0
					# GPIO.output(DENYLED, GPIO.HIGH)
					relay_status = relay_status | DENYLED
					bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
					time.sleep(0.3)
					break
				# the button is pressed
				print("barcode is checking....")
				#displayMsg(barcode)












				if cursor.rowcount != 1:
					print("NO EXIST TICKET GO BACK OR PUNCH ANOTHER TICKET")
					displayMsg("Nepostojeci TIKET! Ocitajte drugi TIKET!", "punched_card_not_exist.jpg")
					# GPIO.output(Barrier1, GPIO.HIGH)
					# relay_status = relay_status | Barrier1
					# bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)
					continue


				row = rows[0]
				StatusTicket_pay = row[0]
				StatusCar_in = row[1]
				IfCanLeave   = row[2]

				if StatusTicket_pay == 0 or StatusCar_in == 0 or IfCanLeave == 0:
					print("Already out or Not Paid. please go back")
					print(StatusTicket_pay)
					print(StatusCar_in)
					#print(QueryTime)
					if StatusTicket_pay == 0:
						displayMsg("Tiket nije placen!", "punched_card_not_exist.jpg")
					elif IfCanLeave == 0:
						displayMsg("Prekoracili ste vreme za izlazak!", "punched_card_not_exist.jpg")
					else:
						displayMsg("Tiket je vec ponisten!", "punched_card_not_exist.jpg")
					# GPIO.output(Barrier1, GPIO.HIGH)
					# relay_status = relay_status | Barrier1
					# bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

					continue
			today = datetime.datetime.now()
			print("Updating database")
			LeaveTime = "%04d-%02d-%02d %02d:%02d:%02d"%(today.year, today.month, today.day, today.hour, today.minute, today.second)
			#query = "update ticket  set StatusCar_in = 0, LeaveTime = \'" + LeaveTime + "\' where BarCode = %(barcode)s" 
			query = "update tickets set exit_time = NOW() where `barcode` = %(barcode)s" 

			
			try:
				cursor.execute(query, {'barcode': barcode})
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
				break

			print("******* Sucessfully passed *******")
			
			# GPIO.output(Barrier1,GPIO.LOW)
			# GPIO.output(Barrier2,GPIO.HIGH)
			relay_status = relay_status & (~Barrier1)
			relay_status = relay_status | Barrier2
			bus.write_byte_data(I2C_ADDRESS, 0x09, relay_status)

			# GPIO.output(B2STATELED, GPIO.HIGH)
			print("Waiting for passing the barrier2...")
			displayMsg("Slobodan prolaz hvala. Napustite zonu rampe !", "user_can_enter_to_the_parkinglot_over_rfid.jpg")
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
				displayMsg("Izlazna rampa je otvorena", "user_can_enter_to_the_parkinglot_over_rfid.jpg")
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
			print("Successfully Exited!")
			# displayMsg("AIRPORT BELGRADE")

			ftp_file_case = "%s_%s"%(barcode, ftp_file_case)
			compared_option = 2
			compared_value = barcode
			break
			# GPIO.output(B2STATELED, GPIO.LOW)