import configparser


class Setting:
    setting = None

    @staticmethod
    def init() -> None:
        Setting.setting = configparser.ConfigParser()
        Setting.setting.read_file('setting.ini')
    
    @staticmethod
    def get(section:str, option:str, default_value:str=None) -> str:
        if Setting.setting is None:
            Setting.init()
            
        return Setting.setting.get(section, option, fallback=default_value) 
