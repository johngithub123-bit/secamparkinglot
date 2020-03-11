import gtk
import threading
import time

gtk.threads_init()

class FractionSetter(threading.Thread):
	stopthread = threading.Event()
	def run(self):
		while not self.stopthread.isSet():
			i = 0
			for line in open('message.txt','r').readlines():
				if i == 0:
					if line[0:6] != 'screen':
						print('screen')
						gtk.main_quit()
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
imagepart = gtk.Image()
vbox.pack_start(imagepart)
imagepart.set_from_file('screensaver.png')

window.add(vbox)
window.fullscreen()

fs = FractionSetter()
fs.start()

window.show_all()
window.connect('destroy', main_quit)
# Put gtk.main() last so our callback functions are used.
gtk.main()