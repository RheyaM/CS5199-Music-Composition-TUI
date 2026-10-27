import re
from Objects.Bar import Bar
import Objects.Beat as Beat
from Objects.Chord import Chord
from Objects.Note import Note
import Draw

class Representation:

    note_dict = {"c": 11, "d": 10, "e": 9, "f": 8, "g": 7, "a": 6, "b": 5}

    current_length = 0
    
    def scoreToString(score, beats):
        string = "B:" + str(beats) + "."
        currentLen = 0

        for bar in score:
            for beat in bar.beats:
                for chord in beat.chords:

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
                        notestr += str(chord.length)
                        currentLen = chord.length

                    string += notestr
            
            string += "|"

        return string

    def pitchToNote(pitch):

        if pitch == -1:
            return "r"

        pitch_dict = {11 : "c", 10: "d", 9: "e", 8: "f", 7: "g", 6: "a", 5: "b"}

        if pitch in pitch_dict.keys():
            return pitch_dict[pitch]

        else:
            dir = 0

            while pitch < 5:
                pitch += 7
                dir += 1

            note = pitch_dict[pitch] + ("'" * dir)

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
            char = notes[0]
            if char == "|":
                [bar, notes] = Representation.extractBar(notes, beats)
                score.append(bar)

        return score

    # Given a substring beginning with |, return the Bar within that
    # TODO: deal with sharps, flats, naturals
    def extractBar(substring, beats):
        
        barregex = re.search("^\|(.*)\|.*", substring)
        barNotes = barregex.group(1)
        bar = Bar(0, beats)
        bar.emptyBar()

        currentBeat = 0
        totalLength = 0

        while len(barNotes) > 0:
            ch = barNotes[0]

            if ch == "<":
                [chord, barNotes] = Representation.extractChord(barNotes)
                totalLength += int(chord.length)
                Representation.current_length = chord.length

            elif ch in Representation.note_dict.keys() or ch == "r":
                [pitch, barNotes] = Representation.getChordNote(barNotes)

                [func, barNotes] = Representation.extractNoteAttributes(barNotes)

                # Determining the length of the note
                [length, barNotes] = Representation.extractLength(barNotes)

                if length is None:
                    length = Representation.current_length
                    print("Using " + str(Representation.current_length) + " as length")
                else:
                    print("Updating current_length to: " + str(length))
                    Representation.current_length = length

                chord = Chord(pitch, length, 0)

                func(chord.notes[0])

                totalLength += chord.length

            bar.beats[currentBeat].addChord(-1, chord)

            if totalLength == 1 or totalLength == 2 or totalLength == 3:
                currentBeat += totalLength
                totalLength = 0
                
                print("Updating currentBeat to: " + str(currentBeat))

        substring = substring[barregex.end(1) ::]
        return [bar, substring]

    # Given a substring beginning with a length
    def extractLength(substring):
        print("Extracting length: " + substring)

        length = re.search("^(\.?[0-9]+).*", substring)

        if length:
            if length.group(1)[0] == ".":
                return [float(length.group(1)), substring[length.end(1)::]]
            return [int(length.group(1)), substring[length.end(1)::]]
        return [None, substring]


    # Given a substring beginning with '
    def extractOctaveIndicators(substring):

        print("Extracting Octave Indicators: " + substring)

        indicators = re.search("^('+)[.]*", substring)
        if indicators:
            number = len(indicators.group(1))
            return [number, substring[indicators.end(1)::]]

        return [0, substring]

    
    # Given a substring beginning with a note
    def getChordNote(substring):
        print("Getting Chord Note: "+substring)

        note = substring[0]

        [octaveIndicators, substring] = Representation.extractOctaveIndicators(substring[1 : len(substring)])

        if note in Representation.note_dict.keys():
            pitch = Representation.note_dict[note]
            pitch -= 7 * octaveIndicators

            return [pitch, substring]

        elif note == "r":
            pitch = -1

            return [pitch, substring[1::]]

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
                return [Note.toggleFlat(), substring[1::]]

            case "n":
                return [Note.toggleNatural(), substring[1::]]

            case _:
                return [passFunc, substring]

                
    # Given a substring beginning with "<"
    def extractChord(substring):
        global note_dict 

        print("Extracting chord: " + substring)

        notes = re.search("^<([a-z',#-]+)>.*", substring)

        chord = Chord(-1, 0, 0, True)
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
        chord.length = length

        print("extractChord returning substring: " + substring)

        # Return the substring after the '>' and optional length indicator
        return [chord, substring]
