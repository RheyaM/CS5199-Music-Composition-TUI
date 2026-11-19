from Objects.Note import Note

class Chord:
    """Class for Chord objects"""
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

    def add_note(self, pitch : int) -> Note:
        """Add a note to the chord"""
        if self.rest:
            self.notes = []
            self.rest = False

        new_note = Note(pitch)
        self.notes.append(new_note)
        self.notes = sorted(self.notes, key = lambda x: x.pitch)

        return new_note

    def remove_note(self, note : Note) -> Note:
        """Remove a note from the chord"""
        if self.rest:
            return

        index = self.notes.index(note)
        self.notes.pop(index)

        if len(self.notes) == 0:
            self.rest = True
            self.notes.append(Note(-1))
            return self.notes[0]

        return self.notes[index - 1 if index > 0 else 0]

    def toggle_staccato(self) -> None:
        """Toggle boolean value of self.staccato"""
        self.staccato = not self.staccato

    def toggle_accent(self) -> None:
        """Toggle boolean value of self.accent"""
        self.accent = not self.accent

    def replace_chord(self, pitch : int) -> Note:
        """Replace the current chord with a single note"""
        self.notes = [Note(pitch)]
        self.staccato = False
        self.accent = False

        return self.notes[0]

    def get_other_note(self, note : Note, change : int) -> Note:
        """Get the next note in a chord in the given direction"""

        current_index = self.notes.index(note)
        new_index = current_index + change

        if len(self.notes) > new_index >= 0:
            return self.notes[new_index]

        return None

    def shift_chord(self, change):
        """Shift the y-coordinate of the chord"""
        self.y += change

    def duplicate_chord(self):
        """Return a copy of the chord"""
        new_chord : Chord = Chord(-1, self.length, self.y)
        new_chord.notes = []

        for note in self.notes:
            new_chord.add_note(note.pitch)

        new_chord.staccato = self.staccato
        new_chord.accent = self.accent
        new_chord.rest = self.rest

        return new_chord
    