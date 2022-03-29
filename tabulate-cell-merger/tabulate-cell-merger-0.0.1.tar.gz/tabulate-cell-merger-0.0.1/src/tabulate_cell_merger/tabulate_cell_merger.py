#auxiliar functions
def isInRowspan(y, x, rowspan):
    rowspan_value = 0
    row_i = 0
    for i in range(y):
        if (i, x) in rowspan.keys():
            rowspan_value = rowspan[(i, x)]
            row_i = i
    if rowspan_value - (y - row_i) > 0:
        return True
    else:
        return False

def writeCell(table, y, x, length, rowspan = {}):
    text = table[y][x]
    extra_spaces = ""
    if isInRowspan(y, x, rowspan):
        text = "|"
        for i in range(length): #according to column width
            text += " "
        print(text, end = "")
    else:
        for i in range(length - len(text) - 2):
            extra_spaces += " " #according to column width
        print(f"| {text} " + extra_spaces, end = "")

def writeColspanCell(length, colspan_value): #length argument refers to sum of column widths
    text = ""
    for i in range(length + colspan_value - 1):
        text += " "
    print(text, end = "")

def getMaxColWidth(table, idx): #find the longest cell in the column to set the column's width
    maxi = 0
    for row in table:
        if len(row) > idx: #avoid index out of range error
            cur_len = len(row[idx]) + 2
            if maxi < cur_len:
                maxi = cur_len
    return maxi

def getMaxRowLen(table): #find longest row list (in terms of elements)
    maxi = 0
    for row in table:
        cur_len = len(row)
        if maxi < cur_len:
            maxi = cur_len
    return maxi

def getAllColLen(table): #collect in a list the widths of each column
    widths = [getMaxColWidth(table, i) for i in range(getMaxRowLen(table))]
    return widths

def getMaxRowWidth(table): #set the width of the table
    maxi = 0
    for i in range(len(table)):
        cur_len = sum(getAllColLen(table)) + len(getAllColLen(table)) + 1 # "|" at borders and between cells
        if maxi < cur_len:
            maxi = cur_len
    return maxi

def drawBorder(table, y, colspan = {}, rowspan = {}):
    col_widths = getAllColLen(table)
    length = getMaxRowWidth(table)
    cell_w_count = 0
    cell_counter = 0
    for i in range(length):
        if isInRowspan(y, cell_counter - 1, rowspan) and not (i == cell_w_count or i == length - 1):
            print(" ", end = "")
        elif i == cell_w_count or i == length - 1:
            print("+", end = "")
            if cell_counter != getMaxRowLen(table):
                cell_w_count += col_widths[cell_counter] + 1
                cell_counter += 1
        else:
            print("-", end = "")
    print("") #next line (end = "\n")

#main function
def tabulate(table, colspan = {}, rowspan = {}):
    table_width = getMaxRowWidth(table)
    col_widths = getAllColLen(table)
    for y, row in enumerate(table):
        drawBorder(table, y, colspan, rowspan)
        x = 0
        while x < len(row): #altered for loop
            writeCell(table, y, x, col_widths[x], rowspan)
            if (y, x) in colspan.keys():
                colspan_value = colspan[(y, x)]
                writeColspanCell(sum(col_widths[x+1:x+colspan_value]), colspan_value)
                x += colspan_value - 1
            x += 1
        print("|") #end table row
    drawBorder(table, getMaxRowLen(table) - 1) #close bottom of table

