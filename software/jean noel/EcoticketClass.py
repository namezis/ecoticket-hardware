# -*- coding: utf-8 -*-
import os
import sys
import struct
import random

import PythonMagick

import qrcode

from uuid import getnode as get_mac

from bluetooth import *
import bluetooth
import threading
import lightblue

import time
import datetime

import ParserClass
import UtilsClass

from Naked.toolshed.shell import execute_js

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from os.path import expanduser

class EcoTicket():
    ## Conf values
    # 0 -> Title
    # 1 -> Language
    # 2 -> Category
    # 3 -> Number of useless lines at the beginning of the ticket TXT
    # 4 -> EOF word
    # 5 -> Parser delimiters
    conf_values = []

    ## Ticket data
    ticketData = ""

    ## Ticket temp name
    ticketName = ""

    ## Device name
    deviceName = "EcoTicketBeta"

    ## Parser Instance
    parser = ParserClass.Parser()

    ## Utils Instance
    utils = UtilsClass.Utils()

    ## PDF printed path
    home = expanduser("~")
    printedpath = home + "/PDF/tmp.pdf"

    def getMacAddress(self):
        bdaddr = ""
        rawaddr = self.utils.read_local_bdaddr()
        tmp = rawaddr[0]
        tmp = tmp.split(":")
        for i in tmp:
            if len(i) == 1:
                bdaddr = bdaddr+"0"+i+":"
            else:
                bdaddr = bdaddr+i+":"
        bdaddr = bdaddr[:-1]
        return bdaddr


    ## Define conf values from the conf file
    def getConfValues(self):
        self.conf_values = self.parser.getConf()
        return

    ## Wait for PDF to be printed
    def waitPDF(self):
	class MyHandler(FileSystemEventHandler):
    	    def on_modified(self, event):
	        path = expanduser("~") + "/PDF"
	        newname = path + "/tmp.pdf"
	        if event.src_path != path:
		    print "waitPDF : PDF printed !"
		    observer.stop()
		    os.rename(event.src_path, newname)

        dirpath = self.home + "/PDF"
        event_handler = MyHandler()
        observer = Observer()
        observer.schedule(event_handler, path=dirpath, recursive=False)
        observer.start()
	prev_mod = os.stat(dirpath + "/tmp.pdf").st_mtime

        try:
            while True:
                time.sleep(1)
		act_mod = os.stat(dirpath + "/tmp.pdf").st_mtime
		if act_mod > prev_mod:
		    return
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    ## Convert PDF to TXT
    def readPDF(self, pdf):
        ## Create new TXT file to send with the pdf
        txtFileName = str(random.getrandbits(32))
        #txtFile = open(txtFileName+'.txt', 'w')

        input = pdf
        output = "./parsed/"+txtFileName+'.txt'
        os.system(("pdftotext %s %s") %( input , output))
        return output

    ## Create and display QRCode
    def createAndDisplayQRCode(self): 
        mac = self.getMacAddress()

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.deviceName + '-' + mac)
        qr.make(fit=True)

        img = qr.make_image()

        img.show()

    ## Manage NFC Communication
    def nfcCommunication(self):
        mac = self.getMacAddress()

        os.system(("python beam.py send text %s") %(self.deviceName + '-' + mac))

    ## Manage bluetooth Connection
    def bluetoothConnection(self, pdfPath, txtPath, total):
        toBreak = 0

        ShopName = self.conf_values[0]
        Category = self.conf_values[2]
        ctime = time.ctime(os.path.getctime(pdfPath))
        date = datetime.datetime.strptime(ctime, "%a %b %d %H:%M:%S %Y")
        date = date.strftime("%d-%m-%Y_%H-%M-%S")
        total = total.replace(',', '-')
        total = total.rstrip('\n')
        total = total.rstrip('€')
        ShopName = ShopName.replace(' ', '-')
        pdfRealName = date + '_' + total + '_' + ShopName

        name_tmp = open('parsed/name_tmp.txt', 'w')
        pdf_tmp = open('parsed/pdf_tmp.txt', 'w')
        txt_tmp = open('parsed/txt_tmp.txt', 'w')
        pdf_data = open(pdfPath, 'rb')
        txt_data = open(txtPath, 'rb')

        name_tmp.write(pdfRealName)
        pdf_tmp.write(pdf_data.read())
        txt_tmp.write(txt_data.read())

        name_tmp.close()
        pdf_tmp.close()
        txt_tmp.close()
        pdf_data.close()
        txt_data.close()

        success = execute_js('js/main.js')

