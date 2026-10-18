import curses
import math

class Draw:
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

        # elif chord.length == 0.5:
        #     pad.addstr(4, y, "Q")
        #     pad.addstr(5, y, "u")

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

    def drawHints(pad):
        pad.addstr("|q: quit|  ")
        pad.addstr("|Opt-UP/DOWN: transposition by 1|   ")
        pad.addstr("|SHIFT-UP/DOWN: transposition by an octave|   ")
        pad.addstr("|SHIFT-LEFT/RIGHT: swap notes|   ")
        pad.addstr("\n|[ and ]: adjust note length|   ")
        pad.addstr("|!: staccato|   ")
        pad.addstr("|>: accent|   ")
        pad.addstr("|#: sharp|   ")
        pad.addstr("|-: flat|   ")
        pad.addstr("|n: natural|   ")
        pad.addstr("|ENTER: reformat bars")
        pad.addstr("|s: save file")






        # pad.addstr("^UP/DOWN: transposition by 1")
        # pad.addstr("^UP/DOWN: transposition by 1")
        # pad.addstr("^UP/DOWN: transposition by 1")
        # pad.addstr("^UP/DOWN: transposition by 1")
        
