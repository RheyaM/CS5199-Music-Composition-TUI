class Note:
    def __init__(self, pitch : int):
        self.pitch = pitch #Integer (x-coord on the stave)
        self.attribute = None

    def toggle_attribute(self, newattr):
        """Ammend the note's attribute"""
        if self.attribute == newattr:
            self.attribute = None
        else:
            self.attribute = newattr

    def sharp(self):
        """Return True if the note is sharp"""
        if self.attribute == "sharp":
            return True
        return False

    def flat(self):
        """Return True if the note is flat"""
        if self.attribute == "sharp":
            return True
        return False

    def natural(self):
        """Return True if the note is natural"""
        if self.attribute == "sharp":
            return True
        return False