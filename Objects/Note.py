class Note:
    def __init__(self, pitch : int):
        self.pitch = pitch #Integer (x-coord on the stave)
        self.attribute = None

    def toggleSharp(self):

        if self.attribute == "sharp":
            self.attribute = None
        else:
            self.attribute = "sharp"
    
    def toggleFlat(self):
        if self.attribute == "flat":
            self.attribute = None
        else:
            self.attribute = "flat"

    def toggle_attribute(self, newattr):
        if self.attribute == newattr:
            self.attribute = None
        else:
            self.attribute = newattr
    
    def toggleNatural(self):
        self.natural = not self.natural
        if self.natural:
            self.flat = False
            self.sharp = False