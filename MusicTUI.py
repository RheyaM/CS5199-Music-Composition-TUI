import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle

from Objects.Bar import Bar
from Objects.Chord import Chord
from Objects.Note import Note
from Draw import Draw
from Representation import Representation
from Playback import Playback

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
visible : list[int] = [] # Indexes of pads which are currently fully visible in pads

current_bar : int = 0 # Index of current bar object in score[]
current_chord : Chord = score[0].chords[0] # Chord object
current_note : Note = current_chord.notes[0] # Note object

# stave_height - going to restrict how many octaves we can use
stave_height : int = 13

stdscr_width : int = 0
stdscr_height : int = 0

# TODO: allow higher/lower notes past the stave
# TODO: Is it better to transpose with - and +?

def main(stdscr : curses.window) -> None:
    global stdscr_width
    global stdscr_height

    stdscr_height, stdscr_width = stdscr.getmaxyx()
    
    setUpTUI(stdscr)

    textbox = setUpTextbox()
    hints = setUpHints()
    stave_pad = getCurrentPad()
    visible.append(0)
    playPad = None

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
                horizontalNavigation(char)

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
                decLength()

            case "]":
                incLength()

            case "s":
                save(stdscr, textbox)

            case "S":
                saveAs(stdscr, textbox)

            case "p":
                playPad = playAudio(score, file.replace(".txt", ""))

            case "v":
                Playback.stopAudio()
                playPad = None

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

        # if not Playback.checkAudio():
        #     playPad.erase()
        #     playPad = None

        # if playPad:
        #     playPad.refresh(0, 0, stdscr_height - 4, stdscr_width - 35, stdscr_height - 1, stdscr_width - 1)
            
        refreshVisiblePads(stdscr)
        stave_pad = getCurrentPad()

        open("keylog.txt", "a").write("\n" + char)

# TODO: cut the chords of the current bar to only play from current_chord
def playAudio(score, file):
    playPad = curses.newpad(4, 20)
    playPad.addstr(1, 1, "Playing... 'v' to Pause")


    subscore = score[current_bar::]
    Playback.createAudio(subscore, file)

    return playPad

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

# Shifting the visible pads based on the current pad
def shiftVisible(visible : list[int], currentPadIndex : int) -> None:

    # If the current pad is already visible
    if currentPadIndex in visible:
        return

    if currentPadIndex < visible[0]:
        toRemove = -1
    else:
        toRemove = 0

    # Add the new pad to the visible pads
    visible.append(currentPadIndex)
    visible.sort()

    # If there are too many visible pads for the current stave_height, remove one
    if len(visible) > (stdscr_height - 6)/stave_height:
        visible.pop(toRemove)

    return visible

def refreshVisiblePads(stdscr):

    x : int = 1

    # Refresh all visible staves
    for index in visible:
        pad = pads[index]
        pad.refresh(0, 0, x, 1, min(stave_height + x, stdscr_height - 6), stdscr_width - 2)

        x += stave_height

    # If there is space for a partly visible stave
    if x < stdscr_height - 5 and visible[-1] <= len(pads) - 2:
        pad = pads[visible[-1] + 1]
        pad.refresh(0, 0, x, 1, min(stave_height + x, stdscr_height - 6), stdscr_width - 2)

    else:
        for i in range(x, stdscr_height - 6):
            stdscr.move(i, 0)
            stdscr.clrtoeol()


def load(stdscr):
    global file
    global score
    global current_bar
    global current_chord
    global current_note
    global visible

    stdscr.clear()
    for pad in pads:
        pad.clear()

    stdscr.addstr(stdscr_height - 7, 1, "Input your file name")
    stdscr.addstr(stdscr_height - 1, 1, "^G: Confirm          To cancel, leave empty")

    textinput = curses.newwin(2, 41, stdscr_height - 5, 2)
    box = Textbox(textinput)
    rectangle(stdscr, stdscr_height - 6, 1, stdscr_height - 3, 43)
    stdscr.refresh()

    box.edit()
    text = box.gather().replace("\n","").replace(" ", "")

    try:
        with open(text, "r") as myfile:
            string = myfile.read().replace("\n", "").replace(" ", "")
        myfile.close()

        file = text

        score = Representation.stringToScore(string)

    except Exception as e:
        open("log.txt", "a").write("\n" + str(e))

    current_bar = 0
    current_chord = score[current_bar].chords[0]
    current_note = current_chord.notes[0]
    
    redoAllPads(score)

    open("log.txt", "a").write(str(score))
    drawEntireScore()
    navigateToNote()

    visiblePadsNum = (stdscr_height - 6)//stave_height
    visible = list(range(0, len(pads) - 1))[:visiblePadsNum]
    

    refreshVisiblePads(stdscr)



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
    text = box.gather().replace("\n", "").replace(" ", "")


    if text != "":
        with open(text + ".txt", "a") as myfile:
            myfile.write(textbox.instr(1, 0).decode("utf-8"))
        myfile.close()
        file = text + ".txt"

    stdscr.clear()
    textinput.erase()

    stdscr.refresh()

