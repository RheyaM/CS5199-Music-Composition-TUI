import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle

from Bar import Bar
from Beat import Beat
from Chord import Chord
from Note import Note
from Draw import Draw
from Representation import Representation

import math
import time

# TODO: if navigateToNote() always comes after drawChord then just put it in drawChord
# TODO: be able to display key

file = ""

note_dict = {"c": 11, "d": 10, "e": 9, "f": 8, "g": 7, "a": 6, "b": 5}
all_notes = ["c", "C", "d", "D", "e", "E", "f", "F", "g", "G", "a", "A", "b", "B"]

beats = 4

# First bar starts at y = 13 and there are 4 beats in a bar
score = [Bar(11, beats), Bar(37, beats)]
pads = []

current_bar = 0 # Index of current bar object in score[]
current_beat = 0 # Index of current beat object in current_bar.beats
current_chord = None # Chord object
current_note = None # Note object

cursor_y = 15 # Current cursor position

# stave_height - going to restrict how many octaves we can use
stave_height = 13

stdscr_width = 0
stdscr_height = 0

# TODO: allow higher/lower notes past the stave
# TODO: Is it better to transpose with - and +?
# TODO: draw rests in drawChord() since rests are chords now

def main(stdscr):
    global current_note
    global current_chord
    global stdscr_height
    global stdscr_width

    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_WHITE, -1)

    curses.curs_set(0)

    current_chord = score[0].beats[0].chords[0]
    current_note = current_chord.notes[0]
    
    stdscr.clear()
    stdscr_height, stdscr_width = stdscr.getmaxyx()


    # Creating and adding the stave pad to the screen
    stave_pad = curses.newpad(15, 300)

    textbox = curses.newpad(3, stdscr_width)
    textbox.addstr(1, 0, Representation.scoreToString(score, beats))
    textbox.refresh(0, 0, stdscr_height - 6, 0, stdscr_height - 4, stdscr_width - 2)

    hints = curses.newpad(3, 300)

    Draw.drawHints(hints, stdscr_width)
    stdscr.refresh()

    pads.append(stave_pad)

    # Adding the empty stave to the pad
    drawEntireScore(score)

    navigateToNote()
    stave_pad.refresh(0, 0, 1, 1, stave_height, stdscr_width - 2)

    textbox.refresh(0, 0, stdscr_height - 6, 0, stdscr_height - 4, stdscr_width - 2)
    hints.refresh(0, 0, stdscr_height - 3, 0, stdscr_height - 1, stdscr_width - 2)

    # textinput = curses.newwin(2, 41, 15, 1)
    # box = Textbox(textinput)
    # rectangle(stdscr, 14, 0, 17, 42)
    # stdscr.refresh()

    # while True:
    #     box.edit()
    #     text = box.gather()
    #     stave_pad.clear()
    #     drawEmptyStave(stave_pad, stave_width)
    #     drawTreble(stave_pad, 1, 4)
    #     drawTimeSig(stave_pad, 4, 10, "4", "4")
    #     parseText(stave_pad, text)
    #     stave_pad.refresh(0, 0, 1, 1, stave_height, stave_width + 2)
    #     stdscr.refresh(◖)


    while True:

        char = stdscr.getkey()

        stave_pad = getCurrentPad()

        match char:
            case "q":
                # save(textbox)
                break

            case "\x7f":
                removeNote(stave_pad)

            case "\n":
                textbox.addstr(0, 0, Representation.scoreToString(score, beats))
                redoBar(stave_pad)

            case "KEY_UP" | "KEY_DOWN":
                verticalNavigation(stave_pad, char)

            case "KEY_RIGHT" | "KEY_LEFT":
                horizontalNavigation(stave_pad, char)

            case "kDN5" | ",":
                transpose("down", stave_pad, 1)

            case "kUP5" | ".":
                transpose("up", stave_pad, 1)

            case "KEY_SR":
                transpose("up", stave_pad, 7)

            case "KEY_SF":
                transpose("down", stave_pad, 7)

            case "KEY_SRIGHT":
                shift(stave_pad, "Right")

            case "KEY_SLEFT":
                shift(stave_pad, "Left")

            case "#":
                makeSharp(stave_pad)

            case "-":
                makeFlat(stave_pad)

            case "n":
                makeAccidental(stave_pad)

            case "!":
                toggleStaccato(stave_pad)

            case ">":
                toggleAccent(stave_pad)

            case "[":
                decLength(stave_pad)

            case "]":
                incLength()

            case "s":
                save(stdscr, textbox)

            case "S":
                saveAs(stdscr, textbox)

            case "p":
                refreshStavePad()

            case "l" | "L":
                load(stdscr)

            case "KEY_RESIZE":
                stdscr_height, stdscr_width = stdscr.getmaxyx()
                Draw.drawHints(hints, stdscr_width)
                redoAllYs(score)
                drawEntireScore(score)
                navigateToNote()


            case _:
                if char in all_notes:
                    parseNote(stave_pad, char)

                else:
                    stave_pad.addstr(0, 0, char)

        textbox.clear()
        textbox.addstr(1, 0, Representation.scoreToString(score, beats))
        textbox.refresh(0, 0, stdscr_height - 6, 0, stdscr_height - 4, stdscr_width - 2)

        hints.refresh(0, 0, stdscr_height - 3, 0, stdscr_height - 1, stdscr_width - 2)

        x = refreshStavePad()


