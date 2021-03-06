#!/usr/bin/env python3

#
# Show scrolling texts on an ESP8266 driven 5x8 matrix display from WS2812 leds.
#
# See: matrix.lua
#
# Usage:
#
# parameter 1:      the text to be displayed
# parameter 2 3 4:  the green/red/blue value of the text foreground color
# parameter 5 6 7:  the green/red/blue value of the background color
# parameter 8:      wait until the message is shown N times
#                   (default 1, use 0 for no wait)
# parameter 9:      the speed in 0.01 seconds per pixel shift
# parameter 10:     the IP4 address of the ESP with the display
#

import socket
import array
import sys

import ephem

import time

#time.sleep(10)
#sys.exit(0)

socket.setdefaulttimeout(20)

display="192.168.0.190"

msg='12345678.90'

count= 1
speed= 30
scaling=1

# Background color: (very dimmed green)
bgc= [ 2, 0, 0 ]

# Foreground color: (dimmed white)
fgc= [ 20, 20, 20 ]

l= len(sys.argv)
if l >= 2:
    msg= sys.argv[1]
if l >= 3:
    fgc= [ int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]) ]
if l >= 6:
    bgc= [ int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]) ]
if l >= 9:
    count= int(sys.argv[8])
if l >= 10:
    speed= int(sys.argv[9])
if l >= 11:
    display= sys.argv[10]


