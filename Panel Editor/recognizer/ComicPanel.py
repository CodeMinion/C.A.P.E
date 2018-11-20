class ComicPanel:
    def __init__(self, boundingRect, countours):
        # Bouding box of the panel
        self.boundingRect = boundingRect
        # Countrous of the panel shape. Intended for complexed panels.
        self.countours = countours

        self.x  = boundingRect[0]
        self.y = boundingRect[1]

    def __repr__(self):
        return repr((self.boundingRect, self.countours))

    def __getitem__(self, key):
        if (key == 0):
            return self.boundingRect
        elif key == 1:
            return self.countours
