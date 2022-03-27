# Python colour formatter

# Can format python output 

# Normalise

def normalise():
    return u"\u001b[0m"


# Standard Colours

def black(string):
    return u"\u001b[30m" + string + normalise()

def red(string):
    return u"\u001b[31m" + string + normalise()

def green(string):
    return u"\u001b[32m" + string + normalise()

def yellow(string):
    return u"\u001b[33m" + string + normalise()

def blue(string):
    return u"\u001b[34m" + string + normalise()

def magenta(string):
    return u"\u001b[35m" + string + normalise()

def cyan(string):
    return u"\u001b[36m" + string + normalise()

def white(string):
    return u"\u001b[37m" + string + normalise()



# Bright Colour Variants

def bright_black(string):
    return u"\u001b[30m;1m" + string + normalise()

def bright_red(string):
    return u"\u001b[31m;1m" + string + normalise()

def bright_green(string):
    return u"\u001b[32m;1m" + string + normalise()

def bright_yellow(string):
    return u"\u001b[33m;1m" + string + normalise()

def bright_blue(string):
    return u"\u001b[34m;1m" + string + normalise()

def bright_magenta(string):
    return u"\u001b[35m;1m" + string + normalise()

def bright_cyan(string):
    return u"\u001b[36m;1m" + string + normalise()

def bright_white(string):
    return u"\u001b[37m;1m" + string + normalise()



# Custom 256 colour support

def colour_256(string, num): # `num` must be 0 >= 255
    num = str(num)
    return u"\u001b[38;5;" + num + "m " + string + normalise()



# Backgrounds

def bgBlack(string):
    return u"\001b[40m" + string + normalise()

def bgRed(string):
    return u"\001b[41m" + string + normalise()

def bgGreen(string):
    return u"\001b[42m" + string + normalise()

def bgYellow(string):
    return u"\001b[43m" + string + normalise()

def bgBlue(string):
    return u"\001b[44m" + string + normalise()

def bgMagenta(string):
    return u"\001b[45m" + string + normalise()

def bgMagenta(string):
    return u"\001b[46m" + string + normalise()

def bgCyan(string):
    return u"\001b[47m" + string + normalise()

def bgWhite(string):
    return u"\001b[48m" + string + normalise()



# Light Variants

def bgBright_Black(string):
    return u"\001b[40m;1m" + string + normalise()

def bgBright_Red(string):
    return u"\001b[41m;1m" + string + normalise()

def bgBright_Green(string):
    return u"\001b[42m;1m" + string + normalise()

def bgBright_Yellow(string):
    return u"\001b[43m;1m" + string + normalise()

def bgBright_Blue(string):
    return u"\001b[44m;1m" + string + normalise()
    
def bgBright_Magenta(string):
    return u"\001b[45m;1m" + string + normalise()

def bgBright_Cyan(string):
    return u"\001b[46m;1m" + string + normalise()

def bgBright_White(string):
    return u"\001b[47m;1m" + string + normalise()

def bgBright_Colour(string,num_):
    num_ = str(num_)
    return u"\001b[48m;5;" + num_

# Formatting Options

def bold(string):
    return u"\u001b[1m" + string + normalise()

def underline(string):
    return u"\u001b[4m" + string + normalise()

def reverse(string):
    return u"\u001b[7m" + string + normalise()
