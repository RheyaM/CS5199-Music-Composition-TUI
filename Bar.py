from Beat import Beat
from Chord import Chord
class Bar:
    def __init__(self, y, beats):
        # y coord of start of bar
        self.y = y

        self.endy = y + 26

        # list of Beat objects in the bar
        self.beats = []
        current_y = y + 4
        for i in range(beats):
            self.beats.append(Beat(current_y))
            current_y = current_y + 6

        # x, y = top left corner of Bar
        self.pad = 0

    def shiftBar(self, change):
        self.y += change
        self.endy += change
        
        for beat in self.beats:
            beat.shiftBeat(change)


    def getNextBeat(self, beat):
        index = self.beats.index(beat)

        if index < len(self.beats) - 1:
            return self.beats[index + 1]
        else:
            return None

    # Get the next chord, regardless of which beat it is in
    # If a beat is empty, skips it
    # TODO: refactor getNext and getPrev into one/smaller functions?
    def getNextChord(self, beat, chord):

        # If there's another chord in the bar
        withinBeat = self.beats[beat].getNextChord(chord)

        if withinBeat:
            return [beat, withinBeat]

        # Look for the next beat
        else:
            temp = beat + 1
            while temp <= len(self.beats) - 1:
                if len(self.beats[temp].chords) > 0:
                    return [temp, self.beats[temp].chords[0]]
                temp += 1

        # None implies there are no more beats in the bar, hence no more chords
        return [beat, None]

    def getPrevChord(self, beat, chord):

        withinBeat = self.beats[beat].getPrevChord(chord)

        if withinBeat:
            return [beat, withinBeat]

        # Was no previous chord in the current beat
        else:
            temp = beat - 1
            while temp >= 0:
                if len(self.beats[temp].chords) > 0:
                    return [temp, self.beats[temp].chords[-1]]
                temp -= 1

        # None implies there are no previous beats/chords in the bar
        return [beat, None]

    def redoY(self):

        # Can only control the y of current chord
        # So add to y based on current chord, then beginning of next loop make that the chords y

        beat = 0
        chord = self.beats[0].chords[0]

        y = self.y + 4

        while chord:
            chord.y = y

            if chord.length == 4:
                chord.y += 5
                y += 11
            elif chord.length == 3:
                chord.y += 3
                y = chord.y + 7
            elif chord.length == 2:
                y += 7

            elif chord.length == 1:
                y += 6

            elif chord.length < 1:
                y += 4

            [beat, chord] = self.getNextChord(beat, chord)

    
        self.endy = y

        return self.endy

    def emptyBar(self):
        for beat in self.beats:
            beat.chords = []
            beat.empty = True

        

            
                
            
    