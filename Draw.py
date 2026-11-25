
import curses
from curses.textpad import rectangle
import math

from Objects.Chord import Chord


class Draw:
    """Class for drawing features onto screen"""

    MIDDLE_C : int = 9

    KEYS : dict = {"C Major": [], "G Major": [6], "D Major": [6, 9],
                "A Major": [6, 9, 5], "E Major": [6, 9, 5, 8],
                "B Major": [6, 9, 5, 8, 11], "F# Major": [6, 9, 5, 8, 11, 7],
                "Db Major": [10, 7, 11, 8, 12], "Ab Major": [10, 7, 11, 8], 
                "Eb Major": [10, 7, 11], "Bb Major": [10, 7], "F Major": [10]}

    HINTS = {"q": "Quit", "s": "Save File", "S": "Save File As", "SHIFT-note": "Add Multiple Notes",
             "Opt-Up/Down": "Change Pitch", "SHIFT-Up/Down": "Change Octave", 
             "[": "Decrease Note Length", "]": "Increase Note Length", "!": "Staccato", 
             ">": "Accent", "#": "Sharp", "-": "Flat", "n": "Natural", "z" : "Undo", 
             "p" : "Play Score", "v" : "Pause Playback", "m" : "Export to PDF", 
             "k" : "Project Settings", "0": "Clear All", "h" : "String Input Mode",
             "CMMD-Left/Right": "Move to Beginning/End"}

    @staticmethod
    def draw_treble(pad, x, y):
        """Draw treble clef"""
        pad.addstr(x, y, "|\\")
        pad.addstr(x + 1, y, "| |")
        pad.addstr(x + 2, y, "|─/")
        pad.addstr(x + 3, y, "|/")
        pad.addstr(x + 4, y - 1, "/|")
        pad.addstr(x + 5, y - 2, "| |▁▁")
        pad.addstr(x + 6, y - 2, "|─/──\\")
        pad.addstr(x + 7, y - 2, "\\ |  |")
        pad.addstr(x + 8, y - 1, "\\|─/")
        pad.addstr(x + 9, y, "|")
        pad.addstr(x + 10, y - 1, "◯|")

    @staticmethod
    def draw_beginning(proj, pad, MIDDLE_C):
        """Draw the beginning of the stave, including treble clef, time & key signatures"""

        beats = proj.beats
        key = proj.key
        length = 15

        pad.addstr(MIDDLE_C - 3, 0, "┎" + ("─" * length))

        for i in range(MIDDLE_C - 1, MIDDLE_C + 4, 2):
            pad.addstr(i, 0, "┠" + ("─" * length))

        for i in range(MIDDLE_C - 2, MIDDLE_C + 5, 2):
            pad.addstr(i, 0, "┃" + (" " * length))

        pad.addstr(MIDDLE_C + 5, 0, "┖" + ("─" * length))

        Draw.draw_treble(pad, MIDDLE_C - 3, 4)
        Draw.draw_time_sig(pad, MIDDLE_C, 10, str(beats), "4")
        Draw.draw_key_sig(pad, 12, key)

    @staticmethod
    def draw_time_sig(pad, x, y, num, dom):
        """Draw the time signature"""
        Draw.empty_stave_region(pad, y)
        pad.addstr(x, y, num)
        pad.addstr(x + 2, y, dom)

    @staticmethod
    def draw_key_sig(pad, y, key):
        """Draw the key signature starting at the given y coordinate"""
        if key[1] == "b" or key == "F Major":
            char = "♭"
        else:
            char = "#"

        # dir represents which direction the coordinates of the notes must change
        start_y = y
        for sharp in Draw.KEYS[key]:
            pad.addstr(sharp, start_y, char)
            start_y += 1

    @staticmethod
    def draw_rest(pad, chord):
        """Draw a rest note"""
        y = chord.y
        if chord.length == 1:
            pad.addstr(Draw.MIDDLE_C, y, "╲")
            pad.addstr(Draw.MIDDLE_C + 1, y, "╱")
            pad.addstr(Draw.MIDDLE_C + 2, y, "╲")
            pad.addstr(Draw.MIDDLE_C + 3, y, "C")

        elif chord.length < 1:
            subdivision = 1 / chord.length
            lines = math.log(subdivision, 2)
            for i in range(int(lines)):
                pad.addstr(Draw.MIDDLE_C + i, y, "⚈")

            for i in range(4):
                pad.addstr(Draw.MIDDLE_C + i, y + 1, "|")

        elif chord.length == 4:
            pad.addstr(Draw.MIDDLE_C - 1, y, "▃▃")

        elif chord.length == 2:
            pad.addstr(Draw.MIDDLE_C + 1, y, "▀▀")

        elif chord.length == 3:
            pad.addstr(Draw.MIDDLE_C + 1, y, "▀▀•")

    @staticmethod
    def draw_notes(pad : curses.window, chord : Chord) -> list[int]:
        """Draw a note onto the stave"""
        notes = chord.notes
        y = chord.y
        note_coords = []

        for note in notes:

            note_coords.append(note.pitch)
            if chord.length >= 2:
                string = "❨❩"
            else:
                string = "⚪"

            if note.pitch < 6:
                for i in range(4, note.pitch - 1, -2):
                    pad.addstr(i, y - 1, "─", curses.color_pair(2))

            if note.pitch > 15:
                for i in range(16, note.pitch + 1, 2):
                    pad.addstr(i, y - 1, "─", curses.color_pair(2))

            pad.addstr(note.pitch, y, string, curses.color_pair(2))
            Draw.draw_attributes(pad, note, chord)

        return note_coords

    @staticmethod
    def draw_attributes(pad, note, chord):
        """Draw note attributes (#, b, natural)"""
        x = note.pitch
        y = chord.y

        match note.attribute:
            case "sharp":
                pad.addstr(x, y-1, "#")
            case "flat":
                pad.addstr(x, y-1, "♭", curses.A_BOLD)
            case "natural":
                pad.addstr(x, y-1, "♮", curses.A_BOLD)

        if chord.length == 3:
            pad.addstr(x, y+2, "•")

    @staticmethod
    def draw_tie(pad, chord):
        """Draw a tie from the current chord to the next"""
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

    @staticmethod
    def empty_stave_region(pad, y):
        """Empty the stave at the given y"""
        for x in range(0, 26):
            pad.addstr(x, y - 1, "    ")
        for x in range (Draw.MIDDLE_C - 3, Draw.MIDDLE_C + 6, 2):
            pad.addstr(x, y - 1, "────")

    @staticmethod
    def draw_hints(pad, width):
        """Draw hints at the bottom of the screen"""
        pad.erase()

        x = 0
        y = 0

        for keypress, expl in Draw.HINTS.items():

            total_len = len(keypress) + 3 + len(expl)
            if y + total_len >= width:
                x += 1
                y = 0

            try:
                pad.addstr(x, y, keypress, curses.A_STANDOUT)
            except curses.error:
                return
            y += len(keypress) + 1
            pad.addstr(x, y, expl)
            y += len(expl) + 3

    @staticmethod
    def draw_chord(pad, chord, stave_height):
        """Draw the given chord"""

        y = chord.y

        Draw.empty_stave_region(pad, y)

        if not chord.rest:
            note_coords = Draw.draw_notes(pad, chord)
            Draw.draw_stem(pad, chord, note_coords, stave_height)

        else:
            Draw.draw_rest(pad, chord)

    @staticmethod
    def draw_stem(pad : curses.window, chord : Chord, note_coords : list[int], stave_height : int):
        """Draw the stem of the chord"""
        y = chord.y
        furthestdist = Draw.determine_furthest_dist(note_coords)

        if furthestdist > 0: # Stem on the right, going up
            side = y + 1
            start = note_coords[0] - 6

            Draw.draw_chord_attributes(pad, chord, note_coords[-1], 1)
        else: # Stem on the left, going down
            side = y
            start = note_coords[0]

            Draw.draw_chord_attributes(pad, chord, note_coords[0], -1)

        note_range = abs(note_coords[0] - note_coords[-1])

        if chord.length != 4:
            for i in range(note_range + 5):
                x = start + i + 1
                if x not in note_coords and x >= 0 and x <= stave_height:
                    pad.addstr(x, side, "\u2502")


        if chord.length < 1:

            subdivision = 1 / chord.length
            lines = int(math.log(subdivision, 2))

            if furthestdist > 0: #on the right, going up (at the top)
                start = start + 1
                char = "⎞"
            else:
                start = note_range + 6 + start - lines
                char = "⎠"

            for i in range(lines):
                pad.addstr(start + i, side + 1, char)

    @staticmethod
    def determine_furthest_dist(note_coords : list[int]):
        """Determine the furthest distance from the middle line in the chord"""
        furthestdist = 0
        for n in note_coords:
            dist = n - (Draw.MIDDLE_C + 1)
            if abs(dist) > abs(furthestdist):
                furthestdist = dist

        note_coords.sort()

        return furthestdist

    @staticmethod
    def draw_chord_attributes(pad, chord, last_note, direction):
        """Draw chord attributes (staccato, accent)"""

        current_coord = last_note + direction

        if chord.staccato:
            pad.addstr(current_coord, chord.y, "•")
            current_coord = current_coord + direction
        if chord.accent:
            pad.addstr(current_coord, chord.y, ">")

    @staticmethod
    def draw_bars_from(proj, pads, bar_index, stave_height):
        """Alternative to draw_bar, draw all bars starting from score[bar_index]."""
        score = proj.score

        for i in range(bar_index, len(score)):
            Draw.draw_bar(proj, pads, i, stave_height)

        for bar in score:
            for chord in bar.chords:
                if chord.tie and not chord.rest:
                    Draw.draw_tie(pads[bar.pad], chord)

    @staticmethod
    def draw_bar(proj, pads, bar_index, stave_height):
        """Draw bar score[bar_index] onto the stave."""

        score = proj.score

        middle_c = Draw.MIDDLE_C

        bar = score[bar_index]
        pad = pads[bar.pad]

        start_y = bar.y
        end_y = bar.endy

        length = end_y - start_y - 1

        for i in range(0, stave_height - 1):
            pad.addstr(i, start_y, " " * (length + 2))

        pad.addstr(middle_c - 3, start_y, "┰" + ("─" * length) + "┒")
        for i in range(middle_c - 2, middle_c + 5, 2):
            pad.addstr(i, start_y, "┃" + (" " * length) + "┃")
        for i in range(middle_c - 1, middle_c + 4, 2):
            pad.addstr(i, start_y, "┠" + ("─" * length) + "┨")
        pad.addstr(middle_c + 5, start_y, "┸" + ("─" * length) + "┚")

        if start_y == 0:
            pad.addstr(middle_c - 3, start_y, "┎")
            pad.addstr(middle_c + 5, start_y, "┖")

        for chord in bar.chords:
            Draw.draw_chord(pad, chord, stave_height)

        if bar_index == 0:
            Draw.draw_beginning(proj, pad, middle_c)

        # If a bar is the last on its pad, or the last in score, remove any further characters
        if (bar_index < len(score) - 1 and score[bar_index + 1].pad > score[bar_index].pad) or bar_index == len(score) - 1:
            [height, width] = pad.getmaxyx()
            for i in range(height):
                pad.move(i, end_y + 1)
                pad.clrtoeol()

    @staticmethod
    def draw_entire_score(proj, pads, stave_height):
        """Redraw entire score"""
        score = proj.score

        for i in range(len(score)):
            Draw.draw_bar(proj, pads, i, stave_height)

        for bar in score:
            for chord in bar.chords:
                if chord.tie and not chord.rest:
                    Draw.draw_tie(pads[bar.pad], chord)

    @staticmethod
    def draw_exception(stdscr : curses.window, x : int, message : str) -> curses.window:
        """Draw a rectangle to store the exception"""
        exception_win = curses.newwin(2, 20, x, 1)
        curses.textpad.rectangle(stdscr, x - 1, 0, x + 2, 21)
        stdscr.refresh()

        exception_win.addstr(0, 0, message)
        exception_win.refresh()

        return exception_win

    @staticmethod
    def remove_exception(exception_win : curses.window) -> None:
        """Remove the exception rectangle"""
        # exception_win.clear()
        exception_win.erase()
