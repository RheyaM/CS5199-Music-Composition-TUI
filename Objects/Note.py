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
            