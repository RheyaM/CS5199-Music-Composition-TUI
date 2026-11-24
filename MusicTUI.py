"""Python module providing screen painting and window creation functionality"""
import curses
import subprocess
import sys
import math
from curses import wrapper
from curses.textpad import Textbox, rectangle
from cursesmenu import CursesMenu
from cursesmenu.items import ExitItem, SubmenuItem
from Objects.Bar import Bar
from Objects.Chord import Chord
from Objects.Note import Note
from Draw import Draw
from Project import Project
from Representation import Representation
from Playback import Playback
from Exceptions import InvalidCharException, ExitTextBoxException

# MIDDLE_C determines the x-coordinates of many features (rests, notes, treble clef, etc.)
# This allows easier adjustment of fixed coordinates if the maximum size of the stave is changes
MIDDLE_C : int = 9

NOTE_DICT : dict = {"c": MIDDLE_C + 7, "d": MIDDLE_C + 6, "e": MIDDLE_C + 5, "f": MIDDLE_C + 4, 
                    "g": MIDDLE_C + 3, "a": MIDDLE_C + 2, "b": MIDDLE_C + 1}
ALL_NOTES : list[str] = ["c", "C", "d", "D", "e", "E", "f", "F", "g", "G", "a", "A", "b", "B"]

pads : list[curses.window] = []
visible : list[int] = [] # Indexes of pads which are currently fully visible in pads

current_bar : int = 0 # Index of current bar object in score[]
current_chord : Chord = None # Chord object
current_note : Note = None # Note object

# prev_stack = for each change to the score, store the string representation
# and the current bar, chord and note
prev_stack : list[[str, int, int, int]] = [["B:4.|r1rrr|rrrr|", current_bar, 0, 0]]

# stave_height - to determine how many octaves we can use
STAVE_HEIGHT : int = 26

stdscr_width : int = 0
stdscr_height : int = 0

