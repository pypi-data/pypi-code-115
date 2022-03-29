import configparser


class Setting:
    setting:configparser.ConfigParser = None

    @staticmethod
    def init() -> None:
        if Setting.setting is None:
            Setting.setting = configparser.ConfigParser()
            Setting.setting.read_file('setting.ini')
    
    @staticmethod
    def get(section:str, option:str, default_value:str=None) -> str:
        Setting.init()
        return Setting.setting.get(section, option, fallback=default_value) 

    @staticmethod
    def get_bool(section:str, option:str, default_value:bool=False) -> bool:
        Setting.init()
        return Setting.setting.getboolean(section, option, fallback=default_value) 

    @staticmethod
    def get_int(section:str, option:str, default_value:int=0) -> int:
        Setting.init()
        return Setting.setting.getint(section, option, fallback=default_value) 

    @staticmethod
    def get_float(section:str, option:str, default_value:float=0.0) -> float:
        Setting.init()
        return Setting.setting.getfloat(section, option, fallback=default_value) 
