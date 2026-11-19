"""Python module providing screen painting and window creation functionality"""
import curses
import subprocess
import sys
import math
from curses import wrapper
from curses.textpad import Textbox, rectangle
from cursesmenu import CursesMenu
from Objects.Bar import Bar
from Objects.Chord import Chord
from Objects.Note import Note
from Draw import Draw
from Representation import Representation
from Playback import Playback

file : str = ""

# MIDDLE_C determines the x-coordinates of many features (rests, notes, treble clef, etc.)
# This allows easier adjustment of fixed coordinates if the maximum size of the stave is changes
MIDDLE_C : int = 9

NOTE_DICT : dict = {"c": MIDDLE_C + 7, "d": MIDDLE_C + 6, "e": MIDDLE_C + 5, "f": MIDDLE_C + 4, 
                    "g": MIDDLE_C + 3, "a": MIDDLE_C + 2, "b": MIDDLE_C + 1}
ALL_NOTES : list[str] = ["c", "C", "d", "D", "e", "E", "f", "F", "g", "G", "a", "A", "b", "B"]

beats : int = 4

key : str = "C Major"

# First bar starts at y = 13 and there are 4 beats in a bar
score : list[Bar] = [Bar(15, beats), Bar(41, beats)]
pads : list[curses.window] = []
visible : list[int] = [] # Indexes of pads which are currently fully visible in pads

current_bar : int = 0 # Index of current bar object in score[]
current_chord : Chord = score[0].chords[0] # Chord object
current_note : Note = current_chord.notes[0] # Note object

# prev_stack = for each change to the score, store the string representation
# and the current bar, chord and note
prev_stack : list[[str, int, int, int]] = [["B:4.|r1rrr|rrrr|", current_bar, 0, 0]]

# stave_height - to determine how many octaves we can use
stave_height : int = 26

stdscr_width : int = 0
stdscr_height : int = 0

string_edit_mode = False

