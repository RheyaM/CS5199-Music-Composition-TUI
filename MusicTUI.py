import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle

from Objects.Bar import Bar
from Objects.Beat import Beat
from Objects.Chord import Chord
from Objects.Note import Note
from Draw import Draw
from Representation import Representation

import math

# TODO: if navigateToNote() always comes after drawChord then just put it in drawChord
# TODO: be able to display key

file = ""

note_dict = {"c": 11, "d": 10, "e": 9, "f": 8, "g": 7, "a": 6, "b": 5}
all_notes = ["c", "C", "d", "D", "e", "E", "f", "F", "g", "G", "a", "A", "b", "B"]

beats = 4

# First bar starts at y = 13 and there are 4 beats in a bar
score = [Bar(11, beats), Bar(37, beats)]
pads : list[curses.window] = []

current_bar : int = 0 # Index of current bar object in score[]
current_beat : int = 0 # Index of current beat object in current_bar.beats
current_chord : Chord = score[0].beats[0].chords[0] # Chord object
current_note : Note = current_chord.notes[0] # Note object

# stave_height - going to restrict how many octaves we can use
stave_height : int = 13

stdscr_width : int = 0
stdscr_height : int = 0

# TODO: allow higher/lower notes past the stave
# TODO: Is it better to transpose with - and +?
# TODO: draw rests in drawChord() since rests are chords now


def main(stdscr : curses.window) -> None:
    global stdscr_width
    global stdscr_height
    
    setUpTUI(stdscr)

    stdscr_height, stdscr_width = stdscr.getmaxyx()

    textbox = setUpTextbox()
    hints = setUpHints()
    stave_pad = getCurrentPad()

    textbox.refresh(0, 0, stdscr_height - 6, 0, stdscr_height - 4, stdscr_width - 2)
    hints.refresh(0, 0, stdscr_height - 3, 0, stdscr_height - 1, stdscr_width - 2)
    stave_pad.refresh(0, 0, 1, 1, stave_height, stdscr_width - 2)

    open("keylog.txt", "a").write("\n#####################################")

    while True:

        char = stdscr.getkey()

        match char:
            case "q":
                # save(textbox)
                break

            case "\x7f":
                removeNote(stave_pad)

            case "\n":
                # textbox.addstr(1, 0, Representation.scoreToString(score, beats))
                pass

            case "KEY_UP" | "KEY_DOWN":
                verticalNavigation(stave_pad, char)

            case "KEY_RIGHT" | "KEY_LEFT":
                horizontalNavigation2(char)

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
                redoAllPads(score)
                drawEntireScore()
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

        refreshStavePad()
        stave_pad = getCurrentPad()

        open("keylog.txt", "a").write("\n" + char)

def setUpTUI(stdscr: curses.window) -> None:

    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_WHITE, -1)
    curses.curs_set(0)

    stdscr.clear()
    
    # Creating and adding the first stave pad to the screen
    stave_pad = curses.newpad(15, 300)

    stdscr.refresh()
    pads.append(stave_pad)
    
    # Adding the empty stave to the pad
    drawEntireScore()
    navigateToNote()
    

def setUpTextbox() -> curses.window:
    textbox = curses.newpad(3, stdscr_width)
    textbox.addstr(1, 0, Representation.scoreToString(score, beats))

    return textbox

def setUpHints() -> curses.window:
    hints = curses.newpad(3, 300)
    Draw.drawHints(hints, stdscr_width)
    
    return hints

def refreshStavePad() -> int:
    x : int = 1
    for pad in pads:
        if x < stdscr_height - 5:
            pad.refresh(0, 0, x, 1, min(stave_height + x, stdscr_height - 6), stdscr_width - 2)
        x += 13

def load(stdscr):
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
    drawEntireScore()
    refreshStavePad()

def save(stdscr : curses.window, textbox : curses.window):

    # Writing the stave itself to the .txt file:
    # for pad in pads:
    #     [y, x] = pad.getmaxyx()
    #     with open("test.txt", "a") as myfile:
    #         for i in range(y):
    #             myfile.write("\n" + pad.instr(i, 0).decode("utf-8"))

    if file != "":
        with open(file, "a") as myfile:
            myfile.write("\n" + textbox.instr(1, 0).decode("utf-8"))

        myfile.close()
    else:
        saveAs(stdscr, textbox)

def saveAs(stdscr, textbox):
    open("log.txt", "a").write("\nIn saveAs")
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
            myfile.write(textbox.instr(1, 0).decode("utf-8"))
        myfile.close()
        file = text + ".txt"

    stdscr.clear()
    textinput.erase()

    stdscr.refresh()

