import time
import collections
from ..exceptions import IoCareError

class Purifier(object):
    def __init__(self, data, api):
        self.api = api
        self.device_id = data['barcode']
        self.name = data['dvcNick']
        self.product_name = data['prodName']
        self.product_name_full = data['prodNameFull']
        self.device_type = data['dvcTypeCd']
        self.device_brand = data['dvcBrandCd']
        self.refresh()

    def refresh(self):
        try:
            control_status = self.api.control_status(self)
            mcu_version = self.api.mcu_version(self)
            if mcu_version['curMcuVer'] is not None:
                self.new_model = True
            else:
                self.new_model = False            
            self.device_connected_to_servers = self.api.network_status(self)
            self.is_on = control_status['0001'] == '1'
            self.is_auto = control_status['0002'] == '1'
            self.is_auto_eco = control_status['0002'] == '6'
            self.is_night = control_status['0002'] == '2'
            self.fan_speed = control_status['0003']
            self.is_light_on = control_status['0007'] == '2'
            self.timer = control_status['offTimerData']
            self.timer_remaining = control_status['0008']
            filters, quality, iaq = self.api.quality_status(self)
            fs = []
            for f in filters:
                fs.append({
                    'name': f['filterName'],
                    'life_level_pct': f['filterPer'],
                    'last_changed': f['lastChangeDate'],
                    'change_months': f['changeCycle']
                    })
            self.filters = fs
            self.quality = {}
            if len(quality) > 0:
                q = quality[0]
                self.quality['dust_pollution'] = q['dustPollution']
                self.quality['air_volume'] = q['airVolume']
                self.quality['pollen_mode'] = q['pollenMode']
            if len(iaq) > 0:
                q = iaq[0]
                self.quality['particulate_matter_2_5'] = q['dustpm25']
                self.quality['particulate_matter_10'] = q['dustpm10']
                self.quality['carbon_dioxide'] = q['co2']
                self.quality['volatile_organic_compounds'] = q['vocs']
                self.quality['air_quality_index'] = q['inairquality']
        except KeyError as e:
            return e
        except AttributeError:
            raise IoCareError(f'Unable to get info for {self.name}. Make sure purifier is connected to WiFi.')

    # True for On and False for Off
    def set_power(self, on):
        self.is_on = on
        self.api.control(self, '0001', '1' if on else '0')

    # True for On and False for Off
    def set_auto_mode(self):
        self.is_auto = True
        self.api.control(self, '0002', '1')

    # True for On and False for Off
    def set_night_mode(self):
        self.is_night = True
        self.api.control(self, '0002', '2')

    # Speed can be 1, 2, or 3 represented as a string
    def set_fan_speed(self, speed):
        self.fan_speed = speed
        self.is_auto = False
        self.is_night = False
        self.api.control(self, '0003', speed)

    # True for On and False for Off
    def set_light(self, on):
        self.is_light_on = on
        self.api.control(self, '0007', '2' if on else '0')

    # Time, in minutes, can be 0, 60, 120, 240, or 480 represented as a string. A time of 0 sets the timer to off.
    def set_timer(self, time):
        self.timer = time
        self.api.control(self, '0008', time)
