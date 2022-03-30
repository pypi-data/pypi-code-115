import base as b

def RunCode(CodeLine):
    ErrorList = []
    Output = None
    LineData = []
    Var = ""

    TempReg = []

    for Character in range(len(CodeLine)):
        if CodeLine[Character] == "=":
            LineData.append(Var)
            Var = ""
        else:
            Var = Var + CodeLine[Character]
    
    #LineData Contains Variable Name (If Any)
    #Var contains rest of the Expression

    def CheckSpecialCharacter(VarName):
        for i in range(len(VarName)):
                if VarName[i] in b.SpecialCharacter:
                    return True
    


    if len(LineData) == 0:
        #TempVars
        MainData = ""
        ParanCount = 0
        for i in range(len(Var)):
            a = Var[i]
            if a == b.L_Paran and ParanCount == 0:
                ParanCount += 1
                TempReg.append(MainData)
                MainData = ""
            elif ParanCount == 1 and a != b.R_Paran:
                MainData = MainData + a
            elif a == b.R_Paran:
                break
            else:
                MainData = MainData + a
        

        # TempReg contains Keyword
        # MainData Contains Expression

        MainData = MainData.replace(" ", "")
        z = ""
        for i in range(len(MainData)):
            a = MainData[i]
            
            if a == '+' or a == '-' or a == '*' or a == '/':
                TempReg.append(z)
                TempReg.append(a)
                z = ""
            elif i == len(MainData) - 1:
                z = z + a
                TempReg.append(z)
            else:
                z = z + a


        DivIndex = None
        NewIndex = None
        Operand1 = None
        Operand2 = None
        Result = None

        #We have values arranged in TempReg List
        # Now we have to solve the expression 

        #While_Condition = b.Plus in TempReg or b.Minus in TempReg or b.Multiply in TempReg or b.Divide in TempReg and len(TempReg) > 2

        for i in TempReg:
            if i == b.Plus or i == b.Minus or i == b.Divide or i == b.Multiply:
                if b.Divide in TempReg:
                    DivIndex = TempReg.index(i)
                    Operand1 = TempReg[DivIndex - 1]
                    NewIndex = DivIndex - 1
                    Operand2 = TempReg[DivIndex + 1]
                    try:
                        Result = float(Operand1) / float(Operand2)
                    except:
                        ErrorList.append(b.Error("Wrong Operation", "String Cannot be Divided"))
                        break

                    if Result != None:
                        del TempReg[DivIndex]
                        del TempReg[DivIndex - 1]
                        del TempReg[DivIndex - 1]
                        TempReg.insert(NewIndex, Result)

                elif b.Multiply in MainData:
                    DivIndex = TempReg.index(i)
                    Operand1 = TempReg[DivIndex - 1]
                    NewIndex = DivIndex - 1
                    Operand2 = TempReg[DivIndex + 1]
                    try:
                        Result = float(Operand1) * float(Operand2)
                    except:
                        ErrorList.append(b.Error("Wrong Operation", "String Cannot be Multiplied with a string"))
                        break

                    if Result != None:
                        del TempReg[DivIndex]
                        del TempReg[DivIndex - 1]
                        del TempReg[DivIndex - 1]
                        TempReg.insert(NewIndex, Result)

                elif b.Plus in MainData:
                    DivIndex = TempReg.index(i)
                    Operand1 = TempReg[DivIndex - 1]
                    NewIndex = DivIndex - 1
                    Operand2 = TempReg[DivIndex + 1]
                    try:
                        Result = float(Operand1) + float(Operand2)
                    except:
                        Result = Operand1 + Operand2

                    del TempReg[DivIndex]
                    del TempReg[DivIndex - 1]
                    del TempReg[DivIndex - 1]
                    TempReg.insert(NewIndex, Result)

                elif b.Minus in MainData:
                    DivIndex = TempReg.index(i)
                    Operand1 = TempReg[DivIndex - 1]
                    NewIndex = DivIndex - 1
                    Operand2 = TempReg[DivIndex + 1]
                    try:
                        Result = float(Operand1) - float(Operand2)
                    except:
                        ErrorList.append(b.Error("Wrong Operation", "String Cannot be subtracted"))
                        break

                    if Result != None:
                        del TempReg[DivIndex]
                        del TempReg[DivIndex - 1]
                        del TempReg[DivIndex - 1]
                        TempReg.insert(NewIndex, Result)            
        
        #Now we have keyword and solved expression in TempReg

        ab = TempReg[0]

        if ab == "out":
            Output = TempReg[1]
        else:
            Output = None

    elif LineData.__len__() == 1 and len(LineData[0].split()) <= 1 and LineData[0][0] not in b.NumericValues and CheckSpecialCharacter(LineData[0][0]) == False:
        pass  
    
    
    #Error Handling if 2 equals in a line
    elif LineData.__len__() > 1:
        ErrorList.append(b.Error("Rule Violation", "Two equals used in a single line"))   

    #ErrorHandling
    else:
        VarName = LineData[0]

        if " " in VarName and len(VarName.split()) > 1:
            ErrorList.append(b.VarNameError("Variable Name Error", 0))

        elif VarName[0] in b.NumericValues:
            ErrorList.append(b.VarNameError("Variable Name Error", 1))

        else:
            if CheckSpecialCharacter(VarName):
                ErrorList.append(b.VarNameError("Variable Name Error", 2))
                    

    return Output, ErrorList
    