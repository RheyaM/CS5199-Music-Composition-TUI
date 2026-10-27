from Objects.Note import Note

# TODO set rest based on pitch instead?
class Chord:
    def __init__(self, pitch, length, y, rest=False):
        self.y = y
        self.length = length
        self.notes = [Note(pitch)]
        self.staccato = False
        self.accent = False
        self.rest = rest

    def addNote(self, pitch):
        if self.rest:
            self.notes = []
            self.rest = False

        newNote = Note(pitch)
        self.notes.append(newNote)
        self.notes = sorted(self.notes, key = lambda x: x.pitch)

        return newNote

    def removeNote(self, note):
        if self.rest:
            return

        index = self.notes.index(note)
        self.notes.pop(index)

        if len(self.notes) == 0:
            self.rest = True
            self.notes.append(Note(-1))
            return self.notes[0]

        return self.notes[index - 1 if index > 0 else 0]

    def toggleStaccato(self):
        self.staccato = not self.staccato

    def toggleAccent(self):
        self.accent = not self.accent

    def replaceChord(self, pitch):
        self.notes = [Note(pitch)]
        self.staccato = False
        self.accent = False

        return self.notes[0]

    def getOtherNote(self, note, change):
        current_index = self.notes.index(note)
        new_index = current_index + change

        if len(self.notes) > new_index and new_index >= 0:
            return self.notes[new_index]

        return None

    def shiftChord(self, change):
        self.y += change

    def duplicateChord(self):
        newChord = Chord(-1, self.length, self.y)
        newChord.notes = []

        for note in self.notes:
            newChord.addNote(note.pitch)

        newChord.staccato = self.staccato
        newChord.accent = self.accent

        return newChord

    # TODO: refactor? 
    def ignoreChord(self):
        if len(self.notes) == 1 and self.notes[0].pitch == -2:
            return True
        return False