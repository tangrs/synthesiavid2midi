#     synthesiavid2midi
#     Copyright (C) 2012  Daniel Tang
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

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