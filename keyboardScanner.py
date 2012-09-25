from cv import *

class ScannerException(Exception): pass
class BoundsSearchFail(ScannerException): pass
class KeySearchFail(ScannerException): pass

class KeyboardScanner:
    debugImage = None
    keyNoteLabels = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    keyNoteHasSharp = [True, True, False, True, True, True, False]
    keyNoteWhites = len(keyNoteLabels)
    noteMidiC4 = 60
    nKeys = None
    middleC = None
    currentState = {}

    def __init__(self, frame, overrides = {}):
        filteredFrame = CreateImage(GetSize(frame), IPL_DEPTH_8U, 1)
        CvtColor(frame, filteredFrame, CV_RGB2GRAY)
        if ("keyboardgrayscalethreshold" in overrides.keys()): videoThreshold = float(overrides["keyboardgrayscalethreshold"])
        else: videoThreshold = 192
        Threshold(filteredFrame, filteredFrame, videoThreshold, 255, CV_THRESH_BINARY)

        self.keyboardBounds = self.getKeyboardBounds(filteredFrame)
        filteredFrame = self.cutFrame(filteredFrame)
        self.debugImage = filteredFrame
        rawFrame = self.cutFrame(frame)

        self.keyBounds = self.getKeySize(filteredFrame)
        if ("whitewidth" in overrides.keys()):
            ww,bw = self.keyBounds
            self.keyBounds = int(overrides["whitewidth"]), bw
        if ("blackwidth" in overrides.keys()):
            ww,bw = self.keyBounds
            self.keyBounds = ww, int(overrides["blackwidth"])

        # bruteforce to get optimal threshold
        # keep trying until we have a middle c
        done = False
        for i in xrange(250, 230, -1):
            for scale in xrange(86, 80, -1):
                try:
                    self.nKeys, self.middleC = self.getKeys(rawFrame, i, scale/100.0)
                    done = True
                    break
                except KeySearchFail:
                    pass
            if (done): break
        if (not done): raise KeySearchFail()

        if ("nkeys" in overrides.keys()): self.nKeys = int(overrides["nkeys"])
        if ("middlec" in overrides.keys()): self.middleC = int(overrides["middlec"])

        self.keyMappings = self.buildMapping()
        for (note, x, y, sharp, pitch) in self.keyMappings:
            self.currentState[pitch] = False



    def buildMapping(self):
        # We pivot everything on middle C which brings a lot of pain.
        # There will be a formular but I can't be bothered working it out.
        _,_,kWidth,kHeight = self.keyboardBounds
        wKeyWidth,bKeyWidth = self.keyBounds
        betweenKeyLen = float(kWidth)/float(self.nKeys)

        keyMappings = []
        index = (self.keyNoteWhites - (self.middleC % self.keyNoteWhites)) % self.keyNoteWhites
        pitch = -1
        # Fill everything before middle C with -1 as midi note
        for k in xrange(0, self.nKeys):
            xPos = int((wKeyWidth/2.0) + (betweenKeyLen*k))
            yPos = int(0.73 * kHeight)
            # (note name, x, y, is sharp, midi pitch)
            if (k == self.middleC): pitch = self.noteMidiC4
            elif (k > self.middleC): pitch += 1
            key = self.keyNoteLabels[index], xPos, yPos, False, pitch
            keyMappings.append(key)
            if (self.keyNoteHasSharp[index]):
                if (k >= self.middleC): pitch += 1
                xPos = int((betweenKeyLen*(k+1))) + 1
                if (xPos < kWidth):
                    yPos = int(0.5 * kHeight)
                    key = self.keyNoteLabels[index]+"#", xPos, yPos, True, pitch
                    keyMappings.append(key)
            index = (index+1) % self.keyNoteWhites

        # Go back and fill them in properly
        _,_,_,_,pitch = keyMappings[-1]
        for k,v in enumerate(keyMappings[::-1]):
            note,x,y,sharp,_ = v
            keyMappings[k] = note,x,y,sharp,pitch
            pitch -= 1

        return keyMappings

    def cutFrame(self,frame):
        x,y,w,h = self.keyboardBounds
        subframe = CreateImage((w,h), frame.depth, frame.nChannels)
        SetImageROI(frame, self.keyboardBounds)
        Copy(frame, subframe)
        ResetImageROI(frame)
        return subframe

    def getKeys(self,frame,videoThreshold = 240,dotscale = 0.82):
        # Find the height of the middle C dot
        filteredFrame = CreateImage(GetSize(frame), IPL_DEPTH_8U, 1)
        CvtColor(frame, filteredFrame, CV_RGB2GRAY)
        Threshold(filteredFrame, filteredFrame, videoThreshold, 255, CV_THRESH_BINARY)
        frame = filteredFrame
        self.debugImage = frame

        _,_,w,h = self.keyboardBounds
        y = int(dotscale * h)
        ww, bw = self.keyBounds

        last,_,_,_ = Get2D(frame, y, 0)
        len = 0
        keys = 0
        middleC = -1
        for x in xrange(1, w):
            p,_,_,_ = Get2D(frame, y, x)
            if (last != p):
                if (last == 0.0):
                    if (len > ww/2):
                        middleC = keys-1
                    else:
                        keys+=1
                len=0
            else:
                len+=1
            last = p
        if (keys == 0 or middleC == -1): raise KeySearchFail()
        return (keys, middleC)

    def getKeySize(self, frame):
        _,_,w,h = self.keyboardBounds
        wlen = -1
        blen = -1

        last,_,_,_ = Get2D(frame, h-1, 0)
        len = 0
        for x in xrange(1, w):
            p,_,_,_ = Get2D(frame, h-1, x)
            if (last != p):
                if (len > wlen and last == 255.0):
                    wlen = len
                len = 0
            else:
                len+=1
            last = p

        last,_,_,_ = Get2D(frame, h/2, 0)
        len = 0
        for x in xrange(1, w):
            p,_,_,_ = Get2D(frame, h/2, x)
            if (last != p):
                if (len > blen and last == 0.0):
                    blen = len
                len = 0
            else:
                len+=1
            last = p

        if (blen == -1 or wlen == -1): raise BoundsSearchFail();
        return (wlen, blen)

    def getKeyboardBounds(self,frame):
        lower = -1
        upper = -1
        for y in xrange(frame.height-1, 0, -1):
            p,_,_,_ = Get2D(frame, y, 0)
            if (p != 0.0):
                lower = y
                break
        if (lower == -1): raise BoundsSearchFail();
        for y in xrange(y-1, 0, -1):
            p,_,_,_ = Get2D(frame, y, 0)
            if (p != 255.0):
                upper = y
                break
        if (upper == -1): raise BoundsSearchFail();
        # Returns CvRect (x, y, width, height)
        return (0, upper, frame.width, lower-upper)

    def scanFrame(self, frame):
        frame = self.cutFrame(frame)
        changes = []
        for (note, x, y, sharp, pitch) in self.keyMappings:
            b,g,r,_ = Get2D(frame, y, x)
            pixel = (0.299*r + 0.587*g + 0.114*b)
            if (sharp):
                if (pixel < 28.0):
                    # Not pressed
                    state = False
                    color = (255.0,255.0,255.0,255.0)
                else:
                    state = True
                    color = (0.0,255.0,0.0,255.0)
            else:
                if (pixel > 240.0):
                    # Not pressed
                    state = False
                    color = (0.0,0.0,0.0,255.0)
                else:
                    state = True
                    color = (0.0,255.0,0.0,255.0)
            if (self.currentState[pitch] != state): changes.append(pitch)
            self.currentState[pitch] = state
            Circle(frame, (x,y), 4, color)
        self.debugImage = frame
        return changes
