from math import log2,log,sqrt
from sys import maxsize
import matplotlib.pyplot as mpl
from decimal import *
getcontext().prec = 1000

def factors(n):
    l = []
    for i in range(1,int(n/2)):
        if n%i==0:
            if i not in l:
                l.append(i)
            if n/i not in l:
                l.append(int(n/i))
    l.sort()
    return l            

def is_perfect(n):
    sum=0
    for j in factors(n):
        sum=sum+j
    if sum==n:
        return True
    else:
        return False

def is_prime(n):
    if len(factors(n)) <= 2:
        return True
    else:
        return False

def per(n):
    i = 0
    while len(str(n))>1:
        new = 1
        for j in str(n):
            new = new * int(j)
        i=i+1
        n = new
    return i

def gamma(n):
    tot = Decimal(0)
    for i in range(1,n+1):
        tot = tot + Decimal(1)/Decimal(i)
    return tot-Decimal(log(Decimal(n)))

def fac(n):
    f = 1
    for i in range(1,n+1):
        f *= i
    return f

def hyper_fac(n):
    f = 1
    for i in range(1,n+1):
        f *= i**i
    return f

def e_p(n):
    n=Decimal(n)
    return Decimal((Decimal(1)+Decimal(Decimal(1)/Decimal(n)))**n)

def e_f(n):
    tot = 1
    for i in range(1,n+1):
        tot = tot + 1/fac(i)
    return tot

def c(n,k):     #binomial
    return fac(n)/(fac(k)*fac(n-k))

def pi_frac(n):     #aka leibniz,   fastest, most inaccurate
    p = Decimal(0)
    for i in range(1,n,4):
        p = p + Decimal(4/i)
        p = p - Decimal(4/(i+2))
    return p

def pi_euler(n):        #basel, riemann zeta,       #1.5 slower than leibniz, gets accurate later
    tot = 0
    for i in range(1,n+1):
        tot = tot + Decimal(1)/Decimal(i*i)
    tot = tot * 6
    return Decimal(sqrt(tot))

pi = Decimal(3.141592558096830689606804298819042742252349853515625) #pi_euler(10**7)

e = Decimal(2.718281828459045235360287471352662497757247093699959574966967627724076630353547594571382178525166427427466391932003059921817413596629043572900334295260595630738132328627943490763233829880753195251019011573834187930702154089149934884167509244761460668082264800168477411853742345442437107539077744992069551702761838606261331384583000752044933826560297606737113200709328709127443747047230696977209310141692836819025515108657463772111252389784425056953696770785449969967946864454905987931636889230098793127736178215424999229576351482208269895193668033182528869398496465105820939239829488793320362509443117301238197068416140397019837679320683282376464804295311802328782509819455815301756717361332069811250996181881593041690351598888519345807273866738589422879228499892086805825749279610484198444363463244968487560233624827041978623209002160990235304369941849146314093431738143640546253152096183690888707016768396424378140592714563549061303107208510383750510115747704171898610687396965521267154688957035034)
#e_p(10**999)

def pi_wallis(n):       #slowest, accurate for low values
    p = Decimal(2)
    for i in range(1,n+1):
        p = p * Decimal((2*i)/(2*i-1))
        p = p * Decimal((2*i)/(2*i+1))
    return p

def zeta(n,prec):       #reimann
    tot = 0
    for i in range(1,prec+1):
        tot = tot + 1/(i**n)
    return tot

def sin(x):
    x = Decimal(x)*Decimal(pi/Decimal(180))
    ans = Decimal(0)
    for i in range(100):
        thing = Decimal((-1)**i)
        thing = Decimal(thing)/Decimal(fac(2*i+1))
        thing = Decimal(thing)*Decimal(x**(2*i+1))
        ans += Decimal(thing)
    return ans

def sin_r(x):
    ans = Decimal(0)
    for i in range(100):
        thing = Decimal((-1)**i)
        thing = Decimal(thing)/Decimal(fac(2*i+1))
        thing = Decimal(thing)*Decimal(x**(2*i+1))
        ans += Decimal(thing)
    return ans

def cos(x):
    return sin(90-x)

def cos_r(x):
    return sin_r((pi/2)-x)

def tan(x):
    return Decimal(sin(x)/cos(x))

def tan_r(x):
    return Decimal(sin_r(x)/cos_r(x))

def sin_approx(x):
    ans = 4*x*(180-x)
    ans = Decimal(ans)/Decimal(40500-(x*(180-x)))
    return ans

def cos_approx(x):
    return sin_approx(90-x)

def tan_approx(x):
    return Decimal(sin_approx(x)/cos_approx(x))

def golden(n):
    r = 2
    for i in range(n):
        r = Decimal(1)/Decimal(r) + Decimal(1)
    return r

def decay_time(mass,atomic_mass,half_life):
    a = 6.02214076*10**23
    particles = int(a*mass/atomic_mass)
    return (log2(particles))*half_life

def graph(eq:str,start:int, end:int, prec:int = 1, showgraph:bool = True): #(pass equation as str in y = 'eq' form),    note: infinite values are graphed as max value avaiable
    if 'x' not in eq:
        raise SyntaxError
    if start>end:
        raise ValueError
    yaxis = []
    xaxis = []
    for i in range(start*prec,end*prec+1):
        try:
            x = i/prec
            xaxis.append(x)
            exec(f'yaxis.append({eq})')
        except ZeroDivisionError:
            yaxis.append(maxsize)
    if showgraph:
        mpl.plot(xaxis,yaxis)
        mpl.show()
    return xaxis,yaxis