# TODO: quaver moving to next bar needs whatever is there to split in half??
# Actually musescore doesn't allow shifting if they're not the same length...
# Or if they're in different bars. Maybe i only shift if same length...
def shift(pad, dir):
    global current_bar
    global current_beat
    global current_chord
    global current_note

    bar = score[current_bar]

    index = bar.chords.index(current_chord)

    if dir == "Right":
        [newBar, toSwitch] = moveRight(current_bar, current_chord)
    else:
        [newBar, toSwitch] = moveLeft(current_bar, current_chord)

    # If there is a next/previous chord (regardless of bar)
    if toSwitch:

        # They must be the same length
        if toSwitch.length != current_chord.length:
            return

        newIndex = score[newBar].chords.index(toSwitch)

        score[current_bar].chords[index] = toSwitch
        score[newBar].chords[newIndex] = current_chord


        # Updating the y coordinates of the relevant chords
        temp = current_chord.y
        current_chord.y = toSwitch.y
        toSwitch.y = temp

        current_bar = newBar

        drawChord(pad, toSwitch)
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

            # Update pad value of all bars that come after
            index = score.index(bar)
            for b in score[index + 1 ::]:
                b.pad += 1


        currentPad = bar.pad
        end_y = bar.endy

def shiftElementsRight(change):
    open("log.txt", "a").write("\nIn shiftElementsRight. Change:" + str(change))
    global current_chord
    global current_bar

    bar = score[current_bar]

    index = bar.chords.index(current_chord)
    for chordIndex in range(index + 1, len(bar.chords)):
        bar.chords[chordIndex].shiftChord(change)

    score[current_bar].endy += change

    redoAllPads(score)

    for i in range(current_bar, len(score)):
        drawBar(i)

def decLength():
    global current_chord
    global current_note

    # Do not decrease the length of a tied chord
    if current_chord.tie:
        return

    # Minimum chord length
    if current_chord.length <= 0.0625:
        return

    bar = score[current_bar]

    # Current chord is the newly created half note
    current_chord = bar.halfChord(current_chord)
    current_note = current_chord.notes[0]

    # get the next chord in the bar
    nextChord = score[current_bar].getNextChord(current_chord)

    # If the next chord is not far enough from the newly created current chord, shift it along
    if nextChord and (nextChord.y < current_chord.y + 4):
        shiftElementsRight(5 - (nextChord.y - current_chord.y))

    # If its the last chord and overtook the end of the bar
    if current_chord.y + 5 > score[current_bar].endy:
        shiftElementsRight(5 - (score[current_bar].endy - current_chord.y))
    
    # If its not the last bar and the next bar doesn't start where it should 
    if current_bar < len(score) - 1 and score[current_bar + 1].y != score[current_bar].endy:
        redoAllPads(score)

    # drawBar(current_bar)
    drawEntireScore()
    navigateToNote()

def incLength():
    global current_chord

    open("log.txt", "a").write("\nIn incLength()")

    # If it will form a tie, the length shouldn't change
    index = score[current_bar].chords.index(current_chord)

    # If the current chord is tied to the next, any change to length should be done to the last chord
    # (For now)
    if current_chord.tie:
        return

    # Rests do not form ties
    if index == len(score[current_bar].chords) - 1 and current_chord.rest:
        return

    if current_chord.length == 2 or current_chord.length == 3 or current_chord.length == 4:
        if index != len(score[current_bar].chords) - 1:
            current_chord.length += 1
        overrideChords(current_bar, current_chord, 1)
        
    else:
        length = current_chord.length
        # If it's not the last chord in the bar, increase the length
        if index != len(score[current_bar].chords) - 1:
            current_chord.length *= 2
            
        overrideChords(current_bar, current_chord, length)
        
    redoAllPads(score)
    drawBarsFrom(current_bar)
    navigateToNote()

# overrideChords should be: starting from this chord (don't incl it), eat this much space.
# space <= 1, always
def overrideChords(barIndex : int, chord, space : float):

    while space > 0:
        [nextBar, nextChord] = moveRight(barIndex, chord)
        index = score[barIndex].chords.index(chord)

        # If there is no next chord to eat, create a newBar
        if nextChord is None:
            newBar = Bar(score[-1].endy, beats)
            score.append(newBar)

            newChord = chord.duplicateChord()
            newChord.length = space
            newChord.y = newBar.chords[0].y

            newBar.chords.insert(0, newChord)

            overrideChords(len(score) - 1, newChord, newChord.length)

            chord.tie = True
            space = 0

        # There is another chord to eat, within the bar or in the next one
        else:
            
            if barIndex != nextBar:

                newChord = chord.duplicateChord()
                newChord.length = space
                newChord.y = score[nextBar].chords[0].y

                score[nextBar].chords.insert(0, newChord)

                chord.tie = True

            score[nextBar].chords.remove(nextChord)
            space -= nextChord.length

            # Chord eaten, and it needs a remainder
            if space < 0:

                remainderChord = nextChord.duplicateChord()
                remainderChord.length = abs(space)

                chordsToAdd = splitChord(remainderChord)
                for c in chordsToAdd:
                    score[nextBar].chords.insert(index + 1, c)

                score[nextBar].redoY()

