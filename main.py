import sys, time
from cv import *
from keyboardBounds import *


NamedWindow("Main")
ResizeWindow("Main", 640, 480)

cap = CaptureFromFile(sys.argv[1])
scanner = KeyboardScanner(QueryFrame(cap))
ShowImage("Main", scanner.debugImage)
#while True:
#    WaitKey(100)

while True:
    frame = QueryFrame(cap)
    ShowImage("Main", scanner.scanFrame(frame))
    WaitKey(1000/25)

#WaitKey()