def main(stdscr : curses.window) -> None:
    global stdscr_width
    global stdscr_height
    global prev_stack
    global key
    global string_edit_mode

    stdscr_height, stdscr_width = stdscr.getmaxyx()

    # Exit if the screen size is too small
    if stdscr_height < 20 or stdscr_width < 113:
        sys.exit("Terminal size is too small")

    set_up_tui(stdscr)

    textbox : curses.window = set_up_textbox()
    hints : curses.window = set_up_hints()
    stave_pad : curses.window = get_current_pad()
    visible.append(0)

    textbox.refresh(0, 0, stdscr_height - 6, 0, stdscr_height - 4, stdscr_width - 2)
    hints.refresh(0, 0, stdscr_height - 3, 0, stdscr_height - 1, stdscr_width - 2)
    stave_pad.refresh(3, 0, 0, 0, 14, stdscr_width - 2)

    open("keylog.txt", "a", encoding="utf-8").write("\n#####################################")

    while True:

        char : chr = stdscr.getkey()
        change_made : bool = True

        match char:
            case "q":
                break

            case "\x7f":
                remove_note(stave_pad)

            case "\n":
                # textbox.addstr(1, 0, Representation.score_to_string(score, beats))
                pass

            case "KEY_UP" | "KEY_DOWN":
                vertical_navigation(stave_pad, char)
                change_made = False

            case "KEY_RIGHT" | "KEY_LEFT":
                horizontal_navigation(char)
                change_made = False

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
                toggle_note_attribute(stave_pad, "sharp")

            case "-":
                toggle_note_attribute(stave_pad, "flat")

            case "n":
                toggle_note_attribute(stave_pad, "natural")

            case "!":
                toggle_note_attribute(stave_pad, "staccato")

            case ">":
                toggle_note_attribute(stave_pad, "accent")

            case "[":
                dec_length()

            case "]":
                inc_length()

            case "s":
                save(stdscr, textbox)
                change_made = False

            case "S":
                save_as(stdscr, textbox)
                change_made = False

            case "p":
                play_pad = play_audio()
                change_made = False

            case "v":
                Playback.stop_audio()
                play_pad = None
                change_made = False

            case "l" | "L":
                load(stdscr)

            case "z":
                prev_stack = undo()
                change_made = False

            case "m":
                export_to_lilypond()
                change_made = False

            case "t":
                time_sig = create_menu(stdscr, "time")
                change_time_signature(int(time_sig[0]))
                set_curses_modes(stdscr)

            case "k":
                key = create_menu(stdscr, "key")
                Draw.draw_entire_score(score, pads, stave_height, beats, key)
                navigate_to_note()
                set_curses_modes(stdscr)

            case "h":
                string_edit_mode = not string_edit_mode
                if string_edit_mode:
                    string_mode()

            case "KEY_RESIZE":
                stdscr_height, stdscr_width = stdscr.getmaxyx()

                # Provided the terminal size is large enough:
                if stdscr_width >= 113 and stdscr_height >= 20:
                    Draw.draw_hints(hints, stdscr_width)
                    redo_all_pads()
                    Draw.draw_entire_score(score, pads, stave_height, beats, key)
                    navigate_to_note()

                change_made = False

            case _:
                if char in ALL_NOTES:
                    parse_note(stave_pad, char)

                else:
                    stave_pad.addstr(0, 0, char)

        # If the terminal is too small, create an error message pad
        if stdscr_height < 20 or stdscr_width < 112:
            too_small = curses.newpad(stdscr_height, stdscr_width)
            too_small.addstr(stdscr_height//2, (stdscr_width // 2) - 12, "Terminal size too small")
            too_small.refresh(0, 0, 0, 0, stdscr_height, stdscr_width)
            continue

        # if a change was made to the score, the prev_stack should be updated
        if change_made:
            prev_stack = change_to_score(Representation.score_to_string(score, beats))

        textbox.clear()
        textbox.addstr(1, 0, Representation.score_to_string(score, beats))
        textbox.refresh(0, 0, stdscr_height - 6, 0, stdscr_height - 4, stdscr_width - 2)

        hints.refresh(0, 0, stdscr_height - 3, 0, stdscr_height - 1, stdscr_width - 2)

        refresh_visible_pads(stdscr)
        stave_pad = get_current_pad()

        open("keylog.txt", "a", encoding="utf-8").write("\n" + char)

def string_mode():
    """Switching to string mode"""
    global score

    writing_box = curses.newwin(2, stdscr_width - 3, stdscr_height - 5, 0)
    writing_box.addstr(Representation.score_to_string(score, beats))

    curses.curs_set(1)

    writing_box.scrollok(True)
    tb = curses.textpad.Textbox(writing_box)
    tb.insert_mode = True

    writing_box.refresh()

    tb.edit(changed_key_inputs)
    text = tb.gather().strip().replace("\n", "")

    try:
        score = Representation.string_to_score(text)

    except Exception:
        open("log.txt", "a", encoding="utf-8").write("\nstring_to_score error")

    curses.curs_set(0)

def changed_key_inputs(x):
    """Alternative integer returns for keystrokes"""
    if x == 10:
        return 7
    elif x == 127:
        return 263
    return x

def set_curses_modes(stdscr):
    """Set up curses"""
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_WHITE, -1)

    # Setting the cursor to invisible
    curses.curs_set(0)

    curses.noecho()
    curses.cbreak()

    stdscr.keypad(True)

def create_menu(stdscr, opt):
    """Creating and displaying time or key signature menus. Returns the user's choice"""

    key_list=["C Major", "G Major", "D Major", "A Major", "E Major", "B Major", "F# Major",
               "Db Major", "Ab Major", "Eb Major", "Bb Major", "F Major"]
    time_signature_list = ["2 / 4", "3 / 4", "4 / 4"]

    if opt == "key":
        chosen_list = key_list
    else:
        chosen_list = time_signature_list

    menu = CursesMenu.make_selection_menu(chosen_list,"Select an option")

    menu.show()
    menu.join()
    selection = menu.selected_option

    set_curses_modes(stdscr)

    return chosen_list[selection]

