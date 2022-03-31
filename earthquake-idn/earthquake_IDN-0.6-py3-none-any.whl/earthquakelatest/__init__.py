import requests
import bs4
"""
Method = Fungsi
Field / Attribute = Variabel
Constructor = method yang dipanggol pertama kali saat object diciptkan, biasanya digunakan untuk mendeklarasikan semua 
              field pada class ini
"""


class Disaster:
    def __init__(self, url, description):
        self.description = description
        self.result = None
        self.url = url

    def display_description(self):
        print(self.description)

    def extraction_data(self):
        print('extraction data not yet implemented')

    def display_data(self):
        print('display data not yet implemented')

    def run(self):
        self.extraction_data()
        self.display_data()

class LatestFlood(Disaster):
    def __init__(self, url):
        super(LatestFlood, self).__init__(url,
                                          'NOT YET IMPLEMENTED, but it should return last flood in Indonesian')

class LatestEarthquake(Disaster):
    def __init__(self, url):
        super(LatestEarthquake, self).__init__(url, 'To get the latest earthquake in Indonesia from BMKG.go.id')

    def extraction_data(self):
        """
        Date: 16 Maret 2022,
        Time: 11:06:43 WIB
        Magnitudo: 4.2
        Depth: 16 km
        Location: LS=7.90 - BT=107.04
        Epicenter: Pusat gempa berada di laut 109 km Tenggara Kota Sukabumi
        perceived: Dirasakan (Skala MMI): II Singajaya, II Cidaun, II Agrabinta, II Cidora
        :return:
        """

        try:
            content = requests.get(self.url)
        except Exception:
            return None
        if content.status_code == 200:
            soup = bs4.BeautifulSoup(content.text, 'html.parser')

            result = soup.find('span', {'class': 'waktu'})
            result = result.text.split(', ')
            date = result[0]
            time = result[1]

            result = soup.find('div', {'class': 'col-md-6 col-xs-6 gempabumi-detail no-padding'})
            result = result.findChildren('li')
            i = 0
            magnitude = None
            depth = None
            ls = None
            bt = None
            epicenter = None
            perceived = None

            for res in result:
                if i == 1:
                    magnitude = res.text
                elif i == 2:
                    depth = res.text
                elif i == 3:
                    coordinate = res.text.split(' - ')
                    ls = coordinate[0]
                    bt = coordinate[1]
                elif i == 4:
                    location = res.text
                elif i == 5:
                    perceived = res.text
                i += 1


            result = dict()
            result["date"] = date
            result["time"] = time
            result["magnitude"] = magnitude
            result["depth"] = depth
            result["coordinate"] = {'ls': ls, 'bt': bt}
            result["location"] = location
            result["perceived"] = perceived

            self.result = result
        else:
            return None

    def display_data(self):
        if self.result is None:
            print("Can't find data latest earthquake")
            return
        print("Last Earthquake base on BMKG")
        print(f"Date: {self.result['date']}")
        print(f"Time: {self.result['time']}")
        print(f"Magnitude: {self.result['magnitude']}")
        print(f"Depth: {self.result['depth']}")
        print(f"Coordinate: LS = {self.result['coordinate']['ls']}, BT = {self.result['coordinate']['bt']}")
        print(f"Location: {self.result['location']}")
        print(f"Perceived: {self.result['perceived']}")

if __name__ == '__main__':
    earthquake_in_indonesian = LatestEarthquake('https://bmkg.go.id')
    earthquake_in_indonesian.display_description()
    earthquake_in_indonesian.run()

    flood_in_indonesian = LatestFlood('NOT YET')
    flood_in_indonesian.display_description()
    flood_in_indonesian.run()
