class Note:
    def __init__(self, pitch):
        self.pitch = pitch #Integer (x-coord on the stave)
        self.sharp = False
        self.flat = False
        self.natural = False

    def toggleSharp(self):
        self.sharp = not self.sharp

        if self.sharp:
            self.natural = False
            self.flat = False
    
    def toggleFlat(self):
        self.flat = not self.flat

        if self.flat:
            self.natural = False
            self.sharp = False
    
    def toggleNatural(self):
        self.natural = not self.natural
        if self.natural:
            self.flat = False
            self.sharp = False