# Making a long list of chords
# TODO: account for change in beats when undoing
def change_time_signature(new_beats):
    """Change the time signature of the piece"""
    global score
    global beats
    global current_bar

    # All chords appended to one list and resorted into bars
    chord_list = []
    for bar in score:
        for chord in bar.chords:
            chord_list.append(chord)

    new_score = [Bar(0, new_beats)]
    new_score[0].empty_bar()
    bar_index = 0

    while len(chord_list) > 0:
        chord = chord_list[0]

        # Create a new bar if needed
        if bar_index == len(new_score):
            new_score.append(Bar(0, new_beats))
            new_score[-1].empty_bar()

        bar = new_score[bar_index]
        bar.chords.append(chord)

        # To preserve the current chord, note which bar it is in
        if chord == current_chord:
            current_bar = bar_index

        # If the bar length exceeds new_beats
        if bar.total_length() > new_beats:
            remainder = bar.total_length() - new_beats
            new_chord = chord.duplicate_chord()
            new_chord.length = remainder
            chords_to_add = split_chord(new_chord)

            for c in chords_to_add[:-2]:
                c.tie = True

            # TODO: is it possible for chord.length to be invalid? i.e. 1.5 length
            chord.length -= remainder
            chord.tie = True
            chord_list = chord_list[:1] + chords_to_add + chord_list[1:]

        # A bar that exceeded length will have the correct length by this point
        if bar.total_length() == new_beats:
            bar_index += 1

        chord_list.pop(0)

    # If the last bar needs to be lengthened with rests
    if bar.total_length() < new_beats:
        new_chord = Chord(-1, new_beats - bar.total_length(), 0)
        rests_to_add = split_chord(new_chord)
        bar.chords = bar.chords + rests_to_add

    for bar in new_score:
        bar.redo_y()

    beats = new_beats
    score = new_score

    redo_all_pads()
    shift_visible(0)

    Draw.draw_entire_score(score, pads, stave_height, beats, key)
    navigate_to_note()

def export_to_lilypond() -> None:
    """Calling the makeLilypond shell script to compile a pdf of the current score"""

    string = Representation.score_to_lilypond(score, beats, key)
    if file == "":
        lilypond_file = "Untitled.ly"
    else:
        lilypond_file = file.replace(".txt", "") + ".ly"

    with open(lilypond_file, "w", encoding="utf-8") as myfile:
        myfile.write(string)

    subprocess.call(["sh", "./makeLilypond.sh", lilypond_file])

def undo():
    """Revert to the previous state, including current bar, chord and note"""
    global current_bar
    global current_chord
    global current_note
    global score

    if len(prev_stack) == 1:
        return prev_stack

    [string, bar_index, chord_index, note_index] = prev_stack[-2]

    score = Representation.string_to_score(string)

    current_bar = bar_index
    current_chord = score[bar_index].chords[chord_index]
    current_note = current_chord.notes[note_index]

    redo_all_pads()
    shift_visible(score[current_bar].pad)

    Draw.draw_entire_score(score, pads, stave_height, beats, key)
    navigate_to_note()
    prev_stack.pop(-1)

    return prev_stack

def change_to_score(new_string : str) -> None:
    """Update the string textbox and the stack of previous strings"""
    global prev_stack

    # update prev_stack, keep the latest 10 changes
    current_chord_index : int = score[current_bar].chords.index(current_chord)
    chord : Chord = score[current_bar].chords[current_chord_index]
    current_note_index : int = chord.notes.index(current_note)

    prev_stack.append([new_string, current_bar, current_chord_index, current_note_index])
    prev_stack = prev_stack[-10:]

    return prev_stack

# TODO: cut the chords of the current bar to only play from current_chord
def play_audio() -> curses.window:
    """Extract the sublist of score to play, then pass to Playback class"""

    play_pad : curses.window = curses.newpad(4, 20)
    play_pad.addstr(1, 1, "Playing... 'v' to Pause")

    subscore : list[Bar] = score[current_bar::]
    Playback.create_audio(subscore, file, key)

    return play_pad

def set_up_tui(stdscr: curses.window) -> None:
    """Set up curses, stdscr, and the stave pads"""

    set_curses_modes(stdscr)

    stdscr.clear()

    # Creating and adding the first stave pad to the screen
    stave_pad : curses.window = curses.newpad(26, 300)

    stdscr.refresh()
    pads.append(stave_pad)

    Draw.draw_entire_score(score, pads, stave_height, beats, key)
    navigate_to_note()

def set_up_textbox() -> curses.window:
    """Set up the textbox for the string representation of the score"""
    textbox : curses.window = curses.newpad(3, stdscr_width)
    textbox.addstr(1, 0, Representation.score_to_string(score, beats))

    return textbox

def set_up_hints() -> curses.window:
    """Set up the pad for hints at the bottom of the TUI"""
    hints : curses.window = curses.newpad(3, 300)
    Draw.draw_hints(hints, stdscr_width)

    return hints

