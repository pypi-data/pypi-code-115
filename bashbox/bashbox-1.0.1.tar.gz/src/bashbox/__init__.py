CornerTL = "\u2554"
CornerTR = "\u2557"
CornerBL = "\u255a"
CornerBR = "\u255d"
EdgeH = "\u2550"
EdgeV = "\u2551"
SplitU = "\u2566"
SplitR = "\u2563"
SplitL = "\u2560"
SplitD = "\u2569"

class BashBox:
    """
    A standard BashBox.
    """
    def __init__(self):
        self.columns = 1
        self.text = [[]] * 1
        self.title = ""
        self.useTitle = False

    def setColumns(self, num):
        """
        Sets the number of columns for the BashBox.

        num: the number of columns. Defaults to 1.
        """
        self.columns = num
        self.text = [[]] * num

    def setTitle(self, title):
        """
        Sets the title of the BashBox. Accepts a single string.

        NOTE: title doesn't play nice when there's only one column and it's smaller than the title. gonna have to fix that.
        """
        self.title = title
        if title != "":
            self.useTitle = True
        else:
            self.useTitle = False

    def setText(self, col, *text):
        """
        Sets the text for a given column.

        col: the column to set the text for.
        text: the text to set. Can take multiple strings.

        NOTE: use setColumns first to set the number of columns before setting text.
        """
        self.text[col] = list(text)
    
    def draw(self):
        """
        Draws the BashBox.
        """
        texts = list(self.text)
        maxes = []
        currentTexts = []
        
        # Sets the maxes array for all given lines.
        for i in range(len(texts)):
            maxes.append(0)
            for j in range(len(texts[i])):
                if len(str(texts[i][j])) > maxes[i]:
                    maxes[i] = len(str(texts[i][j]))

        # Gets the maximum number of lines to draw based off the longest array.
        rowMax = max([len(i) for i in texts])

        titleArray = []
        spaces = 0
        if self.useTitle:
            spaces = sum(maxes) + ((len(maxes) - 1) * 2) + (self.columns + 2) - len(self.title) - 2
            if spaces <= 0:
                spaces = 1
            titleArray.append(CornerTL + (EdgeH * (spaces + len(self.title) + 1)) + CornerTR)
            titleArray.append(EdgeV + " " + self.title + (" " * spaces) + EdgeV)
            titleLength = len(titleArray[1])
        totalMaxes = sum(maxes) + (2 * self.columns) + self.columns + 1

        # Generate the top part of the BashBox.
        topLine = SplitL if self.useTitle else CornerTL
        for i in range(len(maxes)):
            topLine += EdgeH * (maxes[i] + 2)
            # If this isn't the last column, add a split.
            if i < len(maxes) - 1:
                topLine += SplitU
        if self.useTitle:
            difference = titleLength - totalMaxes
            if titleLength > totalMaxes:
                topLine += SplitU + ( EdgeH * (difference - 1)) + CornerBR
                pass
            else:
                topLine += SplitR
        else:
            topLine+= CornerTR

        # Generate the central part of the BashBox.
        centralArray = []
        middleString = ""
        for i in range(rowMax):
            middleString = ""
            for j in range(len(texts)):
                # Try getting the text from the index. If exception is caught, use empty string.
                try:
                    currentTexts.append(str(texts[j][i]))
                except:
                    currentTexts.append("")
            middleString += EdgeV
            # Draw the text in each column.
            for j in range(len(currentTexts)):
                middleString += " " + currentTexts[j] + (" " * (maxes[j] - len(currentTexts[j]) + 1)) + EdgeV
            currentTexts = []
            # Add the current string to the final array.
            centralArray.append(middleString)
        # Print the last split.
        middleString += EdgeV

        # Generate the bottom part of the BashBox.
        bottomLine = CornerBL
        for i in range(len(maxes)):
            bottomLine += EdgeH * (maxes[i] + 2)
            # If this isn't the last column, add a split.
            if i < len(maxes) - 1:
                bottomLine += SplitD
        bottomLine += CornerBR

        # Print the BashBox.
        if self.useTitle:
            for i in range(len(titleArray)):
                print(titleArray[i])
        print(topLine)
        for i in range(len(centralArray)):
            print(centralArray[i])
        print(bottomLine)