#
# Font bitmap data converted from the X11 3x5 micro font:
#
bm = {
   ' ': [3, [ 0x00, 0x00, 0x00, 0x00, 0x00 ] ],
   #'!': [2, [ 0xC0, 0xC0, 0xC0, 0x00, 0xC0 ] ],
   '!': [1, [ 0x80, 0x80, 0x80, 0x00, 0x80 ] ],
   '"': [3, [ 0xA0, 0xA0, 0x00, 0x00, 0x00 ] ],
   '#': [3, [ 0xA0, 0xE0, 0xA0, 0xE0, 0xA0 ] ],
   '$': [3, [ 0x40, 0xE0, 0xC0, 0x60, 0xE0 ] ],
   '%': [3, [ 0xA0, 0x60, 0xC0, 0xA0, 0x00 ] ],
   '&': [3, [ 0x40, 0x40, 0xE0, 0xC0, 0x40 ] ],
   '\'': [3, [ 0x20, 0x60, 0x00, 0x00, 0x00 ] ],
   '(': [3, [ 0x20, 0x40, 0x40, 0x40, 0x20 ] ],
   ')': [3, [ 0x80, 0x40, 0x40, 0x40, 0x80 ] ],
   '*': [3, [ 0xA0, 0x40, 0xE0, 0x40, 0xA0 ] ],
   '+': [3, [ 0x00, 0x40, 0xE0, 0x40, 0x00 ] ],
   ',': [2, [ 0x00, 0x00, 0x00, 0x40, 0xC0 ] ],
   '-': [3, [ 0x00, 0x00, 0xE0, 0x00, 0x00 ] ],
   #'.': [2, [ 0x00, 0x00, 0x00, 0xC0, 0xC0 ] ],
   '.': [1, [ 0x00, 0x00, 0x00, 0x00, 0x80 ] ],
   '/': [3, [ 0x20, 0x20, 0x40, 0x40, 0x80 ] ],
   '0': [3, [ 0x40, 0xA0, 0xA0, 0xA0, 0x40 ] ],
   '1': [2, [ 0x40, 0xC0, 0x40, 0x40, 0x40 ] ],
   '2': [3, [ 0xC0, 0x20, 0x40, 0x80, 0xE0 ] ],
   #'3': [3, [ 0xC0, 0x20, 0x60, 0x20, 0xE0 ] ],
   '3': [3, [ 0xC0, 0x20, 0x60, 0x20, 0xC0 ] ],
   #'4': [3, [ 0xA0, 0xA0, 0xA0, 0xE0, 0x20 ] ],
   '4': [3, [ 0xA0, 0xA0, 0xE0, 0x20, 0x20 ] ],
   '5': [3, [ 0xE0, 0x80, 0xC0, 0x20, 0xC0 ] ],
   '6': [3, [ 0x60, 0x80, 0xE0, 0xA0, 0xE0 ] ],
   '7': [3, [ 0xE0, 0x20, 0x20, 0x40, 0x40 ] ],
   '8': [3, [ 0xE0, 0xA0, 0xE0, 0xA0, 0xE0 ] ],
   '9': [3, [ 0xE0, 0xA0, 0xE0, 0x20, 0xC0 ] ],
   #':': [2, [ 0xC0, 0xC0, 0x00, 0xC0, 0xC0 ] ],
   ':': [1, [ 0x00, 0x80, 0x00, 0x80, 0x00 ] ],
   ';': [2, [ 0xC0, 0xC0, 0x00, 0x40, 0xC0 ] ],
   '<': [3, [ 0x20, 0x40, 0x80, 0x40, 0x20 ] ],
   '=': [3, [ 0x00, 0xE0, 0x00, 0xE0, 0x00 ] ],
   '>': [3, [ 0x80, 0x40, 0x20, 0x40, 0x80 ] ],
   '?': [3, [ 0xE0, 0x20, 0x60, 0x00, 0x40 ] ],
   '@': [3, [ 0x60, 0xA0, 0xC0, 0x80, 0x60 ] ],
   'A': [3, [ 0xE0, 0xA0, 0xE0, 0xA0, 0xA0 ] ],
   'B': [3, [ 0xE0, 0xA0, 0xC0, 0xA0, 0xE0 ] ],
   'C': [3, [ 0xE0, 0x80, 0x80, 0x80, 0xE0 ] ],
   'D': [3, [ 0xC0, 0xA0, 0xA0, 0xA0, 0xC0 ] ],
   'E': [3, [ 0xE0, 0x80, 0xE0, 0x80, 0xE0 ] ],
   'F': [3, [ 0xE0, 0x80, 0xE0, 0x80, 0x80 ] ],
   'G': [3, [ 0xE0, 0x80, 0xA0, 0xA0, 0xE0 ] ],
   'H': [3, [ 0xA0, 0xA0, 0xE0, 0xA0, 0xA0 ] ],
   'I': [3, [ 0xE0, 0x40, 0x40, 0x40, 0xE0 ] ],
   'J': [3, [ 0x20, 0x20, 0x20, 0xA0, 0xE0 ] ],
   'K': [3, [ 0xA0, 0xA0, 0xC0, 0xA0, 0xA0 ] ],
   'L': [3, [ 0x80, 0x80, 0x80, 0x80, 0xE0 ] ],
   'M': [3, [ 0xA0, 0xE0, 0xA0, 0xA0, 0xA0 ] ],
   'N': [3, [ 0xE0, 0xA0, 0xA0, 0xA0, 0xA0 ] ],
   'O': [3, [ 0xE0, 0xA0, 0xA0, 0xA0, 0xE0 ] ],
   'P': [3, [ 0xE0, 0xA0, 0xE0, 0x80, 0x80 ] ],
   'Q': [3, [ 0xE0, 0xA0, 0xA0, 0xC0, 0x60 ] ],
   'R': [3, [ 0xE0, 0xA0, 0xC0, 0xA0, 0xA0 ] ],
   'S': [3, [ 0xE0, 0x80, 0xE0, 0x20, 0xE0 ] ],
   'T': [3, [ 0xE0, 0x40, 0x40, 0x40, 0x40 ] ],
   'U': [3, [ 0xA0, 0xA0, 0xA0, 0xA0, 0xE0 ] ],
   'V': [3, [ 0xA0, 0xA0, 0xA0, 0xA0, 0x40 ] ],
   'W': [3, [ 0xA0, 0xA0, 0xA0, 0xE0, 0xA0 ] ],
   'X': [3, [ 0xA0, 0xE0, 0x40, 0xE0, 0xA0 ] ],
   'Y': [3, [ 0xA0, 0xA0, 0xE0, 0x40, 0x40 ] ],
   'Z': [3, [ 0xE0, 0x20, 0x40, 0x80, 0xE0 ] ],
   '[': [3, [ 0x60, 0x40, 0x40, 0x40, 0x60 ] ],
   '\\': [3, [ 0x80, 0x80, 0x40, 0x40, 0x20 ] ],
   ']': [3, [ 0xC0, 0x40, 0x40, 0x40, 0xC0 ] ],
   '^': [3, [ 0x40, 0xA0, 0x00, 0x00, 0x00 ] ],
   '_': [3, [ 0x00, 0x00, 0x00, 0x00, 0xE0 ] ],
   '`': [2, [ 0x40, 0x60, 0x00, 0x00, 0x00 ] ],
   'a': [3, [ 0x00, 0xE0, 0x60, 0xA0, 0xE0 ] ],
   'b': [3, [ 0x80, 0xE0, 0xA0, 0xA0, 0xE0 ] ],
   'c': [3, [ 0x00, 0xE0, 0x80, 0x80, 0xE0 ] ],
   'd': [3, [ 0x20, 0xE0, 0xA0, 0xA0, 0xE0 ] ],
   'e': [3, [ 0x00, 0xE0, 0xA0, 0xC0, 0xE0 ] ],
   'f': [3, [ 0x60, 0x80, 0xC0, 0x80, 0x80 ] ],
   'g': [3, [ 0x00, 0xE0, 0xA0, 0x60, 0xE0 ] ],
   'h': [3, [ 0x80, 0xE0, 0xA0, 0xA0, 0xA0 ] ],
   #'i': [2, [ 0x00, 0x40, 0x40, 0x40, 0x40 ] ],
   'i': [1, [ 0x80, 0x00, 0x80, 0x80, 0x80 ] ],
   #'i': [1, [ 0x00, 0x80, 0x80, 0x80, 0x80 ] ],
   #'j': [3, [ 0x00, 0x20, 0x20, 0xA0, 0xE0 ] ],
   'j': [3, [ 0x20, 0x00, 0x20, 0xA0, 0xE0 ] ],
   'k': [3, [ 0x80, 0xA0, 0xC0, 0xC0, 0xA0 ] ],
   #'l': [3, [ 0xC0, 0x40, 0x40, 0x40, 0x40 ] ],
   'l': [2, [ 0xC0, 0x40, 0x40, 0x40, 0x40 ] ],
   'm': [3, [ 0x00, 0xA0, 0xE0, 0xA0, 0xA0 ] ],
   'n': [3, [ 0x00, 0xE0, 0xA0, 0xA0, 0xA0 ] ],
   'o': [3, [ 0x00, 0xE0, 0xA0, 0xA0, 0xE0 ] ],
   'p': [3, [ 0x00, 0xE0, 0xA0, 0xE0, 0x80 ] ],
   'q': [3, [ 0x00, 0xE0, 0xA0, 0xE0, 0x20 ] ],
   'r': [3, [ 0x00, 0xE0, 0xA0, 0x80, 0x80 ] ],
   's': [3, [ 0x00, 0xE0, 0xC0, 0x60, 0xE0 ] ],
   't': [3, [ 0x40, 0xE0, 0x40, 0x40, 0x60 ] ],
   'u': [3, [ 0x00, 0xA0, 0xA0, 0xA0, 0xE0 ] ],
   'v': [3, [ 0x00, 0xA0, 0xA0, 0xA0, 0x40 ] ],
   'w': [3, [ 0x00, 0xA0, 0xA0, 0xE0, 0xA0 ] ],
   'x': [3, [ 0x00, 0xA0, 0x40, 0x40, 0xA0 ] ],
   'y': [3, [ 0x00, 0xA0, 0xA0, 0x60, 0xC0 ] ],
   'z': [3, [ 0x00, 0xE0, 0x60, 0xC0, 0xE0 ] ],
   '{': [3, [ 0x60, 0x40, 0xC0, 0x40, 0x60 ] ],
   #'|': [2, [ 0x40, 0x40, 0x40, 0x40, 0x40 ] ],
   '|': [1, [ 0x80, 0x80, 0x80, 0x80, 0x80 ] ],
   '}': [3, [ 0xC0, 0x40, 0x60, 0x40, 0xC0 ] ],
   '~': [3, [ 0x00, 0xC0, 0x60, 0x00, 0x00 ] ],
}

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
   s.connect((display, 23))
