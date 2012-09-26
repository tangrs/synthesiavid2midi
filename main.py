import sys, time
from cv import *
from MidiFile import MIDIFile
from KeyboardScanner import *

if (len(sys.argv) < 3):
    print "Not enough arguments"
    print "main.py [overrides/options in key:value format] output input"
    print "Supported overrides: whitewidth, blackwidth, nkeys, middlec, keyboardgrayscalethreshold, whitethreshold, blackthreshold"
    print "Other options: showprogress, midivelocity"
    quit()

overrides = {}
showProgress = False
midiVelocity = 64
for override in sys.argv[1:-2]:
    p = override.split(":")
    if (p[0] == "showprogress"): showProgress = True
    elif (p[0] == "midivelocity"): midiVelocity = int(p[1])
    else: overrides[p[0]] = p[1]

if (showProgress):
    NamedWindow("Main")
    ResizeWindow("Main", 640, 480)

cap = CaptureFromFile(sys.argv[len(sys.argv)-1])
scanner = KeyboardScanner(QueryFrame(cap), overrides)
midi = MIDIFile(1)

midi.addTrackName(0,0,"Transcribed from Synthesia")
midi.addTempo(0,0,120.0)

noteDeltas = {}
while True:
    t = GetCaptureProperty(cap, CV_CAP_PROP_POS_MSEC) / 500.0
    print t, "\r",
    frame = QueryFrame(cap)
    if (frame == None): break
    changes = scanner.scanFrame(frame)
    if (showProgress):
        ShowImage("Main", scanner.debugImage)
        WaitKey(1)
    for pitch in changes:
        if (scanner.currentState[pitch]):
            # Changed to on
            noteDeltas[pitch] = t
        else:
            # Changed to off
            midi.addNote(0, 0, pitch, noteDeltas[pitch], t-noteDeltas[pitch], midiVelocity)

binfile = open(sys.argv[len(sys.argv)-2], 'wb')
midi.writeFile(binfile)
binfile.close()