def refreshStavePad():
    x = 1
    for pad in pads:
        if x < stdscr_height - 5:
            pad.refresh(0, 0, x, 1, min(stave_height + x, stdscr_height - 6), stdscr_width - 2)
        x += 13

    return x

def load(stdscr):
    # update global file string
    global file
    global score

    stdscr.erase()

    stdscr.addstr(stdscr_height - 7, 1, "Input your file name")
    stdscr.addstr(stdscr_height - 1, 1, "^G: Confirm          To cancel, leave empty")

    textinput = curses.newwin(2, 41, stdscr_height - 5, 2)
    box = Textbox(textinput)
    rectangle(stdscr, stdscr_height - 6, 1, stdscr_height - 3, 43)
    stdscr.refresh()

    box.edit()
    text = box.gather()

    try:
        with open(text, "r") as myfile:
            pass
                
        myfile.close()

        file = text

    except:
        pass

    stdscr.clear()
    drawEntireScore(score)
    refreshStavePad()



def save(stdscr, textbox):

    # Writing the stave itself to the .txt file:
    # for pad in pads:
    #     [y, x] = pad.getmaxyx()
    #     with open("test.txt", "a") as myfile:
    #         for i in range(y):
    #             myfile.write("\n" + pad.instr(i, 0).decode("utf-8"))

    if file != "":
        with open(file, "a") as myfile:
            myfile.write("\n" + textbox.instr(0, 0).decode("utf-8"))

        myfile.close()
    else:
        saveAs(stdscr, textbox)


def saveAs(stdscr, textbox):
    global file

    stdscr.clear()

    stdscr.addstr(stdscr_height - 7, 1, "Input your file name")
    stdscr.addstr(stdscr_height - 1, 1, "^G: Confirm          To cancel, leave empty")

    textinput = curses.newwin(2, 41, stdscr_height - 5, 2)
    box = Textbox(textinput)
    rectangle(stdscr, stdscr_height - 6, 1, stdscr_height - 3, 43)
    stdscr.refresh()

    box.edit()
    text = box.gather()

    if text != "":

        with open(text + ".txt", "a") as myfile:
            myfile.write(textbox.instr(0, 0).decode("utf-8"))
            
        myfile.close()

        file = text + ".txt"

    stdscr.clear()
    textinput.erase()

    stdscr.refresh()


def printAllChords(pad):
    global current_bar

    y = 0

    for beat in score[current_bar].beats:
        for chord in beat.chords:
            pad.addstr(0, y, str(chord.y))
            y += 3


