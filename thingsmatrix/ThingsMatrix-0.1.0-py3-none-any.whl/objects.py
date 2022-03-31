
from fnmatch import translate
from typing import List
from requests import Response,Session,Request
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.text import Text
from enum import Enum


console = Console()
datetime_formatter_one = "%Y-%m-%d %H:%M:%S"
datetime_formatter_two = "%Y-%m-%dT%H:%M:%SZ"



class ThingsMatrixResponse():
    
    code = None
    data = None
    msg = None
    
    __rawData = None
    
    def __init__(self,response:Response) -> None:
        self.status_code = response.status_code
        self.__response = response
        
        if self.status_code == 200:
            self.__rawData = self.__response.json()
            self.code = self.__rawData.get('code',None)
            self.data = self.__rawData.get('data',None)
            self.msg = self.__rawData.get('msg',None)
    
    @property
    def hasData(self) -> bool:
        return self.code == 0 and self.status_code == 200 and self.data
    
    @property
    def hasNoData(self)-> bool:
        return self.code != 0 and self.status_code == 200 and ~self.data
    
            
        
            
class deviceStatus(Enum):
    # "-1: suspended";
    # "0: disabled";
    # "1: offline";
    # "2: online";
    # "3: standby";
    # "4: tracking";
    # "5: inactive"
    suspended = -1
    disabled = 0
    offline = 1
    online = 2
    standby = 3
    tracking = 4
    inactive = 5
    
class Device:
        
    def __init__(self,device_content:dict) -> None:
        self.__json = device_content
        self.alias = device_content.get('alias',None)
        self.attributes = device_content.get('attributes',None)
        self.cerOverwrite = device_content.get('cerOverwrite',None)
        self.certificate = device_content.get('certificate',None)
        self.createTime = device_content.get('createTime',None)
        if self.createTime:
            self.createTime = datetime.strptime(self.createTime,datetime_formatter_one)
        self.creator = device_content.get('creator',None)
        self.description = device_content.get('description',None)
        self.group = device_content.get('group',None)
        if self.group:
            self.group = Group(self.group)
        self.iccid = device_content.get('iccid',None)
        self.id = device_content.get('id',None)
        self.imei = device_content.get('imei',None)
        self.model = device_content.get('model',None)
        if self.model:
            self.model = Model(self.model)
        self.pid = device_content.get('pid',None)
        self.sn = device_content.get('sn',None)
        self.sensorOverwrite = device_content.get('sensorOverwriteodel',None)
        self.sensorSn = device_content.get('sensorSn',None)
        self.status = deviceStatus(device_content.get('status',None))
        self.tags = device_content.get('tags',None)
        self.tempOverwrite = device_content.get('tempOverwrite',None)
        self.template = device_content.get('template',None)
        self.updateTime = device_content.get('updateTime',None)
        self.updator = device_content.get('updator',None)
        self.latest = device_content.get('latest',None)
        if self.latest:
            self.latest = Report(self.latest)
            
    @property
    def json(self):
        return self.__json
    
    def printJson(self):
        console.print_json(data=self.json)
    
    def get_latest(self):
        ...
        return self.latest
    
    def __repr__(self):
        table = Table(show_header=True,header_style="bold magenta")
        table.add_column('id')
        table.add_column('sn')
        table.add_column('imei')
        table.add_column('iccid')
        table.add_column('status')
        table.add_column('creator')
        table.add_column('create time')
        table.add_column('update time')
        table.add_column('model')
        table.add_column('group')
        table.add_column('pid')
        table.add_row(
            self.id,
            self.sn,
            self.imei,
            self.iccid,
            self.status.name,
            self.creator,
            str(self.createTime),
            self.updateTime,
            self.model.name,
            self.group.name,
            self.pid,
        )
        console.print(table)
        return ''
    
    def is_recently(self):
        ...
    
class Devices(list):
    ...
    def __init__(self) -> None:
        pass
    
    def append(self, __object: Device) -> None:
        return super().append(__object)

    
class Group:
    ...
    def __init__(self,group_dict) -> None:
        self.id = group_dict.get('id',None)
        self.name = group_dict.get('name',None)
        
class Model:
    ...
    def __init__(self,model_dict) -> None:
        self.id = model_dict.get('id',None)
        self.name = model_dict.get('name',None)
        
class Company:
    ...
    def __init__(self) -> None:
        pass

class Location:
    pass
    

