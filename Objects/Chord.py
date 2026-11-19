from Objects.Note import Note

# TODO set rest based on pitch instead?
class Chord:
    def __init__(self, pitch, length, y):
        self.y = y
        self.length = length
        self.notes = [Note(pitch)]
        self.staccato = False
        self.accent = False

        if pitch == -1:
            self.rest = True
        else:
            self.rest = False

        self.tie = False

    def addNote(self, pitch : int) -> Note:
        if self.rest:
            self.notes = []
            self.rest = False

        newNote = Note(pitch)
        self.notes.append(newNote)
        self.notes = sorted(self.notes, key = lambda x: x.pitch)

        return newNote

    def remove_note(self, note : Note) -> Note:
        if self.rest:
            return

        index = self.notes.index(note)
        self.notes.pop(index)

        if len(self.notes) == 0:
            self.rest = True
            self.notes.append(Note(-1))
            return self.notes[0]

        return self.notes[index - 1 if index > 0 else 0]

    def toggleStaccato(self) -> None:
        self.staccato = not self.staccato

    def toggleAccent(self) -> None:
        self.accent = not self.accent

    def replaceChord(self, pitch : int) -> Note:
        self.notes = [Note(pitch)]
        self.staccato = False
        self.accent = False

        return self.notes[0]

    def getOtherNote(self, note : Note, change : int) -> Note:
        """Get the next note in a chord in the given direction"""

        current_index = self.notes.index(note)
        new_index = current_index + change

        if len(self.notes) > new_index and new_index >= 0:
            return self.notes[new_index]

        return None

    def shiftChord(self, change):
        self.y += change

    def duplicateChord(self):
        new_chord : Chord = Chord(-1, self.length, self.y)
        new_chord.notes = []

        for note in self.notes:
            new_chord.addNote(note.pitch)

        new_chord.staccato = self.staccato
        new_chord.accent = self.accent
        new_chord.rest = self.rest

        return new_chord