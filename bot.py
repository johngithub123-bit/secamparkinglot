from Tkinter import *
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common import action_chains, keys
from selenium.webdriver.support.ui import Select
import tkMessageBox
import time
import sys

root = Tk()
root.title("froya2.troyacom BOT 1.0")
root.geometry("480x500+0+0")

heading = Label(root, text="Wecome Rune Martinussen", font=("arial", 20, "bold"), fg="steelblue").pack()

label1 = Label(root, text="Server Address: ", font = ("arial", 10), fg="black").place(x=10, y=150)
Userextraction = StringVar()
entry_box = Entry(root, textvariable=Userextraction, width=25, bg="white").place(x = 280, y = 150)

label2 = Label(root, text="User Name: ", font = ("arial", 10), fg="black").place(x=10, y=170)
Username = StringVar()
entry_box = Entry(root, textvariable=Username, width=25, bg="white").place(x = 280, y = 170)

label3 = Label(root, text="Password: ", font = ("arial", 10), fg="black").place(x=10, y=190)
Password = StringVar()
entry_box = Entry(root, textvariable=Password, width=25, bg="white").place(x = 280, y = 190)

label4 = Label(root, text="Display Name: ", font = ("arial", 10), fg="black").place(x=10, y=250)
Displayname = StringVar()
entry_box = Entry(root, textvariable=Displayname, width=25, bg="white").place(x = 280, y = 250)

label5 = Label(root, text="From: ", font = ("arial", 10), fg="black").place(x=10, y=270)
From = StringVar()
entry_box = Entry(root, textvariable=From, width=25, bg="white").place(x = 280, y = 270)

label6 = Label(root, text="To: ", font = ("arial", 10), fg="black").place(x=10, y=290)
To = StringVar()
entry_box = Entry(root, textvariable=To, width=25, bg="white").place(x = 280, y = 290)

label7 = Label(root, text="Secret: ", font = ("arial", 10), fg="black").place(x=10, y=310)
Secret = StringVar()
entry_box = Entry(root, textvariable=Secret, width=25, bg="white").place(x = 280, y = 310)



def do_it():
	user = str(Username.get())
	passw = str(Password.get())
	server = str(Userextraction.get())
	display = str(Displayname.get())
	sec = str(Secret.get())
	f = str(From.get())
	t = str(To.get())

	if server == '':
		tkMessageBox.showerror("Error","Please input Extraction value.")
		sys.exit()

	if user == '':
		tkMessageBox.showerror("Error","Please input User Name.")
		sys.exit()

	if passw == '':
		tkMessageBox.showerror("Error","Please input Password.")
		sys.exit()

	if display == '':
		tkMessageBox.showerror("Error","Please input Display Name.")
		sys.exit()

	if sec == '':
		tkMessageBox.showerror("Error","Please input Security Number.")
		sys.exit()

	if f > t:
		tkMessageBox.showerror("Error","Please input valid From and To number.")
		sys.exit()



	driver = webdriver.Chrome(executable_path=r"C:\Chrome\chromedriver.exe")
	# driver.get("http://"froya2.troyacom.no:444/admin/config.php)
	driver.get("http://" + server)
	button = driver.find_element_by_id('login_admin')
	button.click()

	name = driver.find_element_by_name('username')
	pwd = driver.find_element_by_name('password')
	form = driver.find_element_by_id('loginform')

	action = action_chains.ActionChains(driver)
	action.send_keys(user)
	action.send_keys(Keys.TAB)
	action.send_keys(passw)
	action.send_keys(Keys.TAB)
	action.send_keys(Keys.ENTER)
	action.perform()
	time.sleep(10)
	
	for x in range(int(f), int(t)+1):

		driver.get("http://" + server + "/admin/config.php?display=extensions")
		button = driver.find_element_by_name('Submit')
		button.click()
		time.sleep(5)

		extension = driver.find_element_by_id('extension')
		extension.clear()
		extension.send_keys(x)
		disname = driver.find_element_by_id('name')
		disname.clear()
		disname.send_keys(display)
		secret = driver.find_element_by_id('devinfo_secret')
		secret.clear()
		secret.send_keys(sec)
		select1 = Select(driver.find_element_by_id('devinfo_transport'))
		select1.select_by_visible_text('WSS Only')
		select2 = Select(driver.find_element_by_id('devinfo_avpf'))
		select2.select_by_visible_text('Yes')
		select3 = Select(driver.find_element_by_id('devinfo_force_avp'))
		select3.select_by_visible_text('Yes')
		select4 = Select(driver.find_element_by_id('devinfo_icesupport'))
		select4.select_by_visible_text('Yes')
		select5 = Select(driver.find_element_by_id('dtls_enable'))
		select5.select_by_visible_text('Yes')

		driver.find_element_by_xpath("//*[@id='page_body']/form/table/tbody/tr[100]/td/h6/input").click()

	tkMessageBox.showerror("Success","Congratulations! Your operation finished successfully.")
	sys.exit()

work = Button(root, text="SUBMIT", font = ("arial", 30), bg="lightgreen", command=do_it).place(x=265, y=400)
root.mainloop()