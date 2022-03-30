import configparser

class Config(object):
    def __init__(self, filename=__file__[:-9] + 'config.ini'):
        self._config = configparser.ConfigParser()  # set it to conf
        self._config.read(filename)

    def get_item(self, property_name, item):
        if property_name not in self._config.sections():  # we don't want KeyError
            return None  # just return None if not found
        if property_name == "COORDINATE":
            return eval(self._config[property_name].get(item))
        return self._config[property_name].get(item)

    def create_config(self, filename='config.ini'):
        self._config['PATH'] = {
            'TESSERACT': r'D:\Program Files\Tesseract-OCR\tesseract.exe',
        }
        self._config['COORDINATE'] = {
            'CHECK_MONEY_POS': (250, 120, 110, 55),
            'CHECK_BUY_PHASE': (810, 140, 310, 140),
            'ENEMY_SCORE_INFO': (750, 25, 100, 55),
            'OWN_SCORE_INFO': (1050, 25, 100, 55),
            'TIME_LEFT_POS': (900, 25, 100, 55),
        }

        with open(filename, 'w') as configfile:
            self._config.write(configfile)


class GlobalConfig(Config):
    @property
    def tesseract_path(self):
        return self.get_item('PATH', 'TESSERACT')


class MarketConfig(Config):
    @property
    def money_coor(self):
        return self.get_item('COORDINATE', 'CHECK_MONEY_POS')

    @property
    def buy_phase_coor(self):
        return self.get_item('COORDINATE', 'CHECK_BUY_PHASE')


class GameplayConfig(Config):

    @property
    def buy_phase_coor(self):
        return self.get_item('COORDINATE', 'CHECK_BUY_PHASE')

    @property
    def enemy_info_coor(self):
        return self.get_item('COORDINATE', 'ENEMY_SCORE_INFO')

    @property
    def own_info_coor(self):
        return self.get_item('COORDINATE', 'OWN_SCORE_INFO')

    @property
    def time_left_coor(self):
        return self.get_item('COORDINATE', 'TIME_LEFT_POS')


if __name__ == "__main__":
    # configuration = Config()
    # configuration.create_config()
    # print(c)

    # print(configuration.get_property('COORDINATEs', 'CHECK_MONEY_POS'))
    import os

    configuration = MarketConfig()
    print(configuration.money_coor)
    print(configuration.buy_phase_coor)
