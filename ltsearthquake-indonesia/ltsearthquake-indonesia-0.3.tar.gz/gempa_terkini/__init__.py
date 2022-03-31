"""
Aplikasi Deteksi Gempa terkini
MODULARISASI DENGAN FUNCTION
MODULARISASI DENGAN PACKAGES
"""
import requests
from bs4 import BeautifulSoup

import gempa_terkini


def ekstraksi_data():
    """
    Tanggal: 09 Maret 2022,
    Waktu:08:49:18 WIB
    
    Magnitudo: 5.2
    Loksi: LS=2.57  BT=128.43 BT
    Kedalaman: 14 km
    Pusat Gempa: Pusat gempa berada di Laut 60 km TimurLaut Daruba Dirasakan (Skala MMI): II-III Morotai
    :return:
    """
    try:
        content = requests.get('https://bmkg.go.id')
    except Exception:
        return None

    if content.status_code == 200:
        soup = BeautifulSoup(content.text, 'html.parser')

        result = soup.find('span', {'class': 'waktu'})
        result = result.text.split(', ')
        tanggal = result[0]
        waktu = result[1]
        print(content.text)

        result = soup.find('span', {'class': 'ic magnitude'})
        result = result.findChildren('li')
        i = 0
        for res in result:
            print(res)

            print(result)

        magnitudo = None
        kedalaman = None
        ls = None
        bt = None
        lokasi = None
        dirasakan = None
        print(result)
        # waktu = tanggal.text.split(', ')[1]
        # waktu = result.text.split(', ')[1]
        # tanggal = soup.find('span', {'class': 'waktu'})[0]
        # tanggal = tanggal.text.split(', ')[0]
        # result2 = result.text.split(', ')

        # title = soup.find('title')
        # print(title.string)
        # waktu = Tanggal.text.split(',')
        # result = result.findChildren('li')
        # i = 0
        # for res in result:
        #     print(i, res)
        #     i
        # tanggal = result[0]
        # waktu = result[i]

        # result
        # print(soup.prettify())
        # soup = BeautifulSoup(content)
        # print(soup.prettify())

        for res in result:
            print(i, res)
            if i == 2:
                magnitudo = res.text
            elif i == 2:
                kedalaman = res.text
            elif i == 3:
                koordinat = res.text.split(' -  ')
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
        hasil['pusat'] = 'Pusat gempa berada di Laut 60 km TimurLaut Daruba'
        hasil['dirasakan'] = dirasakan
        return hasil
    else:
        return None


def tampilkan_data(result):
    if result is None:
        print("Tidak bisa menemukan data gempa terkini")
        return

    print('Gempa Terakhir berdasarkan BMKG')
    print(f"Tanggal{result['tanggal']}")
    print(f"Waktu {result['waktu']}")
    print(f"Magnitudo {result['magnitudo']}")
    print(f"Kedalaman {result['kedalaman']}")
    print(f"Lokasi: LS={result['lokasi']    }")
    print(f"Koordinat: LS={result['koordinat']['ls']}, BT={result['koordinat']['bt']}")
    print(f"Pusat {result['pusat']}")
    print(f"Dirasakan {result['dirasakan']}")


if __name__ == '__main__':
    result = gempa_terkini.ekstraksi_data()
    # gempa_terkini.tampilkan_data(result)
    # print('Ini adl packages gempa terkini')
    # print('Hai')
    # result = ekstraksi_data()
    tampilkan_data(result)