class Report:
    ...
    def __init__(self,report_dict) -> None:
        self.chargeFlag = report_dict.get('chargeFlag',None)
        self.eid = report_dict.get('eid',None)
        self.ver = report_dict.get('ver',None)
        self.reportLatency = report_dict.get('reportLatency',None)
        self.iccidChange = report_dict.get('iccidChange',None)
        self.pc_vendor = report_dict.get('pc_vendor',None)
        self.prev_report_time = report_dict.get('prev_report_time',None)
        self.systemTime = report_dict.get('systemTime',None)
        self.mfg = report_dict.get('mfg',None)
        self.fw = report_dict.get('fw',None)
        self.iccid = report_dict.get('iccid',None)
        self.vendor = report_dict.get('vendor',None)
        self.imei = report_dict.get('imei',None)
        self.timeInterval = report_dict.get('timeInterval',None)
        self.model = report_dict.get('model',None)
        self.time = report_dict.get('time',None)
        self.power = report_dict.get('power',None)
        self.sn = report_dict.get('sn',None)
        self.prev_info_time = report_dict.get('prev_info_time',None)
        self.ipaddr = report_dict.get('ipaddr',None)
        self.net = report_dict.get('net',None)
        self.cellid = report_dict.get('cellid',None)
        self.lac = report_dict.get('lac',None)
        self.mcc = report_dict.get('mcc',None)
        self.mnc = report_dict.get('mnc',None)
        self.rssi = report_dict.get('rssi',None)
        self.battery = report_dict.get('battery',None)
        self.prev_report_time = report_dict.get('prev_report_time',None)
        
    @property
    def columns(self):
        columns = [
            'sn',
            'ipaddr',
            'net',
            'cellid',
            'lac',
            'mcc',
            'mnc',
            'rssi',
            'power',
            'battery',
            'timeInterval',
            'prev report time',
            'time',
        ]
        return columns
    
    @property
    def dataRow(self):
        data = [
            self.sn,
            self.ipaddr,
            self.net,
            str(self.cellid),
            str(self.lac),
            str(self.mcc),
            str(self.mnc),
            str(self.rssi),
            str(self.power),
            str(self.battery),
            str(self.timeInterval),
            self.prev_report_time,
            self.time,
        ]
        return data
    
    @property
    def table(self):
        table = Table(show_header=True,header_style="bold magenta")
        for c in self.columns:
            table.add_column(c)
        table.add_row(*self.dataRow)
        return table
    
    @property
    def columns(self):
        columns = [
            'sn',
            'ipaddr',
            'net',
            'cellid',
            'lac',
            'mcc',
            'mnc',
            'rssi',
            'power',
            'battery',
            'timeInterval',
            'prev report time',
            'time',
        ]
        return columns
    
    def __repr__(self) -> str:
        ...
        console.print(self.table)
        return ''

class Reports(list):
    
    def __init__(self,reports:List[Report]) -> None:
        self.__reports = reports
    
    def append(self, __object: Report) -> None:
        return super().append(__object)
    
    @property
    def table(self):
        table = Table(show_header=True,header_style="bold magenta")
        for c in self.columns:
            table.add_column(c)
        for row in self.dataRows:
            table.add_row(*row)
        return table
    
    @property
    def dataRows(self):
        rows = [
            report.dataRow for report in self.__reports
        ]
        return rows
        
    def __repr__(self) -> str: 
        console.print(self.table)
        
        return ''
    
class Event:
    ...
    
class Events(list):
    ...
    
class Pages:
    
    def __init__(self,response:Response) -> None:
        if response.ok and response.status_code == 200:
            data = response.json()
            self.response = response
            self.code = data.get('code',None)
            self.msg = data.get('msg',None)
            if self.code == 0 and self.msg == 'success':
                self.datas = data.get('data',None)
                self.content = []
                if self.datas.get('content',None):
                    self.content = self.datas['content']
                self.number = self.datas.get('number',None)
                self.size = self.datas.get('size',None)
                self.totalElements = self.datas.get('totalElements',None)
                self.totalPages = self.datas.get('totalPages',None)
                self.sort = self.datas.get('sort',None)
                self.last = self.datas.get('last',None)
                self.first = self.datas.get('first',None)
                self.timestamp = data.get('first',None)
            else:
                raise BaseException(self.msg)
        
    def collect_contents(self, useClass,params:dict=None):
        ...
        
        if len(self.content) < self.totalElements:
        # server max get size = 2000
        # if oversize then need to query by page
            with Session() as session:
                prerequest = self.response.request
                if params:
                    params.update({'size':self.totalElements})
                prerequest.prepare_url(prerequest.url[:prerequest.url.index('?')],params)
                response = session.send(prerequest)
                page = Pages(response)
                self.content = page.content
            return response,[useClass(obj) for obj in self.content]
        elif self.number == self.totalPages == 1: #just one page
            if self.totalElements == 1:
                return self.response,[useClass(self.content[0])]
            else:
                return self.response,[useClass(obj) for obj in self.content]
            
        return None, None
       
            

        
        
    
    
    

        