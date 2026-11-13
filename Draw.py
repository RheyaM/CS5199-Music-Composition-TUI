import curses
import math

from Objects.Chord import Chord

keys : dict = {"C Major": [], "G Major": [3], "D Major": [3, 6], 
               "A Major": [3, 6, 2], "E Major": [3, 6, 2, 5],
               "B Major": [3, 6, 2, 5, 8], "F# Major": [3, 6, 2, 5, 8, 4],
               "Db Major": [7, 4, 8, 5, 9], "Ab Major": [7, 4, 8, 5], 
               "Eb Major": [7, 4, 8], "Bb Major": [7, 4], "F Major": [7]}


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

    def drawBeginning(pad, beats, key):

        length = 15

        pad.addstr(3, 0, "┎" + ("─" * length))

        for i in range(5, 10, 2):
            pad.addstr(i, 0, "┠" + ("─" * length))

        for i in range(4, 11, 2):
            pad.addstr(i, 0, "┃" + (" " * length))

        pad.addstr(11, 0, "┖" + ("─" * length))

        Draw.drawTreble(pad, 3, 4)
        Draw.drawTimeSig(pad, 6, 10, str(beats), "4")
        Draw.draw_key_sig(pad, 12, key)
    
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
            pad.addstr(6, y, "╲")
            pad.addstr(7, y, "╱")
            pad.addstr(8, y, "╲")
            pad.addstr(9, y, "C")

        elif chord.length < 1:
            subdivision = 1 / chord.length
            lines = math.log(subdivision, 2)
            for i in range(int(lines)):
                pad.addstr(6 + i, y, "⚈")

            for i in range(4):
                pad.addstr(6 + i, y + 1, "|")

        elif chord.length == 4:
            pad.addstr(5, y, "▃▃")

        elif chord.length == 2:
            pad.addstr(7, y, "▀▀")

        elif chord.length == 3:
            pad.addstr(7, y, "▀▀•")


    def drawNotes(pad : curses.window, chord : Chord) -> list[int]:
        notes = chord.notes
        y = chord.y
        noteCoords = []

        for note in notes:
                    
            noteCoords.append(note.pitch)
            if chord.length >= 2:
                string = "❨❩"
            else:
                string = "\u26AA"

            open("log.txt", "a").write("\nnote.pitch: " + str(note.pitch) + ". y: " + str(y))
            pad.addstr(note.pitch, y, string, curses.color_pair(2))
            Draw.drawAttributes(pad, note, chord)

        return noteCoords

    def drawAttributes(pad, note, chord):
        x = note.pitch
        y = chord.y

        if note.sharp:
            pad.addstr(x, y-1, "#")
        elif note.flat:
            pad.addstr(x, y-1, "\u266D", curses.A_BOLD)
        elif note.natural:
            pad.addstr(x, y-1, "\u266E", curses.A_BOLD)

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
        for x in range(0, 15):
            pad.addstr(x, y - 1, "    ")
        for x in range (3, 12, 2):
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
            