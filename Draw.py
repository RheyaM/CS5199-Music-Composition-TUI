import curses
import math

class Draw:

    hints = {"q": "Quit", "s": "save file", "S": "save file as", "SHIFT-note": "add multiple notes" , "Opt-Up/Down": "transpose by 1", 
             "SHIFT-Up/Down": "transpose by an octave", "SHIFT-Left/Right": "swap notes", 
             "[,]": "adjust note length", "!": "staccato", ">": "accent", "#": "sharp", "-": "flat", 
             "n": "natural", "ENTER": "Reformat bars"}

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

    def drawBeginning(pad):

        pad.addstr(1, 0, "\u250E" + ("\u2500" * 11))

        for i in range(3, 8, 2):
            pad.addstr(i, 0, "\u2520" + ("\u2500" * 11))

        for i in range(2, 9, 2):
            pad.addstr(i, 0, "\u2503" + (" " * 11))

        pad.addstr(9, 0, "\u2516" + ("\u2500" * 11))

        Draw.drawTreble(pad, 1, 4)
        Draw.drawTimeSig(pad, 4, 10, "4", "4")

    
    def drawTimeSig(pad, x, y, num, dom):
        pad.addstr(x, y, num)
        pad.addstr(x + 2, y, dom)

    def drawRest(pad, chord):
        y = chord.y
        if chord.length == 1:
            pad.addstr(4, y, "\u2572")
            pad.addstr(5, y, "\u2571")
            pad.addstr(6, y, "\u2572")
            pad.addstr(7, y, "C")

        elif chord.length < 1:
            subdivision = 1 / chord.length
            lines = math.log(subdivision, 2)
            for i in range(int(lines)):
                pad.addstr(4 + i, y, "⚈")

            for i in range(4):
                pad.addstr(4 + i, y + 1, "|")


        elif chord.length == 2:
            pad.addstr(5, y, "▀▀")

        elif chord.length == 4:
            pad.addstr(5, y, "▃▃")

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

    

    def emptyStaveRegion(pad, y):
        for x in range (1, 10, 2):
            pad.addstr(x, y - 1, "────")
        for x in range(0, 13, 2):
            pad.addstr(x, y - 1, "    ")
        pad.addstr(11, y - 1, "    ")

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