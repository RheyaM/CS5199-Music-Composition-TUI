"""Module for creating .wav files"""
import music
import pygame
from pygame import mixer
from Objects.Bar import Bar


coords_to_pitch = { 0: 0, 1 : -2, 2 : -4, 3 : -5, 4 : -7, 5 : -9, 6 : -10}

keys : dict = {"C Major": [], "G Major": [6], "D Major": [6, 2],
               "A Major": [6, 2, 5], "E Major": [6, 2, 5, 1],
               "B Major": [6, 2, 5, 1, 4], "F# Major": [6, 2, 5, 1, 4, 0],
               "Db Major": [3, 0, 4, 1, 5], "Ab Major": [3, 0, 4, 1], 
               "Eb Major": [3, 0, 4], "Bb Major": [3, 0], "F Major": [3]}


class Playback:
    """Class for creating and playing .wav files"""

    @staticmethod
    def create_audio(score, file, key):
        """Generate a .wav file from the given score and key"""
        chords = Playback.score_to_playback(score, key)

        melody = music.horizontal_stack(*[music.adsr(sonic_vector=n)
                                  for n in chords])

        # , attack_ms=50, decay_ms=70,release_ms=0
        if file == "":
            file = "playback"
        file = file.replace(".txt", "")
        music.write_wav_mono(melody, file + ".wav")
        # music.play_audio(melody)
        Playback.play_audio(file + ".wav")

    @staticmethod
    def play_audio(file):
        """Play the .wav file given"""
        pygame.init()
        mixer.init()

        mixer.music.load(file)
        mixer.music.play()

    @staticmethod
    def stop_audio():
        """Pause the currently playing .wav file"""
        if mixer.get_init():
            mixer.music.stop()

    @staticmethod
    def check_audio():
        """Return true if the audio is currently playing"""
        return mixer.music.get_busy()

    @staticmethod
    def score_to_playback(score : list[Bar], key):
        """Generate sonic vectors for each chord in the score"""

        

        chord_list = []
        for bar in score:
            chord_list.extend(bar.chords)

        open("log.txt", "a").write("\nindex : " + str([c.tie for c in chord_list]))
        

        chords = []

        index = 0
        length = 0
        while index < len(chord_list):
            chord = chord_list[index]

            length += (chord.length / 2)

            # If the current chord is a tie, add its length to the next chord
            if chord.tie:
                index += 1
                continue

            if chord.staccato:
                length = 0.2
            xvalues = Playback.chord_to_pitches(chord, key)

            if xvalues[0] is None:
                chords.append(music.silence(length))

            else:
                freqs = music.pitch_to_freq(start_freq=440, semitones=xvalues)
                chord_to_add = music.note(freqs[0], length)
                if len(freqs) > 1:
                    for f in freqs[1::]:
                        chord_to_add = music.mix(chord_to_add, music.note(f, length))

                chords.append(chord_to_add)

                if chord.staccato:
                    chords.append(music.silence((chord.length / 2) - 0.2))

            length = 0
            index += 1

        return chords

    @staticmethod
    def chord_to_pitches(chord, key) -> list[int]:
        """Standardise all notes to linear scale including flats and sharps"""

        xvalues = []
        for note in chord.notes:
            if note.pitch == -1:
                return [None]

            pitch = note.pitch - 11

            to_multiply = pitch // 7
            standardised = pitch - (to_multiply * 7)
            dict_pitch = coords_to_pitch[standardised]

            dict_pitch -= (12 * to_multiply)

            if note.attribute == "sharp":
                dict_pitch += 1

            elif note.attribute == "flat":
                dict_pitch -= 1

            elif note.pitch - (7 * (note.pitch//7)) in keys[key] and note.attribute != "natural":

                if key[1] == "b" or key == "F Major":
                    dict_pitch -= 1
                else:
                    dict_pitch += 1

            xvalues.append(dict_pitch)

        return xvalues
    