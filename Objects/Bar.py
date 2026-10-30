from Objects.Beat import Beat
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

        self.pad = 0

    def shiftBar(self, change):
        self.y += change
        self.endy += change
        
        for beat in self.beats:
            beat.shiftBeat(change)

    # Takes a Beat object and returns the next one in the Bar
    # Returns the Beat object regardless of if its empty
    def getNextBeat(self, beat):
        index = self.beats.index(beat)

        if index < len(self.beats) - 1:
            return self.beats[index + 1]
        else:
            return None

    # Get the next chord, regardless of which beat it is in
    # Skips empty beats
    def getNextChord(self, beat : int, chord):

        # get the next chord in the current beat
        withinBeat = self.beats[beat].getNextChord(chord)

        # If there was another chord in the current beat
        if withinBeat:
            return [beat, withinBeat]

        # Else, look at the next beat
        else:
            temp = beat + 1
            while temp <= len(self.beats) - 1:
                if not self.beats[temp].empty:
                    return [temp, self.beats[temp].chords[0]]
                temp += 1

        # None implies there are no more beats in the bar, hence no more chords
        return [beat, None]

    # Get the previous chord, regardless of which beat it's in
    # Skips empty beats
    def getPrevChord(self, beat : int, chord):

        withinBeat = self.beats[beat].getPrevChord(chord)

        if withinBeat:
            return [beat, withinBeat]

        # Was no previous chord in the current beat
        else:
            temp = beat - 1
            while temp >= 0:
                if not self.beats[temp].empty:
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

    # Returns the beat index and chord object of the last chord in the Bar
    def getLastChord(self):
        index = len(self.beats) - 1
        while self.beats[index].empty:
            index -= 1

        return [index, self.beats[index].chords[-1]]


            
                
            
    