#Constant Values

ADD = "+"
SUBTRACT = "-"

NumericValues  = "0123456789"
SpecialCharacter = "@$%^&-+\/<>:;"


#######################################################################################
#                              """TOKENS"""
#######################################################################################

class Token:
    def __init__(self, Type, Value) -> None:
        self.type = Type
        self.value = Value

#######################################################################################
#                              """KEYWORDS"""
#######################################################################################

class Keyword:
    k_Keyword = []

    def __init__(self, Type) -> None:
        self.k_Keyword.append(self)
        self.type = Type


out = Keyword("Print")

#######################################################################################
#                           """DELIMETER HANDLING"""
#######################################################################################

L_Paran = "("
R_Paran = ")"
Equals = "="

#######################################################################################
#                               """OPERATORS"""
#######################################################################################

Plus = "+"
Minus = "-"
Multiply = "*"
Divide = "/"

#######################################################################################
#                              """ERRORS"""
#######################################################################################

class Error:
     def __init__(self, Type, Message) -> None:
         self.ErrorType = Type
         self.DisplayMessage = Message
     def __repr__(self):
         return f"{self.ErrorType} : {self.DisplayMessage}"


class VarNameError(Error):
    
    ErrorList = ["Entered Space in Variable Name",
                 "Variable name Started with Numbers",
                 "Variable name contains special characters"]    

    def __init__(self, Type, Message) -> None:
        super().__init__(Type, Message)

    def __repr__(self) -> str:
        if self.DisplayMessage == 0:
            return f"{self.ErrorType} : {self.ErrorList[0]}"
        elif self.DisplayMessage == 1:
            return f"{self.ErrorType} : {self.ErrorList[1]}"
        elif self.DisplayMessage == 2:
            return f"{self.ErrorType} : {self.ErrorList[2]}"




#######################################################################################
#                             """TEXT FORMATTING""
#######################################################################################

class TextFormat:
    def color_text(CodeLine):
        return "\33[{CodeLine}m".format(CodeLine = CodeLine)


#######################################################################################
#                             """STARTUP INFO""
#######################################################################################

import ThirdParty_Libs.CPU_Info as CI
import datetime as dt
CPU_Type = CI.cpu.info[0]['ProcessorNameString']
Time = dt.datetime.now()
Time = str(Time).split('.')[0]
StartLine = f"Running on {CPU_Type} at {Time}"
