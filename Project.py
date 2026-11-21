from Objects.Bar import Bar
from Objects.Chord import Chord

class Project:
    """Project class containing a project, its score, and its characteristics"""
    def __init__(self):
        self.beats = 4
        self.score = [Bar(15, self.beats), Bar(41, self.beats)]
        self.key = "C Major"
        self.bpm = 120

        # self.current_bar = None
        # self.current_chord = None
        # self.current_note = None
        # self.reset_currents()


    def get_current_coords(self):
        """Get the coordinates of the currently selected note"""

        y = self.current_chord.y
        x = self.current_note.pitch
        return [x, y]

    def get_pad_index(self, bar_index):
        """Return the pad of the current bar"""
        return self.score[bar_index].pad

    def create_new_bar(self):
        """Create a new, empty bar"""
        new_y = self.score[-1].endy
        self.score.append(Bar(new_y, self.beats))

        return self.score[-1]

    def reset_currents(self):
        """Reset the current note to the first note of the first bar"""
        self.current_bar = 0
        self.current_chord = self.score[self.current_bar].chords[0]
        self.current_note = self.current_chord.notes[0]

    def toggle_attributes(self, attr):
        """Adjust the attributes of the current chord or note, given attr"""
        match attr:
            case "sharp" | "flat" | "natural":
                self.current_note.toggle_attribute(attr)
            case "accent":
                self.current_chord.toggle_accent()
            case "staccato":
                self.current_chord.toggle_staccato()

    def set_all_currents(self, bar : int, chord_index : int, note_index : int):
        """Set the current bar, chord and note"""
        self.current_bar = bar
        self.current_chord = self.score[self.current_bar].chords[chord_index]
        self.current_note = self.current_chord[note_index]

    def get_bar(self, bar_index) -> Bar:
        """Return the current bar object"""
        return self.score[bar_index]

    def move_left(self, bar_index : int, chord : Chord) -> list[int, Chord]:
        """Given a bar and chord, return the previous chord, regardless of which bar it's in"""
        # Check the current Bar
        prev_chord = self.score[bar_index].get_prev_chord(chord)

        if prev_chord:
            return [bar_index, prev_chord]

        # Is there a previous Bar?
        if bar_index > 0:
            prev_chord = self.score[bar_index - 1].get_last_chord()
            return [bar_index - 1, prev_chord]

        # If not, return None
        return [None, None]

    def move_right(self, bar_index : int, chord : Chord) -> list[int, Chord]:
        """Given a bar and chord, return the next chord along, regardless of which bar it's in"""

        # Check the current Bar
        next_chord = self.score[bar_index].get_next_chord(chord)

        if next_chord:
            return [bar_index, next_chord]

        # Is there a next Bar? Then return the first chord of that Bar
        if bar_index < len(self.score) - 1:
            return [bar_index + 1, self.score[bar_index + 1].chords[0]]

        # If not, return None
        return [None, None]
