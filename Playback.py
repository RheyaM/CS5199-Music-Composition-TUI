from Objects.Bar import Bar
from Objects.Chord import Chord
import music
import pygame
from pygame import mixer

coordsToPitch = { 0: 0, 1 : -2, 2 : -4, 3 : -5, 4 : -7, 5 : -9, 6 : -10}

keys : dict = {"C Major": [], "G Major": [6], "D Major": [6, 2], 
               "A Major": [6, 2, 5], "E Major": [6, 2, 5, 1],
               "B Major": [6, 2, 5, 1, 4], "F# Major": [6, 2, 5, 1, 4, 0],
               "Db Major": [3, 0, 4, 1, 5], "Ab Major": [3, 0, 4, 1], 
               "Eb Major": [3, 0, 4], "Bb Major": [3, 0], "F Major": [3]}


class Playback:

    def createAudio(score, file, key):
        chords = Playback.scoreToPlayback(score, key)

        melody = music.horizontal_stack(*[music.adsr(sonic_vector=n)
                                  for n in chords])
            
        # , attack_ms=50, decay_ms=70,release_ms=0
        if file == "":
            file = "playback"
        music.write_wav_mono(melody, file + ".wav")
        # music.play_audio(melody)
        Playback.playAudio(file + ".wav")

    def playAudio(file):
        pygame.init()
        mixer.init()

        mixer.music.load(file)
        mixer.music.play()

    def stopAudio():
        if mixer.get_init():
            mixer.music.stop()

    def checkAudio():
        return mixer.music.get_busy()

    def scoreToPlayback(score, key):

        chords = []

        for bar in score:
            for chord in bar.chords:
                length = chord.length / 2
                if chord.staccato:
                    length = 0.2
                xvalues = Playback.chordToPitches(chord, key)

                if xvalues[0] == None:
                    chords.append(music.silence(length))

                else:
                    freqs = music.pitch_to_freq(start_freq=440, semitones=xvalues)
                    chordToAdd = music.note(freqs[0], length)
                    if len(freqs) > 1:
                        for f in freqs[1::]:
                            chordToAdd = music.mix(chordToAdd, music.note(f, length))

                    chords.append(chordToAdd)

                    if chord.staccato:
                        chords.append(music.silence((chord.length / 2) - 0.2))

        return chords

    def chordToPitches(chord, key) -> list[int]:
        xvalues = []
        for note in chord.notes:
            if note.pitch == -1:
                return [None]
            
            pitch = (note.pitch - 11)

            toMultiply = pitch // 7
            standardised = pitch - (toMultiply * 7)
            dictPitch = coordsToPitch[standardised]

            dictPitch -= (12 * toMultiply)

      
            if note.sharp:
                dictPitch += 1

            elif note.flat:
                dictPitch -= 1

            elif note.pitch - (7 * (note.pitch//7)) in keys[key]:

                open("log.txt", "a").write("\nyup")

                if key[1] == "b" or key == "F Major":
                    dictPitch -= 1
                else:
                    dictPitch += 1

            xvalues.append(dictPitch)

        return xvalues


            


