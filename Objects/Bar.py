from Objects.Chord import Chord
class Bar:
    """Class for Bar objects"""
    def __init__(self, y, beats):
        # y coord of start of bar
        self.y = y

        self.endy = y + 2 + (6 * beats)

        # list of Chord objects in the bar
        self.chords = []
        current_y = y + 4
        for _ in range(beats):
            self.chords.append(Chord(-1, 1, current_y))
            current_y = current_y + 6

        self.pad = 0

    def shift_bar(self, change):
        """Shift the y-coordinates of the entire bar"""

        self.y += change
        self.endy += change

        for chord in self.chords:
            chord.shift_chord(change)

    def get_next_chord(self, chord : Chord) -> Chord:
        """Get the next chord within the current bar"""

        index = self.chords.index(chord)
        if index >= len(self.chords) - 1:
            return None

        return self.chords[index + 1]

    def get_prev_chord(self, chord):
        """Get the previous chord"""

        index = self.chords.index(chord)

        if index > 0:
            return self.chords[index - 1]

        return None

    def redo_y(self):
        """Readjust y-coordinates of all chords in the bar"""

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
                y += 5

            chord = self.get_next_chord(chord)

        self.endy = y - 2

        return self.endy

    def empty_bar(self) -> None:
        """Remove all chords from the bar"""
        self.chords = []

    def get_last_chord(self) -> Chord:
        """Returns the beat index and chord object of the last chord in the Bar"""
        return self.chords[-1]

    def half_chord(self, chord) -> Chord:
        """Halve the length of the given chord"""
        index = self.chords.index(chord)

        if chord.length == 4 or chord.length == 3:
            chord.length -= 1
        else:
            chord.length /= 2

        new_length = chord.length

        if chord.length == 2 or chord.length == 3:
            new_length = 1

        new_chord = Chord(-1, new_length, chord.y + 5)
        self.chords.insert(index + 1, new_chord)

        return new_chord

    def total_length(self) -> float:
        """Calculate total length of all chords in the bar"""
        total : float = 0

        for chord in self.chords:
            total += chord.length

        return total
    