def shift_visible(current_pad_index : int) -> list[int]:
    """Shifting the visible pads so the current pad is visible"""

    # If the current pad is already visible
    if current_pad_index in visible:
        return

    if current_pad_index < visible[0]:
        to_remove : int = -1
        direction : int = -1
    else:
        to_remove : int = 0
        direction : int = 1

    while current_pad_index not in visible:

        to_compare : int = visible[0 if to_remove == -1 else -1]

        # Add the new pad to the visible pads
        visible.append(to_compare + direction)
        visible.sort()

        total_length = sum([get_pad_height(i) for i in range(len(visible))])
        while total_length > stdscr_height - 6:
            visible.pop(to_remove)
            total_length = sum([get_pad_height(i) for i in range(len(visible))])

def get_pad_height(pad_index):
    """Calculate and return the height of the pad"""
    [top, bottom] = get_pad_min_max(pad_index)
    return bottom - top

def refresh_visible_pads(stdscr : curses.window) -> None:
    """Refreshing pads based on visible pads"""

    x : int = 0

    # Refresh all visible staves
    for index in visible:
        pad : curses.window = pads[index]
        [top, bottom] = get_pad_min_max(index)

        pad.refresh(top, 0, x, 0, min(x + (bottom - top) + 1, stdscr_height - 6), stdscr_width - 2)
        x += (bottom - top)

    # If there is space for a partly visible stave
    if x < stdscr_height - 6 and visible[-1] <= len(pads) - 2:
        pad : curses.window = pads[visible[-1] + 1]
        [top, bottom] = get_pad_min_max(visible[-1] + 1)

        pad.refresh(top, 0, x, 0, min(x + (bottom - top) + 1, stdscr_height - 7), stdscr_width - 2)

    else:
        for i in range(x, stdscr_height - 6):
            stdscr.move(i, 0)
            stdscr.clrtoeol()

def get_pad_min_max(pad_index):
    """Calculating the minimum and maximum note coordinates in a pad"""
    top = MIDDLE_C - 6
    bottom = MIDDLE_C + 7
    for bar in score:
        if bar.pad == pad_index:
            for chord in bar.chords:
                notes = chord.notes
                additional = 0
                if chord.staccato:
                    additional += 1
                if chord.accent:
                    additional += 1

                if not chord.rest and notes[0].pitch - additional < top:
                    top = notes[0].pitch - additional

                if notes[-1].pitch + additional > bottom:
                    bottom = notes[-1].pitch + additional

        if bar.pad > pad_index:
            return [top, bottom + 1]

    return [top, bottom + 1]

def load(stdscr : curses.window) -> None:
    """Loading a new score"""
    global file
    global score
    global current_bar
    global current_chord
    global current_note
    global visible
    global prev_stack

    stdscr.clear()
    for pad in pads:
        pad.clear()

    stdscr.addstr(stdscr_height - 7, 1, "Input your file name")
    stdscr.addstr(stdscr_height - 1, 1, "To cancel, leave empty")

    textinput = curses.newwin(2, 41, stdscr_height - 5, 2)
    box = Textbox(textinput)
    rectangle(stdscr, stdscr_height - 6, 1, stdscr_height - 3, 43)
    stdscr.refresh()

    box.edit(changed_key_inputs)
    text = box.gather().replace("\n","").replace(" ", "")

    try:
        with open(text, "r", encoding="utf-8") as myfile:
            string = myfile.read().replace("\n", "").replace(" ", "")
        myfile.close()

        file = text #Will include .txt

        score = Representation.string_to_score(string)
        prev_stack = []

    except FileNotFoundError as e:
        with open("log.txt", "r", encoding="utf8") as file:
            file.write("\n" + str(e))

    current_bar = 0
    current_chord = score[current_bar].chords[0]
    current_note = current_chord.notes[0]

    redo_all_pads()
    Draw.draw_entire_score(score, pads, stave_height, beats, key)
    navigate_to_note()

    shift_visible(0)

    refresh_visible_pads(stdscr)

def save(stdscr : curses.window, textbox : curses.window) -> None:
    """Save the current score to the current file name"""
    if file != "":
        with open(file, "w", encoding="utf-8") as myfile:
            myfile.write(textbox.instr(1, 0).decode("utf-8"))

        myfile.close()
    else:
        save_as(stdscr, textbox)

