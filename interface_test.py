import gtk
import threading
import time
import os

gtk.threads_init()

class FractionSetter(threading.Thread):
	stopthread = threading.Event()
	global messagebar
	global imagepart
	global imagepath
	def run(self):
		imagepath = ''
		screensaver_flag = 0
		while not self.stopthread.isSet():
			i = 0
			for line in open('message.txt','r').readlines():
				if i == 0:
					if line[0:6] == 'screen' or screensaver_flag == 0:
						os.system('python screensaver.py')
						screensaver_flag = 1
						continue
					else:
						screensaver_flag = 0
					messagebar.set_label(line)
				elif i == 1:
					if imagepath != line:
						imagepart.set_from_file(line)
						imagepath = line
				i = i + 1
			time.sleep(1)

	def stop(self):
		self.stopthread.set()

def main_quit(obj):
	global fs
	fs.stop()
	gtk.main_quit()

window = gtk.Window()
window.connect('destroy', gtk.main_quit)

vbox = gtk.VBox()
headbar = gtk.Label('Parkinglot')
headhbox = gtk.HBox()
headhbox.pack_start(headbar)
headhbox.set_size_request(800, 50)

messagehbox = gtk.HBox()
messagebar = gtk.Label()
messagehbox.pack_start(messagebar)
messagehbox.set_size_request(800, 300)

bottomhbox = gtk.HBox(True)
clockhbox = gtk.HBox()
clockshow = gtk.Label('Time:\n09:03:03')
clockhbox.pack_start(clockshow)
clockhbox.set_size_request(400, 250)

imagehbox = gtk.HBox()
imagepart = gtk.Image()
imagehbox.pack_start(imagepart)
# pixbuf = gtk.gdk.pixbuf_new_from_file(imagepath)
# pixbuf = pixbuf.scale_simple(400, 300, gtk.gdk.INTERP_BILINEAR)
# imagepart.set_from_file(imagepath)
# imagepart.set_from_pixbuf(pixbuf)
imagehbox.set_size_request(400, 250)

bottomhbox.pack_start(clockhbox)
bottomhbox.pack_start(imagehbox)

vbox.pack_start(headhbox)
vbox.pack_start(messagehbox)
vbox.pack_start(bottomhbox)

window.add(vbox)
window.fullscreen()

fs = FractionSetter()
fs.start()

window.show_all()
window.connect('destroy', main_quit)
# Put gtk.main() last so our callback functions are used.
gtk.main()