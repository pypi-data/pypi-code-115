import requests
from bs4 import BeautifulSoup


def ekstraksi_data():
    try:
        content = requests.get('https://bmkg.go.id')
    except Exception:
        return None
    if content.status_code == 200:
        soup = BeautifulSoup(content.text, 'html.parser')
        result = soup.find('span', {'class': 'waktu'})
        result = result.text.split(', ')
        waktu = result[1]
        tanggal = result[0]
        result = soup.find('div', {'class': 'col-md-6 col-xs-6 gempabumi-detail no-padding'})
        result = result.findChildren('li')


        i = 0
        magnitudo = None
        ls = None
        bt = None
        pusat = None
        dirasakan = None
        lokasi = None

        for res in result:
            print(i, res)

            if i == 1:
                magnitudo = res.text
            elif i == 2:
                kedalaman = res.text
            elif i == 3:
                koordinat = res.text.split(' - ')
                ls = koordinat[0]
                bt = koordinat[1]

            elif i == 4:
                lokasi = res.text

            elif i == 5:
                dirasakan = res.text

            i = i + 1
        hasil = dict()
        hasil['tanggal'] = tanggal
        hasil['waktu'] = waktu
        hasil['magnitudo'] = magnitudo
        hasil['kedalaman'] = kedalaman
        hasil['koordinat'] = {'ls': ls, 'bt': bt}
        hasil['lokasi'] = lokasi
        hasil['dirasakan'] = dirasakan
        return hasil
    else:
        return None


def tampilkan_data(result):
    if result is None:
        print('Tidak bisa menemukan data gempa terkini')
        return
    print('Gempa terakhir berdasarkan data BMKG')
    print(f"Tanggal, {result['tanggal']}")
    print(f"waktu, {result['waktu']}")
    print(f"Magnitudo, {result['magnitudo']}")
    print(f"kedalaman, {result['kedalaman']}")
    print(f"koordinat: {result['koordinat']['ls']}, {result['koordinat']['bt']}")
    print(f"Lokasi: {result['lokasi']}")
    print(f"Dirasakan, {result['dirasakan']}")

if __name__ == '__main__':
    result = ekstraksi_data()
    tampilkan_data(result)

