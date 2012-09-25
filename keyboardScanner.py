from cv import *

class ScannerException(Exception): pass
class BoundsSearchFail(ScannerException): pass
class KeySearchFail(ScannerException): pass

class KeyboardScanner:
    debugImage = None
    keyNoteLabels = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    keyNoteHasSharp = [True, True, False, True, True, True, False]
    keyNoteWhites = len(keyNoteLabels)
    def __init__(self, frame, videoThreshold = 192):
        filteredFrame = CreateImage(GetSize(frame), IPL_DEPTH_8U, 1)
        CvtColor(frame, filteredFrame, CV_RGB2GRAY)
        Threshold(filteredFrame, filteredFrame, videoThreshold, 255, CV_THRESH_BINARY)

        self.keyboardBounds = self.getKeyboardBounds(filteredFrame)
        filteredFrame = self.cutFrame(filteredFrame)
        self.debugImage = filteredFrame
        rawFrame = self.cutFrame(frame)

        self.keyBounds = self.getKeySize(filteredFrame)

        # bruteforce to get optimal threshold
        # keep trying until we have a middle c
        for i in xrange(220, 250):
            try:
                self.nKeys, self.middleC = self.getKeys(rawFrame, i)
                break
            except KeySearchFail:
                pass
        if (self.nKeys == None or self.middleC == None): raise KeySearchFail()

        self.keyMappings = self.buildMapping()

    def buildMapping(self):
        _,_,kWidth,kHeight = self.keyboardBounds
        wKeyWidth,bKeyWidth = self.keyBounds
        betweenKeyLen = float(kWidth)/float(self.nKeys)

        keyMappings = []
        index = (self.keyNoteWhites - (self.middleC % self.keyNoteWhites)) % self.keyNoteWhites
        for k in xrange(0, self.nKeys):
            xPos = int((wKeyWidth/2.0) + (betweenKeyLen*k))
            yPos = int(0.73 * kHeight)
            # (note name, x, y, is sharp)
            key = self.keyNoteLabels[index], xPos, yPos, False
            keyMappings.append(key)
            if (self.keyNoteHasSharp[index]):
                xPos = int((betweenKeyLen*(k+1))) + 1
                if (xPos < kWidth):
                    yPos = int(0.5 * kHeight)
                    key = self.keyNoteLabels[index]+"#", xPos, yPos, True
                    keyMappings.append(key)
            index = (index+1) % self.keyNoteWhites
        return keyMappings


    def cutFrame(self,frame):
        x,y,w,h = self.keyboardBounds
        subframe = CreateImage((w,h), frame.depth, frame.nChannels)
        SetImageROI(frame, self.keyboardBounds)
        Copy(frame, subframe)
        ResetImageROI(frame)
        return subframe

    def getKeys(self,frame,videoThreshold = 240):
        # Find the height of the middle C dot
        filteredFrame = CreateImage(GetSize(frame), IPL_DEPTH_8U, 1)
        CvtColor(frame, filteredFrame, CV_RGB2GRAY)
        Threshold(filteredFrame, filteredFrame, videoThreshold, 255, CV_THRESH_BINARY)
        frame = filteredFrame

        _,_,w,h = self.keyboardBounds
        y = int(0.82 * h)
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
        for (note, x, y, sharp) in self.keyMappings:
            b,g,r,_ = Get2D(frame, y, x)
            pixel = (0.299*r + 0.587*g + 0.114*b)
            if (sharp):
                if (pixel < 28.0):
                    color = (255.0,255.0,255.0,255.0)
                else:
                    color = (0.0,255.0,0.0,255.0)
            else:
                if (pixel > 240.0):
                    color = (0.0,0.0,0.0,255.0)
                else:
                    color = (0.0,255.0,0.0,255.0)
            Circle(frame, (x,y), 4, color)
        return frame
