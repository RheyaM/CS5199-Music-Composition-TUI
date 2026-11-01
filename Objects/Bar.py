from Objects.Beat import Beat
from Objects.Chord import Chord
class Bar:
    def __init__(self, y, beats):
        # y coord of start of bar
        self.y = y

        self.endy = y + 26

        # list of Chord objects in the bar
        self.chords = []
        current_y = y + 4
        for i in range(beats):
            self.chords.append(Chord(-1, 1, current_y, True))
            current_y = current_y + 6

        self.pad = 0

    def shiftBar(self, change):
        self.y += change
        self.endy += change
        
        for chord in self.chords:
            chord.shiftChord(change)

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
    def getNextChord(self, chord):

        index = self.chords.index(chord)
        if index >= len(self.chords) - 1:
            return None

        return self.chords[index + 1]


    # Get the previous chord
    def getPrevChord(self, chord):

        index = self.chords.index(chord)

        if index > 0:
            return self.chords[index - 1]

        return None

    def redoY(self):

        # Can only control the y of current chord
        # So add to y based on current chord, then beginning of next loop make that the chords y

        chord = self.chords[0]

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

            chord = self.getNextChord(chord)

        self.endy = y

        return self.endy

    def emptyBar(self):
        self.chords = []

    # Returns the beat index and chord object of the last chord in the Bar
    def getLastChord(self):
        return self.chords[-1]

    def halfChord(self, chord):
        index = self.chords.index(chord)

        if chord.length == 4 or chord.length == 3:
            chord.length -= 1
        else:
            chord.length /= 2

        newLength = chord.length
        
        if chord.length == 2 or chord.length == 3:
            newLength = 1

        newChord = Chord(-1, newLength, chord.y + 4, True)
        self.chords.insert(index + 1, newChord)

        return newChord


            
                
            
    