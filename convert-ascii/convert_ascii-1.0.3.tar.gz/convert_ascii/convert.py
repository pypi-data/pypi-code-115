
Alphabeto_Ma= ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
Equivalente_ascii_ma=['65','66','67','68','69','70','71','72','73','74','75','76','77','78','79','80','81','82','83','84','85','86','87','88','89','90']

Alphabeto_Min= ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
Equivalente_ascii_min=['97','98','99','100','101','102','103','104','105','106','107','108','109','110','111','112','113','114','115','116','117','118','119','120','121','122']


def converte_para_decimal(parametro):
    j=0
    if((parametro).isupper()):
        for i in Alphabeto_Ma:
            if str(parametro) == Alphabeto_Ma[j]:
                return Equivalente_ascii_ma[j]
            j=j+1
    else:
        for i in Alphabeto_Min:
            if parametro == Alphabeto_Min[j]:
                return Equivalente_ascii_min[j]
            j=j+1
def converte_para_letra(parametro):
    j=0
    if int(parametro)<91:
        for i in Equivalente_ascii_ma:
            if parametro == Equivalente_ascii_ma[j]:
                return Alphabeto_Ma[j]
            j=j+1
    else:
        for i in Equivalente_ascii_min:
            if parametro == Equivalente_ascii_min[j]:
                return Alphabeto_Min[j]
            j=j+1


if(__name__=="__main__"):
    valor=input()
    