def save_as(stdscr : curses.window, textbox : curses.window) -> None:
    """Save the score to a given file name"""
    global file

    stdscr.clear()

    stdscr.addstr(stdscr_height - 7, 1, "Input your file name")
    stdscr.addstr(stdscr_height - 1, 1, "To cancel, leave empty")

    textinput = curses.newwin(2, 41, stdscr_height - 5, 2)
    box = Textbox(textinput)
    rectangle(stdscr, stdscr_height - 6, 1, stdscr_height - 3, 43)
    stdscr.refresh()

    box.edit(changed_key_inputs)
    text = box.gather().replace("\n", "").replace(" ", "")


    if text != "":
        with open(text + ".txt", "a", encoding="utf-8") as myfile:
            myfile.write(textbox.instr(1, 0).decode("utf-8"))
        myfile.close()
        file = text + ".txt"

    stdscr.clear()
    textinput.erase()

    stdscr.refresh()

def shift(pad : curses.window, direction : str):
    """Swapping two chords in the direction given"""
    global current_bar

    bar : Bar = score[current_bar]

    index : int = bar.chords.index(current_chord)

    if direction == "Right":
        [new_bar, to_switch] = move_right(current_bar, current_chord)
    else:
        [new_bar, to_switch] = move_left(current_bar, current_chord)

    # If there is a next/previous chord (regardless of bar)
    if to_switch:

        # They must be the same length
        if to_switch.length != current_chord.length:
            return

        new_index : int = score[new_bar].chords.index(to_switch)

        score[current_bar].chords[index] = to_switch
        score[new_bar].chords[new_index] = current_chord

        # Updating the y coordinates of the relevant chords
        temp = current_chord.y
        current_chord.y = to_switch.y
        to_switch.y = temp

        current_bar = new_bar

        Draw.draw_chord(pad, to_switch, stave_height)
        Draw.draw_chord(pad, current_chord, stave_height)
        navigate_to_note()

# TODO: only redo ys from the changed bar
def redo_all_pads():
    """Redo all y values of every bar, beat and chord to get true y values"""
    global pads

    end_y = 15
    current_pad = 0

    for bar in score:

        # If the bar doesn't start where the previous ended, shift it left/right
        if bar.y != end_y and bar.pad == current_pad:
            bar.shift_bar(end_y - bar.y)

        # If the bar is overflowing, update its pad, y, and endy values
        if bar.endy >= stdscr_width - 3:
            bar.pad += 1
            bar.shift_bar(bar.y * -1)

            if bar.pad >= len(pads):
                pads.append(curses.newpad(26, 300))

            # Update pad value of all bars that come after
            index = score.index(bar)
            for b in score[index + 1 ::]:
                b.pad += 1

        current_pad = bar.pad
        end_y = bar.endy

    pads = pads[:current_pad + 1]

def shift_elements_right(change):
    """Shift the y-coordinates of all notes in and after the current bar"""
    global current_chord
    global current_bar

    bar = score[current_bar]

    index = bar.chords.index(current_chord)
    for chord_index in range(index + 1, len(bar.chords)):
        bar.chords[chord_index].shift_chord(change)

    score[current_bar].endy += change

    redo_all_pads()

    for i in range(current_bar, len(score)):
        Draw.draw_bar(score, pads, i, stave_height, beats, key)

def dec_length():
    """Decrease the length of the current chords"""
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
    current_chord = bar.half_chord(current_chord)
    current_note = current_chord.notes[0]

    # get the next chord in the bar
    next_chord = score[current_bar].get_next_chord(current_chord)

    # If the next chord is not far enough from the newly created current chord, shift it along
    if next_chord and (next_chord.y < current_chord.y + 4):
        shift_elements_right(5 - (next_chord.y - current_chord.y))

    # If its the last chord and overtook the end of the bar
    if current_chord.y + 5 > score[current_bar].endy:
        shift_elements_right(5 - (score[current_bar].endy - current_chord.y))

    # If its not the last bar and the next bar doesn't start where it should
    if current_bar < len(score) - 1 and score[current_bar + 1].y != score[current_bar].endy:
        redo_all_pads()

    Draw.draw_entire_score(score, pads, stave_height, beats, key)
    navigate_to_note()

def inc_length():
    """Increase the length of the current chord"""

    # If it will form a tie, the length shouldn't change
    index = score[current_bar].chords.index(current_chord)

    # When chords are tied, any change to length should be done to the last chord
    if current_chord.tie:
        return

    # Rests do not form ties
    if index == len(score[current_bar].chords) - 1 and current_chord.rest:
        return

    if current_chord.length in (2, 3, 4):
        if index != len(score[current_bar].chords) - 1:
            current_chord.length += 1
        override_chords(current_bar, current_chord, 1)

    else:
        length = current_chord.length
        # If it's not the last chord in the bar, increase the length
        if index != len(score[current_bar].chords) - 1:
            current_chord.length *= 2

        override_chords(current_bar, current_chord, length)

    redo_all_pads()
    Draw.draw_bars_from(score, pads, current_bar, stave_height, beats, key)
    navigate_to_note()

