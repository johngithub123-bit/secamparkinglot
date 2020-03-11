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

fob.write('<script src = \"time.js\"></script>');
fob.write('<body onload=\"startTime()\">\n')

fob.write('<div id=\"root\" style = \"' + global_width + ';' + global_height + ';' + font + ';border:1px solid black;">\n')

if image_path == 'screensaver.png':
	fob.write('<div style = \"' + image_path + '\">\n')
	fob.write('<img src = \"' + image_path + '\"></div>\n')
else:
	fob.write('<div class = \"headerbar\" style = \"' + textbox_width + ';' + textbox_height + ';' + textbox_background + ';' + textbox_fontcolor + ';\">\n')

	#if orientation[13:17] == 'land':
	#	fob.write('A<BR/>I<BR/>R<BR/>P<BR/>O<BR/>R<BR/>T</p></th>\n')
	#else:
	#	fob.write('AIRPORT</p></th>\n')
	fob.write('<div style=\"display: table-cell; vertical-align: middle;\">AIRPORT</div></div>\n')

	fob.write('<div class = \"messagepart\" style=\"' + messagebox_background + ';' + messagebox_fontcolor + ';' + messagebox_height + ';' + messagebox_width + ';\">\n')
	fob.write('<div style=\"display: table-cell; vertical-align: middle;\">' + messages + '</div></div>\n')


	fob.write('<div class = \"clockbox\" style=\"float:left;' + clockbox_width + ';' + clockbox_height  + ';' + clockbox_background + ';' + clockbox_fontcolor + ';\">\n')
	fob.write('<div id = "txt" style=\"display: table-cell; vertical-align: middle;\">TIME: ' + str(current_hour) + ':' + str(current_minute) + ':' + str(current_second) + '</div></div>\n')

	fob.write('<div style = \"float: left;' + imagebox_width + ';' + imagebox_height + ';\">\n')
	fob.write('<img src = \"' + image_path + '\" style = \"width:100%;height:100%;\"></div>\n')

fob.write('</div>\n')

fob.write('</body>\n')

fob.write('</html>\n')

fob.close()