# TESTING PURPOSES
# print the y-coordinates of all chords in the current bar
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
# TODO: change this so it only redoes ys from the changed bar. Which could be the start
def redoAllPads(score):
    global pads
    open("log.txt", "a").write("\nredoAllPads()")

    end_y = 11
    currentPad = 0

    for bar in score:

        # If the bar doesn't start where the previous ended, shift it left/right
        if bar.y != end_y and bar.pad == currentPad:
            bar.shiftBar(end_y - bar.y)
            

        # If the bar is overflowing, update its pad, y, and endy values
        if bar.endy >= stdscr_width - 3:
            bar.pad += 1
            bar.shiftBar(bar.y * -1)

            if bar.pad >= len(pads):
                pads.append(curses.newpad(14, 300))


        currentPad = bar.pad
        end_y = bar.endy



def shiftElementsRight(pad, change):
    open("log.txt", "a").write("\nIn shiftElementsRight. Change:" + str(change))
    global current_chord
    global current_bar

    beat = getCurrentBeat()

    index = beat.getChordIndex(current_chord)
    for chordIndex in range(index + 1, len(getCurrentBeat().chords)):
        beat.chords[chordIndex].shiftChord(change)

    # shift all remaining beats in current bar
    for i in range(current_beat + 1, beats):
        score[current_bar].beats[i].shiftBeat(change)

    score[current_bar].endy += change

    redoAllPads(score)

    for i in range(current_bar, len(score)):
        drawBar(i)

def decLength(pad):
    global current_chord
    global current_note
    global current_beat

    open("log.txt", "a").write("\n" + str(current_chord.length))

    if current_chord.length <= 0.0625:
        return
    
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
        open("log.txt", "a").write("\nNext chord not far enough from newly created chord")
        shiftElementsRight(pad, 5 - (nextChord.y - current_chord.y))

    # If its the last chord
    if current_chord.y + 5 > score[current_bar].endy:
        open("log.txt", "a").write("\nOvertook bar end")
        shiftElementsRight(pad, 5 - (score[current_bar].endy - current_chord.y))
    
    # If its not the last bar and the next bar doesn't start where it should 
    if current_bar < len(score) - 1 and score[current_bar + 1].y != score[current_bar].endy:
        open("log.txt", "a").write("\nNext bar doesn't start where it should")
        redoAllPads(score)


    # drawBar(current_bar)
    drawEntireScore()
    navigateToNote()

def incLength():
    global current_chord

    open("log.txt", "a").write("\nIn incLength()")

    if current_chord.length == 2 or current_chord.length == 3:
        current_chord.length += 1
        overrideChords(1)
        
    else:
        overrideChords(current_chord.length)
        current_chord.length *= 2

    redoAllPads(score)
    drawBarsFrom(current_bar)
    navigateToNote()


# A chord has been doubled (current_chord)
# Delete next chords
def overrideChords(space):
    open("log.txt", "a").write("\nIn overrideChords()")

    nextChord = getCurrentBeat().getNextChord(current_chord)

    # If chords within the current beat can be deleted:
    while space > 0 and nextChord:
    
        space -= nextChord.length
        temp = getCurrentBeat().getNextChord(nextChord)

        # If chords within the current beat can be deleted:
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


def horizontalNavigation(dir):
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

    # There is a next/previous chord in the bar
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

            padIndex = score[current_bar].pad

            score.append(Bar(score[-1].endy, beats))
            current_bar = len(score) - 1
            current_beat = 0
            current_chord = getCurrentBeat().chords[0]
            current_note = current_chord.notes[0]

            score[current_bar].pad = padIndex

            # If the current bar overflows off the screen
            if score[current_bar].endy >= stdscr_width - 3:
                redoAllPads(score)
                drawEntireScore()

            else:
                drawBar(newBar)

    navigateToNote()

def horizontalNavigation2(dir):
    global current_bar
    global current_beat
    global current_chord
    global current_note

    navigateAwayFrom()

    if dir == "KEY_RIGHT":
        [nextBar, nextBeat, nextChord] = moveRight(current_bar, current_beat, current_chord)

    else:
        [nextBar, nextBeat, nextChord] = moveLeft(current_bar, current_beat, current_chord)

    if nextChord:
        current_bar = nextBar
        current_beat = nextBeat
        current_chord = nextChord
        current_note = current_chord.notes[0]

    # A new Bar must be created
    elif dir == "KEY_RIGHT":

        padIndex = score[current_bar].pad
        
        score.append(Bar(score[-1].endy, beats))
        current_bar = len(score) - 1
        current_beat = 0
        current_chord = getCurrentBeat().chords[0]
        current_note = current_chord.notes[0]

        score[current_bar].pad = padIndex

        # If the current bar overflows off the screen
        if score[current_bar].endy >= stdscr_width - 3:
            redoAllPads(score)
            drawEntireScore()

        else:
            drawBar(score[-1])


    navigateToNote()


