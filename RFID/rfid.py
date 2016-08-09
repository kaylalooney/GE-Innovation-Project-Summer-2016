# Python 3
# Kayla Looney -- GE Summer Intern Innovation Raspberry Pi 3 Project

# Import a bunch of stuff
import subprocess
from time import sleep
import sqlite3
import datetime
import sys

LOCATION= "front door"  # global variable that is unique to each Pi
MASTER_DICT = {'a0  55  25  11': "white card", "04  f2  48  ea  79  4d  80": "little black circle"} # master dict is used to remember the name for each NFC tag

conn = sqlite3.connect('Pi_NFC.db') # if database does not yet exist, one will be created, otherwise the existing one will be used
c = conn.cursor()

# Create table
#c.execute('''CREATE TABLE nfc (date text,name text,uid real,location text)''') # uncomment when you are running the program for the first time

# setup light part
import RPi.GPIO as GPIO
blue_pin=36
red_pin=33
green_pin=37

GPIO.setmode(GPIO.BOARD)

GPIO.setup(blue_pin, GPIO.OUT)
GPIO.setup(red_pin, GPIO.OUT)
GPIO.setup(green_pin, GPIO.OUT)


def view_all(number_of_entries):
    # View the entries in the table:
    c.execute('SELECT * FROM nfc ORDER BY date desc')
    for each in c.fetchmany(number_of_entries):
        time,name,id,loc=each
        print(time, " ",name, "was at ", loc)


def view_by_card(number_of_entries):
    print("finding records for each card...\n")
    find_records_by_name("white card", number_of_entries)
    find_records_by_name("little black circle", number_of_entries)
    find_records_by_name("unknown", number_of_entries)


def find_records_by_uid(uid,count):
    print("finding all records for: ",uid)
    c.execute('SELECT * FROM nfc WHERE uid=?  ORDER BY date desc',(uid,))
    for row in c.fetchmany(count):
        time,name,id,loc=row
        print(time, " ",name, "was at ", loc)
    print()


def find_records_by_name(name,count):
    print("finding all records for:",name)
    c.execute('SELECT * FROM nfc WHERE name=?  ORDER BY date desc',(name,))
    for row in c.fetchmany(count):
        time,name,id,loc=row
        print(loc," at ",time)
    print()


scans = 0

print("Welcome to NFC scanning")
number_of_scans=input("How many times would you like to scan? [Enter a number or 'inf' for continuous scanning] ")

if number_of_scans=="inf":
    number_of_scans= sys.maxsize


while scans < int(number_of_scans):
    proc = subprocess.Popen('/home/pi/NFC/libnfc/examples/doc/out', stdout=subprocess.PIPE)
    GPIO.output(blue_pin, True)  # Turn on blue light (signals the Pi is ready to start scanning)
    temp = proc.stdout.read()
    GPIO.output(blue_pin, False)  # Turn off blue light (signals the Pi is busy and NOT ready to scan)
    print("scan: ", scans+1)
    id = temp[14:].strip()
    id=id.decode('UTF-8')
    print( "UID: " + id)

    if id in MASTER_DICT: # if the tag is known, turn on the green light and display the name associated with the tag
        GPIO.output(green_pin, True)
        print("identity: ", MASTER_DICT[id])
        name=MASTER_DICT[id]
    else: # otherwise turn on the red light
        GPIO.output(red_pin, True)
        print("unknown... not in dict")
        name="unknown"

    # Get current date and time
    current_time = datetime.datetime.today()
    current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

    # Insert a row of data
    c.execute("insert INTO nfc VALUES (?,?,?,?)", (str(current_time), name, id, LOCATION,))

    # Save (commit) the changes
    conn.commit()

    sleep(0.5) # helps eliminate accidental re-scans (and allows the user a little more time to see a green or red light)

    # Turn the lights back off
    GPIO.output(red_pin, False)
    GPIO.output(green_pin, False)

    scans += 1
    print()

# Won't get down here if the user entered "inf" above
response=input("Would you like to view entries for all cards together? (y/n)")
if response=="y":
    count = input("How many entries? ")
    view_all(int(count))

response=input("Would you like to view entries for each card? (y/n)")
if response=="y":
    count = input("How many entries? ")
    view_by_card(int(count))


# Close the connection
conn.close()

GPIO.output(blue_pin, False) # Turn the main blue light off
GPIO.cleanup()

print("goodbye!")
