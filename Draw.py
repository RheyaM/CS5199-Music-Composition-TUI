import curses
import math

from Objects.Chord import Chord

middle_c = 9

keys : dict = {"C Major": [], "G Major": [6], "D Major": [6, 9], 
               "A Major": [6, 9, 5], "E Major": [6, 9, 5, 8],
               "B Major": [6, 9, 5, 8, 11], "F# Major": [6, 9, 5, 8, 11, 7],
               "Db Major": [10, 7, 11, 8, 12], "Ab Major": [10, 7, 11, 8], 
               "Eb Major": [10, 7, 11], "Bb Major": [10, 7], "F Major": [10]}

class Draw:

    hints = {"q": "Quit", "s": "save file", "S": "save file as", "SHIFT-note": "add multiple notes" , "Opt-Up/Down": "transpose by 1", 
                 "SHIFT-Up/Down": "transpose by an octave", "SHIFT-Left/Right": "swap notes", 
                 "[": "decrease note length", "]": "increase note length", "!": "staccato", ">": "accent", "#": "sharp", "-": "flat", 
                 "n": "natural", "p" : "Play score", "m" : "Export to PDF"}

    def drawTreble(pad, x, y):
        pad.addstr(x, y, "|\\")
        pad.addstr(x + 1, y, "| |")
        pad.addstr(x + 2, y, "|─/")
        pad.addstr(x + 3, y, "|/")
        pad.addstr(x + 4, y - 1, "/|")
        pad.addstr(x + 5, y - 2, "| |\u2581\u2581")
        pad.addstr(x + 6, y - 2, "|─/──\\")
        pad.addstr(x + 7, y - 2, "\ |  |")
        pad.addstr(x + 8, y - 1, "\u005C|─/")
        pad.addstr(x + 9, y, "|")
        pad.addstr(x + 10, y - 1, "◯|")

    def drawBeginning(pad, beats, key, middle_c):

        length = 15

        pad.addstr(middle_c - 3, 0, "┎" + ("─" * length))

        for i in range(middle_c - 1, middle_c + 4, 2):
            pad.addstr(i, 0, "┠" + ("─" * length))

        for i in range(middle_c - 2, middle_c + 5, 2):
            pad.addstr(i, 0, "┃" + (" " * length))

        pad.addstr(middle_c + 5, 0, "┖" + ("─" * length))

        Draw.drawTreble(pad, middle_c - 3, 4)
        Draw.drawTimeSig(pad, middle_c, 10, str(beats), "4")
        Draw.draw_key_sig(pad, middle_c + 5, key)
    
    def drawTimeSig(pad, x, y, num, dom):
        pad.addstr(x, y, num)
        pad.addstr(x + 2, y, dom)

    def draw_key_sig(pad, x, key):
        if key[1] == "b" or key == "F Major":
            char = "♭"
        else:
            char = "#"

        # dir represents which direction the coordinates of the notes must change
        start_x = x
        for sharp in keys[key]:
            pad.addstr(sharp, start_x, char)
            start_x += 1


    def drawRest(pad, chord):
        y = chord.y
        if chord.length == 1:
            pad.addstr(middle_c, y, "╲")
            pad.addstr(middle_c + 1, y, "╱")
            pad.addstr(middle_c + 2, y, "╲")
            pad.addstr(middle_c + 3, y, "C")

        elif chord.length < 1:
            subdivision = 1 / chord.length
            lines = math.log(subdivision, 2)
            for i in range(int(lines)):
                pad.addstr(middle_c + i, y, "⚈")

            for i in range(4):
                pad.addstr(middle_c + i, y + 1, "|")

        elif chord.length == 4:
            pad.addstr(middle_c - 1, y, "▃▃")

        elif chord.length == 2:
            pad.addstr(middle_c + 2, y, "▀▀")

        elif chord.length == 3:
            pad.addstr(middle_c + 2, y, "▀▀•")


    def drawNotes(pad : curses.window, chord : Chord) -> list[int]:
        notes = chord.notes
        y = chord.y
        noteCoords = []

        for note in notes:
                    
            noteCoords.append(note.pitch)
            if chord.length >= 2:
                string = "❨❩"
            else:
                string = "⚪"
            
            pad.addstr(note.pitch, y, string, curses.color_pair(2))
            Draw.drawAttributes(pad, note, chord)

        return noteCoords

    def drawAttributes(pad, note, chord):
        x = note.pitch
        y = chord.y

        if note.sharp:
            pad.addstr(x, y-1, "#")
        elif note.flat:
            pad.addstr(x, y-1, "♭", curses.A_BOLD)
        elif note.natural:
            pad.addstr(x, y-1, "♮", curses.A_BOLD)

        if chord.length == 3:
            pad.addstr(x, y+2, "•")

    def drawTie(pad, chord):
        y = chord.y
        x = chord.notes[-1].pitch

        linex = x + 1 if x > 5 else x - 1
        chars = ["\\", "_",  "/"] if x > 5 else ["/", "▔",  "\\"]
        pad.addstr(linex, y + 1, chars[0])
        y += 1
        
        above = pad.instr(x, y + 1, 3).decode("utf-8")


        while above != "❨" and above != "⚪":
            pad.addstr(linex, y + 1, chars[1])
            y += 1
            above = pad.instr(x, y + 1, 3).decode("utf-8")
            
        pad.addstr(linex, y, chars[1] + chars[2])

    def emptyStaveRegion(pad, y):
        for x in range(0, 24):
            pad.addstr(x, y - 1, "    ")
        for x in range (middle_c - 3, middle_c + 6, 2):
            pad.addstr(x, y - 1, "────")

    def drawHints(pad, width):
        pad.erase()

        x = 0
        y = 0

        for key in Draw.hints.keys():

            expl = Draw.hints[key]

            totalLen = len(key) + 3 + len(expl)
            if y + totalLen >= width:
                x += 1
                y = 0

            pad.addstr(x, y, key, curses.A_STANDOUT)
            y += len(key) + 1
            pad.addstr(x, y, expl)
            y += len(expl) + 3
            