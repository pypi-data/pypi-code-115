from bs4 import BeautifulSoup
import requests

def DataExtraction():
    
    try:
        content = requests.get('https://www.bmkg.go.id/')
    except Exception:
        return None
    
    if content.status_code == 200:
        soup = BeautifulSoup(content.text, 'html.parser')
        
        datetime = soup.find('span', {'class': 'waktu'}) 
        datetime = datetime.text.split(', ')
        date = datetime[0]
        time = datetime[1]
        
        datascrap = soup.find('div', {'class': 'col-md-6 col-xs-6 gempabumi-detail no-padding'}) 
        datascrap = datascrap.findChildren('li') 
        
        i = 0
        magnitude = None
        kedalaman = None
        ls = None
        bt = None
        location  = None
        dampak = None
        
        for datalist in datascrap:
            
            if i == 1:
                magnitude = datalist.text
            elif i == 2:
                kedalaman = datalist.text
            elif i == 3:
                coordinate = datalist.text.split(' - ')
                ls = coordinate[0]
                bt = coordinate[1]
            elif i == 4:
                location = datalist.text
            elif i == 5:
                dampak = datalist.text
                
            i = i + 1
        
        hasil = dict()
        hasil['tanggal']       = date
        hasil['waktu']         = time
        hasil['magnitudo']     = magnitude
        hasil['kedalaman']     = kedalaman
        hasil['koordinat']     = {'ls':ls, 'bt':bt}
        hasil['lokasi']        = location
        hasil['dampak']        = dampak
        
        return hasil
    else:
        return None


def ShowData(result):
    if result is None:
        print("Data Not Found")
        return
    
    print("Latest Earthquake based on BMKG")
    print(f"Tanggal    : {result['tanggal']}")
    print(f"Waktu      : {result['waktu']}")
    print(f"Magnitudo  : {result['magnitudo']}")
    print(f"Kedalaman  : {result['kedalaman']}")
    print(f"Koordinat  : LS = {result['koordinat']['ls']} | BT = {result['koordinat']['bt']}")
    print(f"Lokasi     : {result['lokasi']}")
    print(f"Dampak     : {result['dampak']}")
    
if __name__ == '__main__':
    print('Package BMKG Latest Earthquake')
    result = DataExtraction()
    ShowData(result)