import re
from Objects.Bar import Bar
from Objects.Chord import Chord
from Objects.Note import Note

class Representation:

    note_dict = {"c": 13, "d": 12, "e": 11, "f": 10, "g": 9, "a": 8, "b": 7}
    pitch_dict = {13 : "c", 12: "d", 11: "e", 10: "f", 9: "g", 8: "a", 7: "b"}

    current_length = 0
    
    def scoreToString(score, beats):
        string = "B:" + str(beats) + "."
        currentLen = 0

        string += "|"

        for bar in score:
            for chord in bar.chords:

                notestr = ""

                for note in chord.notes:
                    notestr += Representation.pitchToNote(note.pitch)

                    if note.sharp:
                        notestr += "#"
                    elif note.flat:
                        notestr += "-"
                    elif note.natural:
                        notestr += "n"

                if len(chord.notes) > 1:
                    notestr = "<" + notestr + ">"

                if chord.length != currentLen:
                    lengthString = str(chord.length)

                    if chord.length < 1 and len(lengthString) > 1:
                        notestr += lengthString[1::]
                    else:
                        notestr += str(int(chord.length))
                    currentLen = chord.length

                string += notestr
            
            string += "|"

        return string

    def pitchToNote(pitch):

        if pitch == -1:
            return "r"


        if pitch in Representation.pitch_dict.keys():
            return Representation.pitch_dict[pitch]

        else:
            dir = 0

            while pitch < 7:
                pitch += 7
                dir += 1
                char = "'"

            while pitch > 13:
                pitch -= 7
                dir += 1
                char = ","

            note = Representation.pitch_dict[pitch] + (char * dir)

            return note


    # TODO: maybe removing charrs as we go isn't the most efficient? space or timing wise?
    # Iterating when possible mayy be better
    # I.e. like when you get the group of notes in a chord. Don't need to eat them
    # Just need to iterate probably
    def stringToScore(string):
        global note_dict

        score = []

        index = string.index(".")

        beats = int(re.search("B:(\d)\.", string).group(1))

        notes = string[index + 1::]

        # While there are still bars to extract
        while len(notes) > 1:
            [bar, notes] = Representation.extractBar(notes, beats)
            score.append(bar)

        return score

    # Given a substring beginning with |
    # Return the first bar extracted, and the remaining substring containing the last |
    def extractBar(substring, beats):

        barNotes = substring[1::]
        bar = Bar(0, beats)
        bar.emptyBar()

        while len(barNotes) > 1:

            ch = barNotes[0]

            if ch == "|":
                bar.redoY()
                return [bar, barNotes]

            if ch == "<":
                [chord, barNotes] = Representation.extractChord(barNotes)
                Representation.current_length = chord.length

            elif ch in Representation.note_dict.keys() or ch == "r":
                [pitch, barNotes] = Representation.getChordNote(barNotes)

                [func, barNotes] = Representation.extractNoteAttributes(barNotes)

                # Determining the length of the note
                [length, barNotes] = Representation.extractLength(barNotes)

                if length is None:
                    length = Representation.current_length
                else:
                    Representation.current_length = length

                chord = Chord(pitch, length, 0)

                func(chord.notes[0])


            bar.chords.append(chord)

        bar.redoY()
        return [bar, barNotes]

    # Given a substring beginning with a length
    # TODO: should default to current_length here rather than once None has been extracted
    def extractLength(substring):

        length = re.search("^(\.?[0-9]+).*", substring)

        if length:
            if length.group(1)[0] == ".":
                return [float(length.group(1)), substring[length.end(1)::]]
            return [int(length.group(1)), substring[length.end(1)::]]
        return [None, substring]


    # Given a substring beginning with ' or ,
    def extractOctaveIndicators(substring):

        indicators = re.search("^([',\,]+).*", substring)
        if indicators:
            number = len(indicators.group(1))
            if indicators.group(1)[0] == ",":
                number *= -1

            return [number, substring[indicators.end(1)::]]

        return [0, substring]

    
    # Given a substring beginning with a note
    def getChordNote(substring):

        note = substring[0]

        [octaveIndicators, substring] = Representation.extractOctaveIndicators(substring[1 : len(substring)])

        if note in Representation.note_dict.keys():
            pitch = Representation.note_dict[note]
            pitch -= 7 * octaveIndicators

            return [pitch, substring]

        elif note == "r":
            pitch = -1

            return [pitch, substring]

        

        return [None, substring]


    def extractNoteAttributes(substring):
        def passFunc(self):
            pass

        if len(substring) == 0:
            return [passFunc, substring]

        match substring[0]:
            case "#":
                return [Note.toggleSharp, substring[1::]]

            case "-":
                return [Note.toggleFlat, substring[1::]]

            case "n":
                return [Note.toggleNatural, substring[1::]]

            case _:
                return [passFunc, substring]

                
    # Given a substring beginning with "<"
    def extractChord(substring):
        global note_dict 

        notes = re.search("^<([a-z',#-]+)>.*", substring)

        chord = Chord(-1, 0, 0)
        chord.removeNote(chord.notes[0])

        substring = substring[notes.start(1)::]
        ch = substring[0]

        while ch != ">":

            [pitch, substring] = Representation.getChordNote(substring[0::])
            note = chord.addNote(pitch)

            [func, substring] = Representation.extractNoteAttributes(substring)
            func(note)

            ch = substring[0]

        [length, substring] = Representation.extractLength(substring[1::])

        if length is None:
            chord.length = Representation.current_length
        else:
            chord.length = length
            Representation.current_length = length


        # Return the substring after the '>' and optional length indicator
        return [chord, substring]

    def scoreToLilypond(score : list[Bar]):
        string = ""
        for bar in score:
            for chord in bar.chords:
                
                chordstr = ""
                for note in chord.notes:
                    notestr = Representation.pitchToNote(note.pitch)

                    if note.sharp:
                        notestr = notestr[0] + "is" + notestr[1::]
                    elif note.flat:
                        notestr = notestr[0] + "es" + notestr[1::]

                    chordstr += notestr

                if len(chord.notes) > 1:
                    chordstr = "<" + chordstr + ">"

                # Convert to lilypond length convention
                if chord.length < 1:
                    lilypond_length = int((1 / chord.length) * 4)

                elif chord.length == 1:
                    lilypond_length = 4

                elif chord.length == 4:
                    lilypond_length = 1

                else:
                    lilypond_length = chord.length
                

                if lilypond_length != Representation.current_length:
                    chordstr += str(lilypond_length)
                    Representation.current_length = lilypond_length

                string += chordstr + " "

        return "\\version \"2.26.0\"{ \\fixed c' {" + string + "}}"
                