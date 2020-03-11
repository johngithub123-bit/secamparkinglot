import os
import sys
import datetime

config_no = 0
line_no = 0

global_width = ''
global_height = ''
font = ''
orientation = ''
textbox_width = ''
textbox_height = ''
textbox_background = ''
textbox_fontcolor = ''
messagebox_width = ''
messagebox_height = ''
messagebox_background = ''
messagebox_fontcolor = ''
imagebox_width = ''
imagebox_height = ''
imagebox_background = ''
clockbox_width = ''
clockbox_height = ''
clockbox_background = ''
clockbox_fontcolor = ''
active = ''
start_time = ''
time_images = ''

messages = ''
image_path = str(sys.argv[1])

current_hour = datetime.datetime.now().hour
current_minute = datetime.datetime.now().minute
current_second = datetime.datetime.now().second

for i in range(2, len(sys.argv)):
	messages += str(sys.argv[i]) + ' '

for line in open('config.txt','r').readlines():
	if line[0:8] == '[global]':
		config_no = 1
		continue
	elif line[0:9] == '[textbox]':
		config_no = 2
		continue
	elif line[0:10] == '[Msg. box]':
		config_no = 3
		continue
	elif line[0:11] == '[Image box]':
		config_no = 4
		continue
	elif line[0:11] == '[clock box]':
		config_no = 5
		continue
	elif line[0:13] == '[screensaver]':
		config_no = 6
		continue

	if config_no == 1:
		if line[0:5] == 'width':
			global_width = line[0:len(line) - 2]
		elif line[0:6] == 'height':
			global_height = line[0:len(line) - 2]
		elif line[0:4] == 'font':
			font = line[0:len(line) - 2]
		elif line[0:4] == 'orie':
			orientation = line[0:len(line) - 2]

	elif config_no == 2:
		if line[0:5] == 'width':
			textbox_width = line[0:len(line) - 2]
		elif line[0:6] == 'height':
			textbox_height = line[0:len(line) - 2]
		elif line[0:4] == 'back':
			textbox_background = line[0:len(line) - 2]
		elif line[0:4] == 'colo':
			textbox_fontcolor = line[0:len(line) - 2]

	elif config_no == 3:
		if line[0:5] == 'width':
			messagebox_width = line[0:len(line) - 2]
		elif line[0:6] == 'height':
			messagebox_height = line[0:len(line) - 2]
		elif line[0:4] == 'back':
			messagebox_background = line[0:len(line) - 2]
		elif line[0:4] == 'colo':
			messagebox_fontcolor = line[0:len(line) - 2]

	elif config_no == 4:
		if line[0:5] == 'width':
			imagebox_width = line[0:len(line) - 2]
		elif line[0:6] == 'height':
			imagebox_height = line[0:len(line) - 2]
		elif line[0:4] == 'back':
			imagebox_background = line[0:len(line) - 2]

	elif config_no == 5:
		if line[0:5] == 'width':
			clockbox_width = line[0:len(line) - 2]
		elif line[0:6] == 'height':
			clockbox_height = line[0:len(line) - 2]
		elif line[0:4] == 'back':
			clockbox_background = line[0:len(line) - 2]
		elif line[0:4] == 'colo':
			clockbox_fontcolor = line[0:len(line) - 2]

	elif config_no == 6:
		if line[0:6] == 'active':
			active = line[0:len(line) - 2]
		elif line[0:5] == 'start':
			start_time = line[0:len(line) - 2]
		elif line[0:4] == 'time':
			time_images = line[0:len(line) - 2]
			line_no = 0

fob = open('display.html', 'w')
fob.write('<html>\n')
fob.write('<meta http-equiv=\"refresh\"" content=\"1\" />\n')
if orientation[13:17] == 'land':
	fob.write('<link rel=\"stylesheet\" href=\"style_land.css\">\n')
else:
	fob.write('<link rel=\"stylesheet\" href=\"style_portrait.css\">\n')

fob.write('<body>\n')

fob.write('<table style=\"' + global_width + ';' + global_height + ';' + font + ';">\n')

if image_path == 'screensaver.png':
	fob.write('<td style = \"' + image_path + '\">\n')
	fob.write('<img src = \"' + image_path + '\"></td>\n')
else:
	fob.write('<tr><th style = \"' + textbox_width + ';' + textbox_height + ';' + textbox_background + ';' + textbox_fontcolor + ';\">\n')
	fob.write('<p class = \"headerbar">')

	#if orientation[13:17] == 'land':
	#	fob.write('A<BR/>I<BR/>R<BR/>P<BR/>O<BR/>R<BR/>T</p></th>\n')
	#else:
	#	fob.write('AIRPORT</p></th>\n')

	fob.write('AIRPORT</p></th></tr>\n')

	fob.write('<tr><th class = \"messagebox\" style=\"' + messagebox_background + ';' + messagebox_fontcolor + ';' + messagebox_height + ';' + messagebox_width + ';\">\n')
	fob.write('<p class = \"messagepart\">' + messages + '</p></th></tr>\n')

	fob.write('<tr style=\"' + clockbox_height + '\">')

	fob.write('<td class = \"clockbox\" style=\"' + clockbox_width  + ';' + clockbox_background + ';\">\n')
	fob.write('<p class = \"timestampbar\" style = \"' + clockbox_fontcolor)
	fob.write(';\">TIME: ' + str(current_hour) + ':' + str(current_minute) + ':' + str(current_second) + '</p></td>\n')

	fob.write('<td style = \"' + imagebox_width + '\">\n')
	fob.write('<img src = \"' + image_path + ' style = \"width:100%;height:100%;\"></td>\n')

	fob.write('</tr>')

fob.write('</table>\n')

fob.write('</body>\n')

fob.write('</html>\n')

fob.close()