# TODO: quaver moving to next bar needs whatever is there to split in half??
# Actually musescore doesn't allow shifting if they're not the same length...
# Or if they're in different bars. Maybe i only shift if same length...
def shift(pad, dir):
    global current_bar
    global current_beat
    global current_chord
    global current_note

    if dir == "Right":
        [beat, nextChord] = score[current_bar].getNextChord(current_beat, current_chord)
        change = 1
    else:
        [beat, nextChord] = score[current_bar].getPrevChord(current_beat, current_chord)
        change = -1

    # If there isn't another chord in the current bar
    if nextChord is None:
        nextBar = current_bar + change
        if nextBar < len(score) and nextBar >= 0:

            if dir == "Right":
                beat = 0 
            else:
                beat = -1

            nextChord = score[nextBar].beats[beat].chords[beat]

            if nextChord.length != current_chord.length:
                return

        else:
            return

    else:
        nextBar = current_bar
    
    current_beat_obj = getCurrentBeat()
    next_beat_obj = score[nextBar].beats[beat]

    nextIndex = next_beat_obj.getChordIndex(nextChord)
    currentIndex = current_beat_obj.getChordIndex(current_chord)

    # Switching the chords
    next_beat_obj.chords[nextIndex] = current_chord
    current_beat_obj.chords[currentIndex] = nextChord

    # Updating the y coordinates of the relevant chords
    temp = current_chord.y
    current_chord.y = nextChord.y
    nextChord.y = temp

    
    current_bar = nextBar
    current_beat = beat if beat != -1 else len(score[current_bar].beats) - 1

    drawChord(pad, nextChord)
    drawChord(pad, current_chord)
    navigateToNote()


# Redo all y values of every bar, beat and chord to get true y values
def redoAllYs(score):
    global pads

    end_y = 11

    for bar in score:

        # If the bar doesn't start where the previous ended, shift it left
        if bar.y != end_y and bar.y != 0:
            bar.shiftBar(end_y - bar.y)

        # If the bar is overflowing, update its pad, y, and endy values
        if bar.endy >= stdscr_width - 3:
            bar.pad += 1
            bar.shiftBar(bar.y * -1)

            if bar.pad >= len(pads):
                pads.append(curses.newpad(14, 300))

        end_y = bar.endy


def redoBar(pad):
    endy = score[current_bar].redoY()
    bar = current_bar + 1

    while bar < len(score) and endy != score[bar].y:
        score[bar].shiftBar(endy - score[bar].y)

        endy = score[bar].endy
        bar += 1

    drawEntireScore(score)
    navigateToNote()


def shiftElementsRight(pad, change):
    global current_chord
    global current_bar

    beat = getCurrentBeat()

    index = beat.getChordIndex(current_chord)
    for chordIndex in range(index + 1, len(getCurrentBeat().chords)):
        beat.chords[chordIndex].shiftChord(change)

    # shift all remaining beats in current bar
    for i in range(current_beat + 1, beats):
        score[current_bar].beats[i].shiftBeat(change)

    score[current_bar].endy = score[current_bar].beats[-1].y + 4

    # shift all remaining bars
    for i in range(current_bar + 1, len(score)):
        score[i].shiftBar(change)

    redoAllYs(score)

    for i in range(current_bar, len(score)):
        drawBar(i)

    pad.addstr(0, 0, str([b.y for b in score]))

def decLength(pad):
    global current_chord
    global current_note
    global current_beat

    if current_chord.length == 4 or current_chord.length == 3:
        current_chord.length -= 1
    else:
        current_chord.length /= 2

    # Current chord is the newly created half note
    current_chord = getCurrentBeat().halfChord(current_chord)
    current_note = current_chord.notes[0]

    # get the next chord in the bar
    [beat, nextChord] = score[current_bar].getNextChord(current_beat, current_chord)

    # If the next chord is not far enough from the newly created current chord, shift it along
    if nextChord and (nextChord.y < current_chord.y + 4):
        shiftElementsRight(pad, 5 - (nextChord.y - current_chord.y))
        pad.addstr(0, 0, str(nextChord.y))


    # drawBar(current_bar)
    drawEntireScore(score)
    navigateToNote()

