def gpapsgcalc(*marks):
    sum=0
    credsum=0
    for i in range(0,len(marks),2):
        sum+=(a[i]*a[i+1])
        credsum+=a[i+1]
    gpa=sum/credsum
    print(gpa)
    return gpa
def cgpapsgcalc(*gpa):
    sumgpa=0
    for i in range(0,len(gpa),1):
        sumgpa+=gpa[i]
    cgpa=sumgpa/len(gpa)
    print(cgpa)
    return cgpa  
