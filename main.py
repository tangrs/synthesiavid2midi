import sys, time
from cv import *
from MidiFile import MIDIFile
from KeyboardScanner import *


NamedWindow("Main")
ResizeWindow("Main", 640, 480)

cap = CaptureFromFile(sys.argv[1])
scanner = KeyboardScanner(QueryFrame(cap))
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
    ShowImage("Main", scanner.debugImage)
    for pitch in changes:
        if (scanner.currentState[pitch]):
            # Changed to on
            noteDeltas[pitch] = t
        else:
            # Changed to off
            midi.addNote(0, 0, pitch, noteDeltas[pitch], t-noteDeltas[pitch], 64)

binfile = open("output.mid", 'wb')
midi.writeFile(binfile)
binfile.close()