def incLength():
    global current_chord

    if current_chord.length == 2 or current_chord.length == 3:
        current_chord.length += 1
        overrideChords(1)
        
    else:
        overrideChords(current_chord.length)
        current_chord.length *= 2
    
    drawBar(current_bar)
    navigateToNote()


# A chord has been doubled (current_chord)
# Delete next chords
def overrideChords(space):

    nextChord = getCurrentBeat().getNextChord(current_chord)

    # If chords within the current beat can be deleted:
    while space > 0 and nextChord:
    
        space -= nextChord.length
        temp = getCurrentBeat().getNextChord(nextChord)

        if space >= 0:
            getCurrentBeat().deleteChord(nextChord)

        # If the chord deleted was too large (needs to get shortened)
        else:
            remainderChord = nextChord.duplicateChord()
            remainderChord.length = abs(space)

            index = getCurrentBeat().getChordIndex(current_chord)
            getCurrentBeat().addChord(index + 1, remainderChord)

        nextChord = temp

    nextBeat = score[current_bar].getNextBeat(getCurrentBeat())

    # If there are still chords to delete, move on to the next Beats
    # TODO: what if its eating 1 of a note thats length 2? Beat after will have to contend w that
    while space > 0 and nextBeat:

        while nextBeat.empty:
            nextBeat = score[current_bar].getNextBeat(nextBeat)

        nextChord = nextBeat.chords[0]

        while space > 0 and nextChord:
            space -= nextChord.length
            temp = nextBeat.getNextChord(nextChord)

            if space >= 0:
                nextBeat.deleteChord(nextChord)

            else:
                remainderChord = nextChord.duplicateChord()
                remainderChord.length = abs(space)
                
                nextBeat.addChord(0, remainderChord)

            nextChord = temp

        nextBeat = score[current_bar].getNextBeat(getCurrentBeat())

    # TODO: if space still >0 and no more beats in bar, move onto next Bar
    # TODO: refactor all the duplicated code together (using Bar.py's getNextChord() i think)

def getCurrentPad():
    return pads[score[current_bar].pad]

def getCurrentCoords():
    return [current_note.pitch, current_chord.y]

def toggleStaccato(pad):
    global current_chord

    current_chord.toggleStaccato()
    drawChord(pad, current_chord)
    navigateToNote()

def toggleAccent(pad):
    global current_chord

    current_chord.toggleAccent()
    drawChord(pad, current_chord)
    navigateToNote()

def makeFlat(pad):
    global current_note

    current_note.toggleFlat()
    drawChord(pad, current_chord)
    navigateToNote()

def makeSharp(pad):
    global current_note

    current_note.toggleSharp()
    drawChord(pad, current_chord)
    navigateToNote()

def makeAccidental(pad):
    global current_note

    current_note.toggleNatural()

    drawChord(pad, current_chord)
    navigateToNote()

def navigateAwayFrom():

    pad = getCurrentPad()
    [x, y] = getCurrentCoords()

    if x == -1 or x == None:
        for i in range(4, 8):
            pad.chgat(i, y, 1, curses.color_pair(2))
    else:
        if current_chord.length >= 2:
            pad.chgat(x, y, 2, curses.color_pair(2)) 
        else:
            pad.chgat(x, y, 2, curses.color_pair(2))    

def navigateToNote():

    pad = getCurrentPad()
    [x, y] = getCurrentCoords()
    if x:
        if x != -1:
            if current_chord.length >= 2:
                pad.chgat(x, y, 2, curses.color_pair(1))
            else:
                pad.chgat(x, y, 2, curses.color_pair(1))
        else:
            for i in range(4, 8):
                pad.chgat(i, y, 1, curses.color_pair(1))

def getCurrentBeat():
    return score[current_bar].beats[current_beat]