#        name = "BluetoothChat"
#        uuid = "fa87c0d0-afac-11de-8a39-0800200c9a66"
#
#        server_sock = bluetooth.BluetoothSocket( bluetooth.RFCOMM )
#        server_sock.bind(("", bluetooth.PORT_ANY))
#        server_sock.listen(1)
#        port = server_sock.getsockname()[1]
#
#        bluetooth.advertise_service( server_sock, name, uuid )
#
#        print "Waiting for connection on RFCOMM channel %d" % port
#
#        class echoThread(threading.Thread):
#            def __init__ (self,sock,client_info):
#                threading.Thread.__init__(self)
#                self.sock = sock
#                self.client_info = client_info
#            def run(self):
#                try:
#                    ## Send PDF
#                    time.sleep(1)
#                    self.sock.send("SOF PDF " + pdfRealName)
#                    time.sleep(1)
#                    pdfSize = os.path.getsize(pdfPath)
#                    f = open(pdfPath,'rb')
#                    print 'Sending PDF ...'
#                    l = f.read(pdfSize)
#                    self.sock.send(l)
#                    #while (l):
#                    #    self.sock.send(l)
#                    #    l = f.read(1024)
#                    #    print 'Sending PDF ...'
#                    f.close()
#                    print 'Sending PDF done !'
#                    time.sleep(1)
#                    self.sock.send("EOF PDF")
#
#                    ## Send TXT
#                    time.sleep(1)
#                    self.sock.send("SOF TXT " + pdfRealName)
#                    time.sleep(1)
#                    txtSize = os.path.getsize(txtPath)
#                    f = open(txtPath,'rb')
#                    print 'Sending TXT ...'
#                    l = f.read(txtSize)
#                    self.sock.send(l)
#                    #while (l):
#                    #    print 'Sending TXT ...'
#                    #    self.sock.send(l)
#                    #    l = f.read(1024)
#                    f.close()
#                    print 'Sending TXT done !'
#                    time.sleep(1)
#                    self.sock.send("EOF TXT")
#
#                except IOError:
#                    pass
#                self.sock.close()
#                print self.client_info, ": disconnected"
#                ## While can't exit thread, do os.remove here
#                os.remove(txtPath)
#
#        timeout = time.time() + 10
#        while (True):
#            client_sock, client_info = server_sock.accept()
#            print client_info, ": connection accepted"
#            echo = echoThread(client_sock, client_info)
#            echo.setDaemon(True)
#            echo.start()
#
#        server_sock.close()
        print "all done"

    def main(self):
        ###### For test purposes, PDF path is hardcoded
        # pdf = "pdfs/le_comptoir_1.pdf"
        ######

	pdf = self.printedpath

        choice = 0

        print ("Main : Start Getting Conf Values ...")
        ## Define conf values from the conf file
        self.getConfValues()
        print ("Main : End Getting Conf Values ...")

        print ("Main : Start Waiting for PDF ...")
	## Wait for PDF to be printed
        self.waitPDF()
        print ("Main : End Waiting for PDF ...")

        print("Main : Start Reading PDF ...")
        ## Test read PDF
        txtPath = self.readPDF(pdf)
        print("Main : End Reading PDF ...")

        print("Main : Start Parsing TXT File ...")
        ## Parse TXT file
        total = self.parser.parseFile(txtPath, self.conf_values)
        print("Main : End Parsing TXT File ...")

        while (choice != 1 and choice != 2):
            choice = input('Choose QRCode(1) or NFC(2): ')
            if (choice == 1):
                print("Main : Start Displaying QRCode ...")
                ## Test display qrcode
                self.createAndDisplayQRCode()
                print("Main : End Displaying QRCode ...")
            elif (choice == 2):
                print("Main : Start NFC ...")
                ## Test display qrcode
                self.nfcCommunication()
                print("Main : End NFC ...")
            else :
                print("Wrong Choice !")

        print("Main : Start Sending via Bluetooth ...")
        ## Test bluetooth
        self.bluetoothConnection(pdf, txtPath, total)
        print("Main : End Sending via Bluetooth ...")

        ## Clean temp files
        os.remove(txtPath)

	self.main()

        return
