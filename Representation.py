"""Importing regex module"""
import re
from Objects.Bar import Bar
from Objects.Chord import Chord
from Objects.Note import Note
from Project import Project

class Representation:
    """Class for converting score to strings and vice versa"""

    MIDDLE_C : int = 9

    NOTE_DICT : dict = {"c": MIDDLE_C + 7, "d": MIDDLE_C + 6, "e": MIDDLE_C + 5, "f": MIDDLE_C + 4,
                        "g": MIDDLE_C + 3, "a": MIDDLE_C + 2, "b": MIDDLE_C + 1}
    pitch_dict = {v: k for k, v in NOTE_DICT.items()}

    current_length = 0

    @staticmethod
    def score_to_string(proj : Project):
        """Parsing the score list to a string"""

        score = proj.score
        beats = proj.beats
        string = "B:" + str(beats) + "."
        current_len = 0

        string += "|"

        for bar in score:
            for chord in bar.chords:

                notestr = ""

                for note in chord.notes:
                    notestr += Representation.pitch_to_note(note.pitch)

                    match note.attribute:
                        case "sharp":
                            notestr += "#"
                        case "flat":
                            notestr += "-"
                        case "natural":
                            notestr += "n"

                if len(chord.notes) > 1:
                    notestr = "<" + notestr + ">"

                if chord.length != current_len:
                    length_string = str(chord.length)

                    if chord.length < 1 and len(length_string) > 1:
                        notestr += length_string[1::]
                    else:
                        notestr += str(int(chord.length))
                    current_len = chord.length

                string += notestr

            string += "|"

        return string

    @staticmethod
    def pitch_to_note(pitch):
        """Convert the pitch to a letter note"""

        if pitch == -1:
            return "r"

        if pitch in Representation.pitch_dict.keys():
            return Representation.pitch_dict[pitch]

        direction = 0

        while pitch < Representation.MIDDLE_C + 1:
            pitch += 7
            direction += 1
            char = "'"

        while pitch > Representation.MIDDLE_C + 7:
            pitch -= 7
            direction += 1
            char = ","

        note = Representation.pitch_dict[pitch] + (char * direction)

        return note


    # TODO: maybe removing charrs as we go isn't the most efficient? space or timing wise?
    # Just need to iterate probably
    @staticmethod
    def string_to_score(string):
        """Parse the given string and create score list"""

        score = []

        index = string.index(".")

        beats = int(re.search("B:(\d)\.", string).group(1))

        notes = string[index + 1::]

        # While there are still bars to extract
        while len(notes) > 1:
            [bar, notes] = Representation.extract_bar(notes, beats)
            score.append(bar)

        return score

    @staticmethod
    def extract_bar(substring : str, beats):
        """Given a substring beginning with |, return the first bar extracted, 
        and the remaining substring containing the last |"""

        bar_notes = substring[1::]
        bar = Bar(0, beats)
        bar.empty_bar()

        while len(bar_notes) > 1:

            ch = bar_notes[0]

            if ch == "|":
                bar.redo_y()
                return [bar, bar_notes]

            if ch == "<":
                [chord, bar_notes] = Representation.extract_chord(bar_notes)
                Representation.current_length = chord.length

            elif ch in Representation.NOTE_DICT or ch == "r":
                [pitch, bar_notes] = Representation.get_chord_note(bar_notes)

                [attribute, bar_notes] = Representation.extract_note_attributes(bar_notes)

                # Determining the length of the note
                [length, bar_notes] = Representation.extract_length(bar_notes)

                if length is None:
                    length = Representation.current_length
                else:
                    Representation.current_length = length

                chord = Chord(pitch, length, 0)

                if attribute is not None:
                    chord.notes[0].toggle_attribute(attribute)

            bar.chords.append(chord)

        bar.redo_y()
        return [bar, bar_notes]

    # TODO: should default to current_length here rather than once None has been extracted
    @staticmethod
    def extract_length(substring):
        """Extract the length from a substring beginning with the length"""

        length = re.search("^(\.?[0-9]+).*", substring)

        if length:
            if length.group(1)[0] == ".":
                return [float(length.group(1)), substring[length.end(1)::]]
            return [int(length.group(1)), substring[length.end(1)::]]
        return [None, substring]


    @staticmethod
    def extract_octave_indicators(substring):
        """Given a substring beginning with ' or , extract the octave indicators"""

        indicators = re.search("^([',\,]+).*", substring)
        if indicators:
            number = len(indicators.group(1))
            if indicators.group(1)[0] == ",":
                number *= -1

            return [number, substring[indicators.end(1)::]]

        return [0, substring]


    @staticmethod
    def get_chord_note(substring):
        """Given a substring beginning with a note, get the chord"""

        note = substring[0]

        [octave_indicators, substring] = Representation.extract_octave_indicators(
            substring[1 : len(substring)])

        if note in Representation.NOTE_DICT:
            pitch = Representation.NOTE_DICT[note]
            pitch -= 7 * octave_indicators

            return [pitch, substring]

        elif note == "r":
            pitch = -1

            return [pitch, substring]

        return [None, substring]

    @staticmethod
    def extract_note_attributes(substring : str) -> list[str, str]:
        """Extract note attributes (#, b, natural)"""

        if len(substring) == 0:
            return [None, substring]

        match substring[0]:
            case "#":
                return ["sharp", substring[1::]]

            case "-":
                return ["flat", substring[1::]]

            case "n":
                return ["natural", substring[1::]]

            case _:
                return [None, substring]

    @staticmethod
    def extract_chord(substring):
        """Given a substring beginning with "<", extract the chord"""

        notes = re.search("^<([a-z',#-]+)>.*", substring)

        chord = Chord(-1, 0, 0)
        chord.remove_note(chord.notes[0])

        substring = substring[notes.start(1)::]
        ch = substring[0]

        while ch != ">":

            [pitch, substring] = Representation.get_chord_note(substring[0::])
            note = chord.add_note(pitch)

            [attribute, substring] = Representation.extract_note_attributes(substring)
            note.toggle_attribute(attribute)

            ch = substring[0]

        [length, substring] = Representation.extract_length(substring[1::])

        if length is None:
            chord.length = Representation.current_length
        else:
            chord.length = length
            Representation.current_length = length


        # Return the substring after the '>' and optional length indicator
        return [chord, substring]

    @staticmethod
    def score_to_lilypond(score : list[Bar], beats : int, key : str):
        """Convert a score to lilypond notation"""
        string = "\\version \"2.26.0\"{ \\fixed c' { \\numericTimeSignature "

        string += f"\\time {beats}/4 "

        [pitch, mode] = key.split(" ")
        pitch = pitch.replace("#", "is").replace("b", "es").lower()
        string += f"\\key {pitch} \\{mode.lower()} "

        for bar in score:
            for chord in bar.chords:

                chordstr = ""
                for note in chord.notes:
                    notestr = Representation.pitch_to_note(note.pitch)

                    if note.sharp:
                        notestr = notestr[0] + "is" + notestr[1::]
                    elif note.flat:
                        notestr = notestr[0] + "es" + notestr[1::]

                    chordstr += " " + notestr

                if len(chord.notes) > 1:
                    chordstr = "<" + chordstr + ">"

                # Convert to lilypond length convention
                if chord.length < 1:
                    lilypond_length = int((1 / chord.length) * 4)

                else:
                    lilypond_length = { 1 : "4", 4 : "1", 3 : "2.", 2 : "2"}.get(chord.length)

                if lilypond_length != Representation.current_length:
                    chordstr += str(lilypond_length)
                    Representation.current_length = lilypond_length

                if chord.tie:
                    chordstr += "~"

                if chord.accent:
                    chordstr += "->"

                if chord.staccato:
                    chordstr += "\\staccato"

                string += chordstr + " "


        return string + "}}"
                