def horizontalNavigation(pad, dir):
    global current_bar
    global current_beat
    global current_chord
    global current_note

    navigateAwayFrom()

    if dir == "KEY_RIGHT":
        [current_beat, newChord] = score[current_bar].getNextChord(current_beat, current_chord)
        change = 1

    else:
        [current_beat, newChord] = score[current_bar].getPrevChord(current_beat, current_chord)
        change = -1

    # There was a next/previous chord in the bar
    if newChord:

        current_chord = newChord
        current_note = current_chord.notes[0]


    # else, move to the next bar
    else:
        newBar = current_bar + change

        # The next bar exists
        if newBar >= 0 and newBar < len(score):
            current_bar = newBar
            if dir == "KEY_RIGHT":

                current_beat = 0  
                current_chord = getCurrentBeat().chords[0]
                current_note = current_chord.notes[0]
            
            else:
                current_beat = len(score[current_bar].beats) - 1
                while getCurrentBeat().empty:
                    current_beat -= 1

                current_chord = getCurrentBeat().LastChord()
                current_note = current_chord.notes[0]

        # A new bar must be created
        elif newBar >= 0:

            lastBeat = score[-1].beats[-1]
            # lastCoord = lastBeat.y if lastBeat.empty else lastBeat.chords[-1].y

            padIndex = score[current_bar].pad

            score.append(Bar(score[-1].endy, beats))
            current_bar = len(score) - 1
            current_beat = 0
            current_chord = getCurrentBeat().chords[0]
            current_note = current_chord.notes[0]

            score[current_bar].pad = padIndex

            # If the current bar overflows off the screen
            if score[current_bar].endy >= stdscr_width - 3:
                redoAllYs(score)
                drawEntireScore(score)
            else:
                drawBar(newBar)

    navigateToNote()

# Cursor navigation vertically (within a chord)
def verticalNavigation(pad, dir):
    global current_note
    global current_chord

    if dir == "KEY_UP":
        add = -1
    else:
        add = 1

    if current_chord and current_note:
        if current_chord.getOtherNote(current_note, add):
            current_note = current_chord.getOtherNote(current_note, add)

    drawChord(pad, current_chord)
    navigateToNote()

# TODO: deal with a note already being in that position
def transpose(direction, stave_pad, change):
    global current_note
    global current_chord

    # current_chord and current_note are not None
    if current_note.pitch != -1:
            
        if direction == "up":
            newPitch = current_note.pitch - change
        else:
            newPitch = current_note.pitch + change

        # If new pitch is outside valid stave height
        if newPitch < 0 or newPitch > 13:
            return

        current_chord.removeNote(current_note)
        current_note = current_chord.addNote(newPitch)
            
        drawChord(stave_pad, current_chord)
        navigateToNote()

# Get the coordinate of the currently selected note
def getCurrentCoords():
    global current_note
    global current_chord

    y = current_chord.y
    x = current_note.pitch
    return [x, y]

def removeNote(pad):
    global current_chord
    global current_note

    if not current_chord.rest:
        current_note = current_chord.removeNote(current_note)
        drawChord(pad, current_chord)

        navigateToNote()

def parseNote(stave_pad, note):
    global current_chord
    global current_note

    note_code = ord(note)
    lowercase_note = note.lower()
    x = note_dict[lowercase_note]

    navigateAwayFrom()

    if not current_chord.rest:
        
        # If regular note (Replace entire chord)
        if note_code >= 97 and note_code <= 103:
            current_note = current_chord.replaceChord(x)

        # If SHIFT + note
        elif note_code >= 65 and note_code <= 71:
            current_note = current_chord.addNote(x)
    else:
        # Current chord is a rest
        newChord = Chord(x, current_chord.length, current_chord.y)

        index = getCurrentBeat().getChordIndex(current_chord)
        getCurrentBeat().addChord(index, newChord)

        current_chord = newChord
        current_note = current_chord.notes[0]

    drawChord(stave_pad, current_chord)
    navigateToNote()

