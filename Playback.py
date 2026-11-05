from Objects.Bar import Bar
from Objects.Chord import Chord
import music
import pygame
from pygame import mixer

coordsToPitch = { 0: 0, 1 : -2, 2 : -4, 3 : -5, 4 : -7, 5 : -9, 6 : -10}

class Playback:

    def createAudio(score, file):
        chords = Playback.scoreToPlayback(score)

        melody = music.horizontal_stack(*[music.adsr(sonic_vector=n)
                                  for n in chords])

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

    def scoreToPlayback(score):

        chords = []

        for bar in score:
            for chord in bar.chords:
                length = chord.length / 2
                if chord.staccato:
                    length = 0.2
                xvalues = Playback.chordToPitches(chord)

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

    def chordToPitches(chord) -> list[int]:
        xvalues = []
        for note in chord.notes:
            if note.pitch == -1:
                return [None]
            
            pitch = (note.pitch - 6)

            toMultiply = pitch // 7
            standardised = pitch - (toMultiply * 7)
            dictPitch = coordsToPitch[standardised]

            dictPitch -= (12 * toMultiply)

            if note.sharp:
                dictPitch += 1

            if note.flat:
                dictPitch -= 1

            xvalues.append(dictPitch)

        return xvalues


            


