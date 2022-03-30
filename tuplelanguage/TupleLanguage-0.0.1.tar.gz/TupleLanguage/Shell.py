import os 
import time
import SingleLineInterpreter as SL

import ColorGrading as CG
from ColorGrading import SetColor as scr

ShellCode = "TUPLE -> "
EndCode1 = "Exiting with "
EndCode2 = "Exiting with 0 Errors"

def Run():
    os.system('cls')
    time.sleep(1)
    scr(CG.Green)
    print(SL.b.StartLine)
    scr(CG.Reset)
    
    time.sleep(1)
    
    while True:
        InputCode = input(ShellCode)
        Result, Errors = SL.RunCode(InputCode)
    
        if Errors:
            count = 0
    
            scr(CG.Red)
            print("Displaying Errors:")
            
            for i in range(len(Errors)):
                count += 1
                print(f"{count}. {Errors[i]}")
            for i in range(2):
                print(" ")
            
            scr(CG.Reset)
            print(EndCode1, len(Errors), " Errors" )
            break
        
        else:
            if Result == None:
                Result = " "
    
            print(f"      -> {Result}")
            scr(CG.Green)
            print(EndCode2)
            scr(CG.Reset)