def drawChord(pad, chord):

    y = chord.y

    Draw.emptyStaveRegion(pad, y)

    if not chord.rest:
        notes = chord.notes
        noteCoords = []

        for note in notes:
            
            noteCoords.append(note.pitch)
            if chord.length >= 2:
                string = "❨❩"
            else:
                string = "\u26AA"

            pad.addstr(note.pitch, y, string, curses.color_pair(2))
            Draw.drawAttributes(pad, note, chord)

        # Adding stems
        furthestdist = 0
        for n in noteCoords:
            dist = n - 5
            if abs(dist) > abs(furthestdist):
                furthestdist = dist

        noteCoords.sort()
        noteRange = abs(noteCoords[0] - noteCoords[-1])

        if furthestdist > 0: # Stem on the right, going up
            side = y + 1
            start = noteCoords[0] - 6

            drawChordAttributes(pad, chord, noteCoords[-1], 1)
        else: # Stem on the left, going down
            side = y
            start = noteCoords[0]

            drawChordAttributes(pad, chord, noteCoords[0], -1)

        # Draw stem
        if chord.length != 4:
            for i in range(noteRange + 5):
                x = start + i + 1
                if x not in noteCoords and x >= 0 and x <= 13:
                    pad.addstr(x, side, "\u2502")


            if chord.length < 1:

                subdivision = 1 / chord.length
                lines = int(math.log(subdivision, 2))

                if furthestdist > 0: #on the right, going up (at the top)
                    start = start + 1
                    char = "⎞"
                else:
                    start = noteRange + 6 + start - lines
                    char = "⎠"

                for i in range(lines):
                    pad.addstr(start + i, side + 1, char)

    else:
        Draw.drawRest(pad, chord)

    pad.refresh(0, 0, 1, 1, stave_height, stdscr_width - 2)

def drawChordAttributes(pad, chord, lastNote, dir):

    current_coord = lastNote + dir

    if chord.staccato:
        pad.addstr(current_coord, chord.y, "•")
        current_coord = current_coord + dir
    if chord.accent:
        pad.addstr(current_coord, chord.y, ">")

def drawBar(barIndex):
        global pads

        bar = score[barIndex]
        pad = pads[bar.pad]

        start_y = bar.y
        end_y = bar.endy

        length = end_y - start_y + 1

        for i in range(0, 13):
            pad.addstr(i, start_y, " " * (length + 2))


        pad.addstr(1, start_y, "┰" + ("\u2500" * length) + "\u2512")
        pad.addstr(2, start_y, "\u2503" + (" " * length) + "\u2503")
        pad.addstr(3, start_y, "\u2520" + ("\u2500" * length) + "\u2528")
        pad.addstr(4, start_y, "\u2503" + (" " * length) + "\u2503")
        pad.addstr(5, start_y, "\u2520" + ("\u2500" * length) + "\u2528")
        pad.addstr(6, start_y, "\u2503" + (" " * length) + "\u2503")
        pad.addstr(7, start_y, "\u2520" + ("\u2500" * length) + "\u2528")
        pad.addstr(8, start_y, "\u2503" + (" " * length) + "\u2503")
        pad.addstr(9, start_y, "┸" + ("\u2500" * length) + "\u251A")

        if start_y == 0:
            pad.addstr(1, start_y, "\u250E")
            pad.addstr(9, start_y, "\u2516")


        for beat in bar.beats:
            drawBeat(pad, beat)

        if barIndex == 0:
            Draw.drawBeginning(pad)

        # pad.refresh(0, 0, 1, 1, stave_height, stdscr_width - 2)
        return

def drawBeat(pad, beat):

    if beat.empty:
        pass
    if beat.restBeat():
        Draw.drawRest(pad, beat.chords[0])
    else:
        for chord in beat.chords:
            drawChord(pad, chord)

def drawEntireScore(score):
    for i in range(len(score)):
        drawBar(i)
    
wrapper(main)