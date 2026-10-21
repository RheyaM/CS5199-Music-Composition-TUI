######################################################

To start the Music Composition TUI, in the src folder:

python3 MusicTUI.py

######################################################

To save your file, use 's'. If there is no current 
save file, it will ask for a file name then use this
file whenever the score is saved. 

To save to a different file, use 'S'. This will bring
up the filename textbox. Use ^G to finish writing, and
^H to backspace*

*Following curses' backspacing convention, but this 
will be altered to use regular backspace.

######################################################

The terminal will need to be large enough to accomodate 
the stave and the hints, that is at least 94 columns and 
20 rows.

######################################################

Depending on the terminal used, it may not send 'Option' 
as a keypress. An alternative for Opt-Up/Down for 
transposition has been implemented:

"." - transpose up by 1
"," - transpose down by 1
