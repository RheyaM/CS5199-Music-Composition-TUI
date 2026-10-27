from Objects.Chord import Chord

class Beat:
    def __init__(self, y):
        self.chords = [Chord(-1, 1, y, True)]
        self.y = y
        self.empty = False

    def addChord(self, index, chord):
        
        if index < len(self.chords) and index >= 0:
            self.chords[index] = chord
        else:
            self.chords.append(chord)

        self.empty = False

    def getChordIndex(self, chord):
        if chord in self.chords:
            return self.chords.index(chord)

        return None


    # Replace a chord with a rest of the same length
    def removeChord(self, chord):
        index = self.getChordIndex(chord)
        newChord = Chord(-1, chord.length, chord.y, True)
        self.chords[index] = newChord

        return newChord

    # Fully delete a chord (in service of doubling note length)
    def deleteChord(self, chord):
        self.chords.remove(chord)
        if len(self.chords) == 0:
            self.empty = True


    def getPrevChord(self, chord):
        if chord:
            index = self.getChordIndex(chord)
            if index > 0:
                return self.chords[index - 1]
        # No previous chord or current chord
        return None

    # returns None if there is no next chord
    def getNextChord(self, chord):
        if chord:
            index = self.getChordIndex(chord)
            if index < len(self.chords) - 1:
                return self.chords[index + 1]
        return None

    def LastChord(self):
        if self.empty:
            return None
        return self.chords[-1]

    def restBeat(self):
        if (len(self.chords) == 1 and self.chords[0].notes[0].pitch == -1):
            return True
        return False

    # TODO
    def shiftBeat(self, change):
        self.y += change
        for chord in self.chords:
            chord.y += change

    def halfChord(self, chord):

        # MuseScore does it so that if u half a chord, it duplicates itself for the new half
        # Weird??
        
        index = self.getChordIndex(chord)
        newLength = chord.length

        if chord.length == 2 or chord.length == 3:
            newLength = 1

        newChord = Chord(-1, newLength, chord.y + 4, True)
        self.chords.insert(index + 1, newChord)

        return newChord


    def totalLength(self):
        return sum(chord.length for chord in self.chords)


    # Because of the doubling of a chord, determine how much overflow exists in a beat
    def determineOverflow(self, chord):
        total = self.totalLength()

        if total == 1:
            return None

        else: 
            overflow = total - 1
            overflowChords = []

            current_index = len(self.chords) - 1
            while overflow > 0:
                current_chord = self.chords[current_index]
                if current_chord.length <= overflow:
                    overflowChords.insert(0, current_chord)
                    overflow -= current_chord.length

                if current_chord.length > overflow:
                    newChord = current_chord.duplicateChord()
                    newChord.length = overflow

                    overflowChords.insert(0, newChord)
                    overflow = 0

                    current_chord.length -= overflow

            return overflowChords

            # TODO: y's of overflow chords must be updated