# Note: the space to override will always be <= 1
def override_chords(bar_index : int, chord, space : float):
    """Given a chord and the space (length) to override, remove 
    the appropriate number of following chords."""

    while space > 0:
        [next_bar, next_chord] = move_right(bar_index, chord)
        index = score[bar_index].chords.index(chord)

        # If there is no next chord to override, create a new_bar
        if next_chord is None:
            new_bar = Bar(score[-1].endy, beats)
            score.append(new_bar)

            new_chord = chord.duplicate_chord()
            new_chord.length = space
            new_chord.y = new_bar.chords[0].y

            new_bar.chords.insert(0, new_chord)

            override_chords(len(score) - 1, new_chord, new_chord.length)

            chord.tie = True
            space = 0

        # There is another chord to override, within the bar or in the next one
        else:

            if bar_index != next_bar:

                new_chord = chord.duplicate_chord()
                new_chord.length = space
                new_chord.y = score[next_bar].chords[0].y

                score[next_bar].chords.insert(0, new_chord)

                chord.tie = True

            score[next_bar].chords.remove(next_chord)
            space -= next_chord.length

            # Chord overriden, and it needs a remainder
            if space < 0:

                remainder_chord = next_chord.duplicate_chord()
                remainder_chord.length = abs(space)

                chords_to_add = split_chord(remainder_chord)
                for c in chords_to_add:
                    score[next_bar].chords.insert(index + 1, c)

                score[next_bar].redo_y()

def split_chord(chord : Chord) -> list[Chord]:
    """Splitting chords into valid note lengths"""
    chords = []
    length = chord.length

    if length in (1, 2, 3, 4):
        return [chord]

    while length > 0:
        new_chord = chord.duplicate_chord()

        new_length = math.floor(length)
        if new_length == 0:

            power = math.log(length, 2)
            if power.is_integer():
                new_length = length
            else:
                new_length = 2 ** math.floor(power)


        new_chord.length = new_length
        length -= new_length

        chords.append(new_chord)

    return chords

def get_current_pad():
    """Return the pad of the current bar"""
    return pads[score[current_bar].pad]

def toggle_note_attribute(pad : curses.window, attr : str):
    """Toggle the note attributes"""
    match attr:
        case "sharp" | "flat" | "natural":
            current_note.toggle_attribute(attr)
        case "accent":
            current_chord.toggle_accent()
        case "staccato":
            current_chord.toggle_staccato()

    Draw.draw_chord(pad, current_chord, stave_height)
    navigate_to_note()

def navigate_away_from():
    """Remove highlight from current note"""

    pad = get_current_pad()
    [x, y] = get_current_coords()

    if x == -1 or x is None:
        for i in range(MIDDLE_C, MIDDLE_C + 4):
            pad.chgat(i, y, 1, curses.color_pair(2))
            pad.chgat(i, y + 1, 1, curses.color_pair(2))
    else:
        if current_chord.length >= 2:
            pad.chgat(x, y, 2, curses.color_pair(2))
        else:
            pad.chgat(x, y, 2, curses.color_pair(2))

def navigate_to_note():
    """Highlight the current note"""

    pad = get_current_pad()
    [x, y] = get_current_coords()

    if x is not None:
        if x != -1:
            if current_chord.length >= 2:
                pad.chgat(x, y, 2, curses.color_pair(1))
            else:
                pad.chgat(x, y, 1, curses.color_pair(1))
        else:
            if current_chord.length < 2:
                for i in range(MIDDLE_C, MIDDLE_C + 4):
                    pad.chgat(i, y, 1, curses.color_pair(1))
            else:
                pad.chgat(MIDDLE_C, y, 2, curses.color_pair(1))