except:
    print("no connection...", end= '\r')
    time.sleep(10)
    sys.exit(1)


locLat= '52.212'
locLong= '5.287'

obs= ephem.Observer()  
obs.lat= locLat  
obs.long= locLong  

if ephem.Sun(obs).alt > 0.06:
    scaling= 2
else:
    scaling= 10


def scale(a):
    return [ int(round(a[0]/scaling)), int(round(a[1]/scaling)), int(round(a[2]/scaling)) ]

def bmWidth(str):
    len= 0
    for c in str:
        len= len + bm[c][0] + 1
    return len

def addChar(b, pos, w, c, fg, bg):
    base= 12 + 3*pos
    bt= bm[c][1]
    width= bm[c][0]
    for li in range(0,5):
        o= base + 3*li*w
        l= bt[li]
        for cl in range(0,width+1) :
            oc= o+3*cl
            if l & 0x80 :
                b[oc]= fg[0]
                b[oc+1]= fg[1]
                b[oc+2]= fg[2]
            else :
                b[oc]= bg[0]
                b[oc+1]= bg[1]
                b[oc+2]= bg[2]
            l= (l << 1) & 0xFF

#msg= ''
#for c in bm :
#    msg= msg + c
#print(msg)

width= bmWidth(msg)
b= bytearray(5 * 3*width + 12)

for idx,c in enumerate("!matrix ") :
    b[idx]= ord(c)

# speed
b[8]= speed

# background
b[9]= int(bgc[0]/scaling)
b[10]= int(bgc[1]/scaling)
b[11]= int(bgc[2]/scaling)

pos= 0
for c in msg:
    addChar(b, pos, width, c, scale(fgc), scale(bgc) )
    pos= pos + bm[c][0] + 1

#print(b)

s.send(b)

if count > 0:
    while True:
        line= s.recv(1024)
        if int(str(line[0])) == 48+count:
            break

#print(s.recv(1024))