def splitChord(chord : Chord) -> list[Chord]:
    chords = []
    length = chord.length

    if length == 1 or length == 2 or length == 3 or length == 4:
        return [chord]

    while length > 0:
        newChord = chord.duplicateChord()

        newLength = math.floor(length)
        if newLength == 0:

            power = math.log(length, 2)
            if power.is_integer():
                newLength = length
            else:
                newLength = 2 ** math.floor(power)


        newChord.length = newLength
        length -= newLength

        chords.append(newChord)

    return chords


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
    open("log.txt", "a").write("\nIn navigateToNote()")

    pad = getCurrentPad()
    [x, y] = getCurrentCoords()

    if x is not None:
        if x != -1:
            if current_chord.length >= 2:
                pad.chgat(x, y, 2, curses.color_pair(1))
            else:
                pad.chgat(x, y, 1, curses.color_pair(1))
        else:
            for i in range(4, 8):
                pad.chgat(i, y, 1, curses.color_pair(1))

def horizontalNavigation(dir):
    global current_bar
    global current_chord
    global current_note

    navigateAwayFrom()

    if dir == "KEY_RIGHT":
        [nextBar, nextChord] = moveRight(current_bar, current_chord)

    else:
        [nextBar, nextChord] = moveLeft(current_bar, current_chord)

    if nextChord:
        current_bar = nextBar
        current_chord = nextChord
        current_note = current_chord.notes[0]

    # A new Bar must be created
    elif dir == "KEY_RIGHT":

        padIndex = score[current_bar].pad
        
        score.append(Bar(score[-1].endy, beats))
        current_bar = len(score) - 1
        current_chord = score[-1].chords[0]
        current_note = current_chord.notes[0]

        score[current_bar].pad = padIndex

        # If the current bar overflows off the screen
        if score[current_bar].endy >= stdscr_width - 3:
            redoAllPads(score)
            drawEntireScore()

        else:
            drawBar(-1)

    shiftVisible(visible, score[current_bar].pad)
    navigateToNote()

# Given a bar and chord, return the previous chord, regardless of which bar it's in
# Ignores empty beats
def moveLeft(barIndex : int, chord : Chord) -> list[int, Chord]:

    # Check the current Bar
    prevChord = score[barIndex].getPrevChord(chord)

    if prevChord:
        return [barIndex, prevChord]

    # Is there a previous Bar?
    if barIndex > 0:
        prevChord = score[barIndex - 1].getLastChord()
        return [barIndex - 1, prevChord]

    # If not, return None
    return [None, None]


# Given a bar and chord, return the next chord along, regardless of which bar it's in
# Ignores empty beats
def moveRight(barIndex : int, chord : Chord) -> list[int, Chord]:

    # Check the current Bar
    nextChord = score[barIndex].getNextChord(chord)

    if nextChord:
        return [barIndex, nextChord]

    # Is there a next Bar? Then return the first chord of that Bar
    if barIndex < len(score) - 1:
        return [barIndex + 1, score[barIndex + 1].chords[0]] # The first chord of a bar cannot be empty
    
    # If not, return None
    return [None, None]
    

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

        if current_chord.rest:
            [prevBar, prevChord] = moveLeft(current_bar, current_chord)
            if prevChord:
                prevChord.tie = False

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

        index = score[current_bar].chords.index(current_chord)
        score[current_bar].chords[index] = newChord

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

    for bar in score:
        for chord in bar.chords:
            if chord.tie and not chord.rest:
                Draw.drawTie(pads[bar.pad], chord)

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

        for chord in bar.chords:
            drawChord(pad, chord)

        if barIndex == 0:
            Draw.drawBeginning(pad)

        # If a bar is the last on its pad, or the last in score, remove any further characters
        if (barIndex < len(score) - 1 and score[barIndex + 1].pad > score[barIndex].pad) or barIndex == len(score) - 1:
            [height, width] = pad.getmaxyx()
            for i in range(height):
                pad.move(i, end_y + 1)
                pad.clrtoeol()

def drawEntireScore():
    for i in range(len(score)):
        drawBar(i)

    for bar in score:
        for chord in bar.chords:
            if chord.tie and not chord.rest:
                Draw.drawTie(pads[bar.pad], chord)
    
wrapper(main)