def main(stdscr : curses.window) -> None:
    global stdscr_width
    global stdscr_height
    global current_bar
    global current_chord
    global current_note
    global prev_stack

    stdscr_height, stdscr_width = stdscr.getmaxyx()

    # Exit if the screen size is too small
    if stdscr_height < 20 or stdscr_width < 113:
        sys.exit("Terminal size is too small")

    proj = Project()
    file : str = ""
    current_chord = proj.score[0].chords[0]
    current_note = current_chord.notes[0]

    set_up_tui(proj, stdscr)

    textbox : curses.window = set_up_textbox(proj)
    hints : curses.window = set_up_hints()
    stave_pad : curses.window = get_current_pad(proj)
    visible.append(0)
    navigate_to_note(pads[proj.get_pad_index(current_bar)])

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
                remove_note(proj, stave_pad)

            case "KEY_UP" | "KEY_DOWN":
                vertical_navigation(stave_pad, char)
                change_made = False

            case "KEY_RIGHT" | "KEY_LEFT":
                horizontal_navigation(proj, char)
                change_made = False

            case "kDN5" | ",":
                transpose("down", stave_pad, 1)

            case "kUP5" | ".":
                transpose("up", stave_pad, 1)

            case "KEY_SR":
                transpose("up", stave_pad, 7)

            case "KEY_SF":
                transpose("down", stave_pad, 7)

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
                dec_length(proj.score)
                Draw.draw_bars_from(proj, pads, max(current_bar - 1, 0), STAVE_HEIGHT)

            case "]":
                inc_length(proj)
                Draw.draw_bars_from(proj, pads, current_bar, STAVE_HEIGHT)

            case "s":
                file = save(file, stdscr, textbox)
                change_made = False

            case "S":
                file = save_as(file, stdscr, textbox)
                change_made = False

            case "p":
                play_audio(proj, file)
                change_made = False

            case "v":
                Playback.stop_audio()
                change_made = False

            case "l" | "L":
                file = load(file, proj, stdscr)

            case "z":
                prev_stack = undo(proj)
                change_made = False
                Draw.draw_entire_score(proj, pads, STAVE_HEIGHT)

            case "m":
                lilypond_string = Representation.score_to_lilypond(proj)
                export_to_lilypond(file, lilypond_string)
                change_made = False

            case "k":
                [key, time] = create_menu(stdscr)
                parse_menu_selections(proj, key, time)
                set_curses_modes(stdscr)

            case "h":
                navigate_away_from(stave_pad)
                refresh_visible_pads(proj.score, stdscr)
                string_mode(proj, stdscr)

            case "0":
                proj = clear_all()
                current_bar = 0
                current_chord = proj.score[current_bar].chords[0]
                current_note = current_chord.notes[0]

            case "KEY_RESIZE":
                stdscr_height, stdscr_width = stdscr.getmaxyx()

                # Provided the terminal size is large enough:
                if stdscr_width >= 113 and stdscr_height >= 20:
                    Draw.draw_hints(hints, stdscr_width)
                    redo_all_pads(proj.score)
                    Draw.draw_entire_score(proj, pads, STAVE_HEIGHT)

                change_made = False

            case _:
                if char in ALL_NOTES:
                    parse_note(proj.get_bar(current_bar), stave_pad, char)

                else:
                    stave_pad.addstr(0, 0, char)

        navigate_to_note(pads[proj.get_pad_index(current_bar)])

        # If the terminal is too small, create an error message pad
        if stdscr_height < 20 or stdscr_width < 112:
            too_small = curses.newpad(stdscr_height, stdscr_width)
            too_small.addstr(stdscr_height//2, (stdscr_width // 2) - 12, "Terminal size too small")
            too_small.refresh(0, 0, 0, 0, stdscr_height, stdscr_width)
            continue

        # if a change was made to the score, the prev_stack should be updated
        if change_made:
            current_chords = proj.get_bar(current_bar).chords
            prev_stack = change_to_score(current_chords, Representation.score_to_string(proj))

        textbox.clear()
        textbox.addstr(1, 0, Representation.score_to_string(proj))
        textbox.refresh(0, 0, stdscr_height - 6, 0, stdscr_height - 4, stdscr_width - 2)

        hints.refresh(0, 0, stdscr_height - 3, 0, stdscr_height - 1, stdscr_width - 2)

        refresh_visible_pads(proj.score, stdscr)
        stave_pad = get_current_pad(proj)

        open("keylog.txt", "a", encoding="utf-8").write("\n" + char)

def clear_all() -> Project:   
    """Clear the entire stave"""

    proj = Project()
    Draw.draw_entire_score(proj, pads, STAVE_HEIGHT)
    return proj

def string_mode(proj, stdscr):
    """Switching to string mode"""
    global current_bar
    global current_chord
    global current_note

    exception_win = None
    writing_box = curses.newwin(2, stdscr_width - 3, stdscr_height - 5, 0)
    writing_box.addstr(Representation.score_to_string(proj))

    curses.curs_set(1)

    writing_box.scrollok(True)
    tb = curses.textpad.Textbox(writing_box)
    tb.insert_mode = True
    tb.stripspaces = True

    writing_box.refresh()

    valid = False
    while not valid:
        try:
            tb.edit(string_mode_key_inputs)
        except ExitTextBoxException:
            curses.curs_set(0)
            return
        
        text = tb.gather().strip().replace("\n", "")
        if exception_win is not None:
            Draw.remove_exception(exception_win)
            exception_win = None

        try:
            proj.score = Representation.string_to_score(text)
            proj.score = redo_bar_lengths(proj.score, proj.beats)
            valid = True
        except InvalidCharException:
            open("log.txt", "a", encoding="utf-8").write("\nInvalid char error")
            exception_win = Draw.draw_exception(stdscr, stdscr_height - 8, 0, "Invalid character\ndetected")
        except Exception:
            open("log.txt", "a", encoding="utf-8").write("\nstring_to_score error")

    current_bar = 0
    current_chord = proj.score[current_bar].chords[0]
    current_note = current_chord.notes[0]

    for bar in proj.score:
        bar.redo_y()

    redo_all_pads(proj.score)

    Draw.draw_entire_score(proj, pads, STAVE_HEIGHT)

    curses.curs_set(0)

def input_box_key_inputs(x):
    """Alternative integer returns for textboxes"""
    if x == 10:
        return 7
    if x == 127:
        return 263
    return x

def string_mode_key_inputs(x):
    """Alternative integer returns for string_mode"""
    if x == 104:
        raise ExitTextBoxException
    return input_box_key_inputs(x)

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

def create_menu(stdscr):
    """Creating and displaying time or key signature menus. Returns the user's choice"""

    key_list=["C Major", "G Major", "D Major", "A Major", "E Major", "B Major", "F# Major",
               "Db Major", "Ab Major", "Eb Major", "Bb Major", "F Major"]
    time_signature_list = ["2 / 4", "3 / 4", "4 / 4"]

    menu = CursesMenu("Project Settings")

    time_submenu = CursesMenu.make_selection_menu(time_signature_list, "Select a time signature")
    key_submenu = CursesMenu.make_selection_menu(key_list, "Select a key signature")
    time_submenu_item = SubmenuItem("Time Signature", time_submenu, menu=menu)
    key_submenu_item = SubmenuItem("Key Signature", key_submenu, menu=menu)
    quit_item = ExitItem(menu=menu)
    time_submenu.items.append(quit_item)
    key_submenu.items.append(quit_item)

    menu.items.append(time_submenu_item)
    menu.items.append(key_submenu_item)

    menu.show()
    menu.join()
    time_selection = time_submenu.selected_option
    key_selection = key_submenu.selected_option

    new_key = None if key_selection == -1 else key_list[key_selection]
    new_beats = None if time_selection == -1 else int(time_signature_list[time_selection][0])

    set_curses_modes(stdscr)

    return [new_key, new_beats]

def parse_menu_selections(proj : Project, key : str, time : int):
    """Take menu selections and update proj as needed"""

    if time is not None:

        proj.score = change_time_signature(proj.score, time)

        proj.beats = time
        redo_all_pads(proj.score)

        shift_visible(proj.score, 0)

        Draw.draw_entire_score(proj, pads, STAVE_HEIGHT)

    if key is not None:
        proj.key = key
        Draw.draw_beginning(proj, pads[0], MIDDLE_C)

def resort_chord_list(chord_list : list[Chord], new_beats : int) -> list[Bar]:
    """Given a list of chords and beats per bar, resort the existing chords into bars.
    Return the new score"""
    new_score = []
    bar_index = 0

    while len(chord_list) > 0:
        chord = chord_list[0]

        # Create a new bar if needed
        if bar_index == len(new_score):
            new_score.append(Bar(0, new_beats))
            new_score[-1].empty_bar()

        bar = new_score[bar_index]
        bar.chords.append(chord)

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

    return new_score

def redo_bar_lengths(score : list[Bar], length : int) -> list[Bar]:
    """Given a score, return a copy of new score with bars of the given length
    and appropriately added rests"""

    # All chords appended to one list and resorted into bars
    chord_list = []
    for bar in score:
        for chord in bar.chords:
            chord_list.append(chord)

    new_score = resort_chord_list(chord_list, length)

    # If the last bar needs to be lengthened with rests
    last_bar = new_score[-1]
    if last_bar.total_length() < length:
        new_chord = Chord(-1, length - last_bar.total_length(), 0)
        rests_to_add = split_chord(new_chord)
        last_bar.chords = last_bar.chords + rests_to_add

    return new_score


# Making a long list of chords
# TODO: account for change in beats when undoing
def change_time_signature(score : list[Bar], new_beats : int) -> list[Bar]:
    """Format the project into the new, given time signature"""
    global current_bar

    new_score = redo_bar_lengths(score, new_beats)

    for bar in new_score:
        bar.redo_y()

        # Preserving the current_chord
        if current_chord in bar.chords:
            current_bar = new_score.index(bar)

    return new_score

def export_to_lilypond(file : str, string : str) -> None:
    """Calling the makeLilypond shell script to compile a pdf of the current score"""

    if file == "":
        lilypond_file = "Untitled.ly"
    else:
        lilypond_file = file.replace(".txt", "") + ".ly"

    with open(lilypond_file, "w", encoding="utf-8") as myfile:
        myfile.write(string)

    subprocess.call(["sh", "./makeLilypond.sh", lilypond_file])

def undo(proj : Project):
    """Revert to the previous state, including current bar, chord and note"""
    global current_bar
    global current_chord
    global current_note

    if len(prev_stack) == 1:
        return prev_stack

    [string, bar_index, chord_index, note_index] = prev_stack[-2]

    proj.score = Representation.string_to_score(string)

    current_bar = bar_index
    current_chord = proj.score[bar_index].chords[chord_index]
    current_note = current_chord.notes[note_index]

    redo_all_pads(proj.score)
    shift_visible(proj.score, proj.score[current_bar].pad)

    prev_stack.pop(-1)

    return prev_stack

def change_to_score(current_chords : list[Chord], new_string : str) -> None:
    """Update the string textbox and the stack of previous strings"""
    global prev_stack

    # update prev_stack, keep the latest 10 changes
    current_chord_index : int = current_chords.index(current_chord)
    chord : Chord = current_chords[current_chord_index]
    current_note_index : int = chord.notes.index(current_note)

    prev_stack.append([new_string, current_bar, current_chord_index, current_note_index])
    prev_stack = prev_stack[-10:]

    return prev_stack

# TODO: cut the chords of the current bar to only play from current_chord
def play_audio(proj, file) -> curses.window:
    """Extract the sublist of score to play, then pass to Playback class"""

    play_pad : curses.window = curses.newpad(4, 20)
    play_pad.addstr(1, 1, "Playing... 'v' to Pause")

    subscore : list[Bar] = proj.score[current_bar::]
    Playback.create_audio(subscore, file, proj.key)

    return play_pad

def set_up_tui(proj : Project, stdscr: curses.window) -> None:
    """Set up curses, stdscr, and the stave pads"""

    set_curses_modes(stdscr)

    stdscr.clear()

    # Creating and adding the first stave pad to the screen
    stave_pad : curses.window = curses.newpad(26, 300)

    stdscr.refresh()
    pads.append(stave_pad)

    Draw.draw_entire_score(proj, pads, STAVE_HEIGHT)
    # navigate_to_note()

def set_up_textbox(proj) -> curses.window:
    """Set up the textbox for the string representation of the score"""
    textbox : curses.window = curses.newpad(3, stdscr_width)
    textbox.addstr(1, 0, Representation.score_to_string(proj))

    return textbox

def set_up_hints() -> curses.window:
    """Set up the pad for hints at the bottom of the TUI"""
    hints : curses.window = curses.newpad(3, 300)
    Draw.draw_hints(hints, stdscr_width)

    return hints

def shift_visible(score, current_pad_index : int) -> list[int]:
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

        total_length = sum([get_pad_height(score, i) for i in range(len(visible))])
        while total_length > stdscr_height - 6:
            visible.pop(to_remove)
            total_length = sum([get_pad_height(score, i) for i in range(len(visible))])

def get_pad_height(score, pad_index):
    """Calculate and return the height of the pad"""
    [top, bottom] = get_pad_min_max(score, pad_index)
    return bottom - top

def refresh_visible_pads(score : list[Bar], stdscr : curses.window) -> None:
    """Refreshing pads based on visible pads"""

    x : int = 0

    # Refresh all visible staves
    for index in visible:
        pad : curses.window = pads[index]
        [top, bottom] = get_pad_min_max(score, index)

        pad.refresh(top, 0, x, 0, min(x + (bottom - top) + 1, stdscr_height - 6), stdscr_width - 2)
        x += (bottom - top)

    # If there is space for a partly visible stave
    if x < stdscr_height - 6 and visible[-1] <= len(pads) - 2:
        pad : curses.window = pads[visible[-1] + 1]
        [top, bottom] = get_pad_min_max(score, visible[-1] + 1)

        pad.refresh(top, 0, x, 0, min(x + (bottom - top) + 1, stdscr_height - 7), stdscr_width - 2)

    else:
        for i in range(x, stdscr_height - 6):
            stdscr.move(i, 0)
            stdscr.clrtoeol()

def get_pad_min_max(score : list[Bar], pad_index : int) -> list[int, int]:
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

def load(file : str, proj : Project, stdscr : curses.window) -> str:
    """Loading a new score"""
    global current_bar
    global current_chord
    global current_note

    stdscr.clear()
    for pad in pads:
        pad.clear()

    stdscr.addstr(stdscr_height - 7, 1, "Input your file name")
    stdscr.addstr(stdscr_height - 1, 1, "To cancel, leave empty")

    textinput = curses.newwin(2, 41, stdscr_height - 5, 2)
    box = Textbox(textinput)
    rectangle(stdscr, stdscr_height - 6, 1, stdscr_height - 3, 43)
    stdscr.refresh()

    box.edit(input_box_key_inputs)
    text = box.gather().replace("\n","").replace(" ", "")

    if text == "":
        Draw.draw_entire_score(proj, pads, STAVE_HEIGHT)
        return file

    try:
        with open(text, "r", encoding="utf-8") as myfile:
            string = myfile.read().replace("\n", "").replace(" ", "")
        myfile.close()

        file = text #Will include .txt

        proj.score = Representation.string_to_score(string)
        del prev_stack[:]

    except FileNotFoundError as e:
        with open("log.txt", "r", encoding="utf8") as file:
            file.write("\n" + str(e))

    current_bar = 0
    current_chord = proj.score[current_bar].chords[0]
    current_note = current_chord.notes[0]

    redo_all_pads(proj.score)
    Draw.draw_entire_score(proj, pads, STAVE_HEIGHT)

    shift_visible(proj.score, 0)

    return file

def save(file : str, stdscr : curses.window, textbox : curses.window) -> str:
    """Save the current score to the current file name"""
    if file != "":
        with open(file, "w", encoding="utf-8") as myfile:
            myfile.write(textbox.instr(1, 0).decode("utf-8"))

        myfile.close()
        return file
    else:
        return save_as(file, stdscr, textbox)

def save_as(file : str, stdscr : curses.window, textbox : curses.window) -> str:
    """Save the score to a given file name"""

    stdscr.clear()

    stdscr.addstr(stdscr_height - 7, 1, "Input your file name")
    stdscr.addstr(stdscr_height - 1, 1, "To cancel, leave empty")

    textinput = curses.newwin(2, 41, stdscr_height - 5, 2)
    box = Textbox(textinput)
    rectangle(stdscr, stdscr_height - 6, 1, stdscr_height - 3, 43)
    stdscr.refresh()

    box.edit(input_box_key_inputs)
    text = box.gather().replace("\n", "").replace(" ", "")


    if text != "":
        with open(text + ".txt", "w", encoding="utf-8") as myfile:
            myfile.write(textbox.instr(1, 0).decode("utf-8"))
        myfile.close()
        file = text + ".txt"

    stdscr.clear()
    textinput.erase()

    stdscr.refresh()

    return file

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

        Draw.draw_chord(pad, to_switch, STAVE_HEIGHT)
        Draw.draw_chord(pad, current_chord, STAVE_HEIGHT)
        # navigate_to_note()

def redo_all_pads(score : list[Bar]):
    """Redo all y values of every bar, beat and chord to get true y values."""

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

    del pads[current_pad + 1:]

def dec_length(score : list[Bar]):
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

    # current_chord remains halved chord, rather than newly created chord
    created_chord = bar.half_chord(current_chord)

    # get the next chord in the bar
    next_chord = score[current_bar].get_next_chord(created_chord)

    # If the next chord is not far enough from the newly created chord, shift it along
    if next_chord and (next_chord.y < created_chord.y + 4):
        score[current_bar].redo_y()

    # If its the last chord and overtook the end of the bar
    if created_chord.y + 5 > score[current_bar].endy:
        score[current_bar].redo_y()

    redo_all_pads(score)

def inc_length(proj : Project):
    """Increase the length of the current chord"""
    score = proj.score

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
        override_chords(proj, current_bar, current_chord, 1)

    else:
        length = current_chord.length
        # If it's not the last chord in the bar, increase the length
        if index != len(score[current_bar].chords) - 1:
            current_chord.length *= 2

        override_chords(proj, current_bar, current_chord, length)

    redo_all_pads(score)
    # navigate_to_note()

# Note: the space to override will always be <= 1
def override_chords(proj : Project, bar_index : int, chord, space : float):
    """Given a chord and the space (length) to override, remove 
    the appropriate number of following chords."""

    score = proj.score

    while space > 0:
        [next_bar, next_chord] = proj.move_right(bar_index, chord)
        index = score[bar_index].chords.index(chord)

        # If there is no next chord to override, create a new_bar
        if next_chord is None:
            new_bar = proj.create_new_bar()

            new_chord = chord.duplicate_chord()
            new_chord.length = space
            new_chord.y = new_bar.chords[0].y

            new_bar.chords.insert(0, new_chord)

            override_chords(proj, len(score) - 1, new_chord, new_chord.length)

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

def get_current_pad(proj):
    """Return the pad of the current bar"""
    return pads[proj.get_pad_index(current_bar)]

def toggle_note_attribute(pad : curses.window, attr : str):
    """Toggle the note attributes"""
    match attr:
        case "sharp" | "flat" | "natural":
            current_note.toggle_attribute(attr)
        case "accent":
            current_chord.toggle_accent()
        case "staccato":
            current_chord.toggle_staccato()

    Draw.draw_chord(pad, current_chord, STAVE_HEIGHT)
    # navigate_to_note()

def navigate_away_from(pad):
    """Remove highlight from current note"""

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

def navigate_to_note(pad):
    """Highlight the current note"""

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

def horizontal_navigation(proj, direction):
    """Navigate horizontally: between chords"""
    global current_bar
    global current_chord
    global current_note

    score = proj.score
    navigate_away_from(pads[proj.get_pad_index(current_bar)])

    if direction == "KEY_RIGHT":
        [next_bar, next_chord] = proj.move_right(current_bar, current_chord)

    else:
        [next_bar, next_chord] = proj.move_left(current_bar, current_chord)

    if next_chord:
        current_bar = next_bar
        current_chord = next_chord
        current_note = current_chord.notes[0]

    # A new Bar must be created
    elif direction == "KEY_RIGHT":

        pad_index = score[current_bar].pad
        proj.create_new_bar()
        current_bar = len(score) - 1
        current_chord = score[-1].chords[0]
        current_note = current_chord.notes[0]

        score[current_bar].pad = pad_index

        # If the current bar overflows off the screen
        if score[current_bar].endy >= stdscr_width - 3:
            redo_all_pads(proj.score)
            Draw.draw_entire_score(proj, pads, STAVE_HEIGHT)

        else:
            Draw.draw_bar(proj, pads, -1, STAVE_HEIGHT)

        current_chords = proj.score[current_bar].chords
        change_to_score(current_chords, Representation.score_to_string(proj))


    shift_visible(score, score[current_bar].pad)

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

    Draw.draw_chord(pad, current_chord, STAVE_HEIGHT)
    # navigate_to_note()

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
        if new_pitch < 2 or new_pitch >= STAVE_HEIGHT - 2:
            return

        current_chord.remove_note(current_note)
        current_note = current_chord.add_note(new_pitch)

        Draw.draw_chord(stave_pad, current_chord, STAVE_HEIGHT)
        # navigate_to_note()

def get_current_coords():
    """Get the coordinates of the currently selected note"""

    y = current_chord.y
    x = current_note.pitch
    return [x, y]

def remove_note(proj : Project, pad : curses.window):
    """Remove the current note from the current chord"""
    global current_note

    if not current_chord.rest:
        current_note = current_chord.remove_note(current_note)

        Draw.draw_chord(pad, current_chord, STAVE_HEIGHT)

        if current_chord.rest:
            [prev_bar, prev_chord] = proj.move_left(current_bar, current_chord)
            if prev_chord:
                prev_chord.tie = False
                Draw.draw_entire_score(proj, pads, STAVE_HEIGHT)

def parse_note(bar : Bar, stave_pad : curses.window, note : Note):
    """Add the given note to the current chord"""
    global current_chord
    global current_note

    note_code = ord(note)
    lowercase_note = note.lower()
    x = NOTE_DICT[lowercase_note]

    navigate_away_from(stave_pad)

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

        index = bar.chords.index(current_chord)
        bar.chords[index] = new_chord

        current_chord = new_chord
        current_note = current_chord.notes[0]

    Draw.draw_chord(stave_pad, current_chord, STAVE_HEIGHT)

wrapper(main)