def horizontal_navigation(direction):
    """Navigate horizontally: between chords"""
    global current_bar
    global current_chord
    global current_note

    navigate_away_from()

    if direction == "KEY_RIGHT":
        [next_bar, next_chord] = move_right(current_bar, current_chord)

    else:
        [next_bar, next_chord] = move_left(current_bar, current_chord)

    if next_chord:
        current_bar = next_bar
        current_chord = next_chord
        current_note = current_chord.notes[0]

    # A new Bar must be created
    elif direction == "KEY_RIGHT":

        pad_index = score[current_bar].pad

        score.append(Bar(score[-1].endy, beats))
        current_bar = len(score) - 1
        current_chord = score[-1].chords[0]
        current_note = current_chord.notes[0]

        score[current_bar].pad = pad_index

        # If the current bar overflows off the screen
        if score[current_bar].endy >= stdscr_width - 3:
            redo_all_pads()
            Draw.draw_entire_score(score, pads, stave_height, beats, key)
            navigate_to_note()

        else:
            Draw.draw_bar(score, pads, -1, stave_height, beats, key)

        change_to_score(Representation.score_to_string(score, beats))


    shift_visible(score[current_bar].pad)
    navigate_to_note()

def move_left(bar_index : int, chord : Chord) -> list[int, Chord]:
    """Given a bar and chord, return the previous chord, regardless of which bar it's in"""
    # Check the current Bar
    prev_chord = score[bar_index].get_prev_chord(chord)

    if prev_chord:
        return [bar_index, prev_chord]

    # Is there a previous Bar?
    if bar_index > 0:
        prev_chord = score[bar_index - 1].get_last_chord()
        return [bar_index - 1, prev_chord]

    # If not, return None
    return [None, None]

def move_right(bar_index : int, chord : Chord) -> list[int, Chord]:
    """Given a bar and chord, return the next chord along, regardless of which bar it's in"""

    # Check the current Bar
    next_chord = score[bar_index].get_next_chord(chord)

    if next_chord:
        return [bar_index, next_chord]

    # Is there a next Bar? Then return the first chord of that Bar
    if bar_index < len(score) - 1:
        return [bar_index + 1, score[bar_index + 1].chords[0]]

    # If not, return None
    return [None, None]

def vertical_navigation(pad, direction):
    """Cursor navigation vertically (within a chord)"""
    global current_note

    if direction == "KEY_UP":
        add = -1
    else:
        add = 1

    if current_chord and current_note:
        if current_chord.get_other_note(current_note, add):
            current_note = current_chord.get_other_note(current_note, add)

    Draw.draw_chord(pad, current_chord, stave_height)
    navigate_to_note()

# TODO: deal with a note already being in that position
def transpose(direction, stave_pad, change):
    """Change the pitch of the current note"""
    global current_note

    # current_chord and current_note are not None
    if current_note.pitch != -1:

        if direction == "up":
            new_pitch = current_note.pitch - change
        else:
            new_pitch = current_note.pitch + change

        # If new pitch is outside valid stave height
        if new_pitch < 2 or new_pitch >= stave_height - 2:
            return

        current_chord.remove_note(current_note)
        current_note = current_chord.add_note(new_pitch)

        Draw.draw_chord(stave_pad, current_chord, stave_height)
        navigate_to_note()

def get_current_coords():
    """Get the coordinates of the currently selected note"""

    y = current_chord.y
    x = current_note.pitch
    return [x, y]

def remove_note(pad):
    """Remove the current note from the current chord"""
    global current_note

    if not current_chord.rest:
        current_note = current_chord.remove_note(current_note)

        Draw.draw_chord(pad, current_chord, stave_height)

        if current_chord.rest:
            [prev_bar, prev_chord] = move_left(current_bar, current_chord)
            if prev_chord:
                prev_chord.tie = False

        navigate_to_note()

def parse_note(stave_pad, note):
    """Add the given note to the current chord"""
    global current_chord
    global current_note

    note_code = ord(note)
    lowercase_note = note.lower()
    x = NOTE_DICT[lowercase_note]

    navigate_away_from()

    if not current_chord.rest:

        # If regular note (Replace entire chord)
        if 97 <= note_code <= 103:
            current_note = current_chord.replace_chord(x)

        # If SHIFT + note
        elif 65 <= note_code <= 71:
            current_note = current_chord.add_note(x)
    else:
        # Current chord is a rest
        new_chord = Chord(x, current_chord.length, current_chord.y)

        index = score[current_bar].chords.index(current_chord)
        score[current_bar].chords[index] = new_chord

        current_chord = new_chord
        current_note = current_chord.notes[0]

    Draw.draw_chord(stave_pad, current_chord, stave_height)
    navigate_to_note()

wrapper(main)