# Given a bar, beat, and chord, return the previous chord, regardless of which bar it's in
# Ignores empty beats
def moveLeft(barIndex : int, beatIndex : int, chord : Chord):

    # Check the current Bar
    [prevBeat, prevChord] = score[barIndex].getPrevChord(beatIndex, chord)

    if prevChord:
        return [barIndex, prevBeat, prevChord]

    # Is there a previous Bar?
    if barIndex > 0:
        [prevBeat, prevChord] = score[barIndex - 1].getLastChord()
        return [barIndex - 1, prevBeat, prevChord]

    # If not, return None
    return [None, None, None]


# Given a bar, beat, and chord, return the next chord along, regardless of which bar it's in
# Ignores empty beats
def moveRight(barIndex : int, beatIndex : int, chord : Chord) -> list[int, int, Chord]:

    # Check the current Bar
    [nextBeat, nextChord] = score[current_bar].getNextChord(beatIndex, chord)

    if nextChord:
        return [barIndex, nextBeat, nextChord]

    # Is there a next Bar? Then return the first chord of that Bar
    if barIndex < len(score) - 1:
        return [barIndex + 1, 0, score[barIndex + 1].beats[0].chords[0]] # The first chord of a bar cannot be empty
    
    # If not, return None
    return [None, None, None]
    

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

# Get the coordinates of the currently selected note
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
        noteCoords = Draw.drawNotes(pad, chord)
        drawStem(pad, chord, noteCoords)

    else:
        Draw.drawRest(pad, chord)

    pad.refresh(0, 0, 1, 1, stave_height, stdscr_width - 2)

def drawStem(pad : curses.window, chord : Chord, noteCoords : list[int]):
    y = chord.y
    furthestdist = determineFurthestDist(noteCoords)

    if furthestdist > 0: # Stem on the right, going up
        side = y + 1
        start = noteCoords[0] - 6

        drawChordAttributes(pad, chord, noteCoords[-1], 1)
    else: # Stem on the left, going down
        side = y
        start = noteCoords[0]

        drawChordAttributes(pad, chord, noteCoords[0], -1)

    noteRange = abs(noteCoords[0] - noteCoords[-1])

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

def determineFurthestDist(noteCoords : list[int]):
    furthestdist = 0
    for n in noteCoords:
        dist = n - 5
        if abs(dist) > abs(furthestdist):
            furthestdist = dist

    noteCoords.sort()

    return furthestdist

def drawChordAttributes(pad, chord, lastNote, dir):

    current_coord = lastNote + dir

    if chord.staccato:
        pad.addstr(current_coord, chord.y, "•")
        current_coord = current_coord + dir
    if chord.accent:
        pad.addstr(current_coord, chord.y, ">")

def drawBarsFrom(barIndex):
    for i in range(barIndex, len(score)):
        drawBar(i)

def drawBar(barIndex):

        bar = score[barIndex]
        pad = pads[bar.pad]

        start_y = bar.y
        end_y = bar.endy

        length = end_y - start_y - 1

        for i in range(0, 13):
            pad.addstr(i, start_y, " " * (length + 2))

        pad.addstr(1, start_y, "┰" + ("\u2500" * length) + "\u2512")
        for i in range(2, 9, 2):
            pad.addstr(i, start_y, "\u2503" + (" " * length) + "\u2503")
        for i in range(3, 8, 2):
            pad.addstr(i, start_y, "\u2520" + ("\u2500" * length) + "\u2528")
        pad.addstr(9, start_y, "┸" + ("\u2500" * length) + "\u251A")

        if start_y == 0:
            pad.addstr(1, start_y, "\u250E")
            pad.addstr(9, start_y, "\u2516")

        for beat in bar.beats:
            drawBeat(pad, beat)

        if barIndex == 0:
            Draw.drawBeginning(pad)

        # If a bar is the last on its pad, or the last in score, remove any further characters
        if (barIndex < len(score) - 1 and score[barIndex + 1].pad > score[barIndex].pad) or barIndex == len(score) - 1:
            [height, width] = pad.getmaxyx()
            for i in range(height):
                pad.move(i, end_y + 3)
                pad.clrtoeol()


def drawBeat(pad : curses.window, beat : Beat):

    if beat.empty:
        pass
    if beat.restBeat():
        Draw.drawRest(pad, beat.chords[0])
    else:
        for chord in beat.chords:
            drawChord(pad, chord)

def drawEntireScore():
    for i in range(len(score)):
        drawBar(i)
    
wrapper(main)