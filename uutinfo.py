from os.path import expanduser
from sys import argv
from win32com.client.gencache import __init__
import wmi
import json
import os
import re
import pprint

class Catuutinfo:

    def __init__(self):
        '''
        Win32_BIOS
        Win32_ComputerSystem
        Win32_OperatingSystem
        Win32_PnPSignedDriver
        Win32_NetworkAdapter
        '''
        '''
        wwan case:
        ude
        modem
        qmux (mostly Qualcomm) above gnss
        gnss
        '''

    @property
    def devquery_dict(self):
        query = None
        devicequery = os.path.join(os.path.dirname(__file__),'DeviceQuery.json')
        if os.path.exists(devicequery):
            with open(devicequery) as devquery:
                try:
                    query = json.loads(devquery.read())
                except Exception as e:
                    print(e)
        else:
            query = {
                "base":r"SELECT * FROM WIN32_PNPSIGNEDDRIVER WHERE ",
                "wlan":r"(deviceclass='net' and ((description like '%intel%' and description like '%wireless%') or (description like '%intel%' and description like '%wi-fi%') or (description like '%realtek%' and description like '%802.11%')))",
                "modem":r"(deviceclass='System' and  (Description like '%ModemControl%'))",
                "wwan_cat":r"(deviceclass='System' and  (Description like '%7360%' or Description like '%7560%' or Description like '%xmm%'))",
                "lan":r"(deviceclass='net' and ((description like '%intel%' and description like '%ethernet%') or (description like '%realtek%' and description like '%gbe%')))",
                "wwan_net":r"(deviceclass='net' and (Description like '%Mobile Broadband%'))",
                "ble":r"(deviceclass='Bluetooth' and ((description like '%intel%') or (description like '%realtek%')))",
                "nfc":r"(deviceclass='Proximity')",
                "rfid":r"(deviceclass='HIDClass' and HardWareID like '%0C27%')",
                "gnss":r"(deviceclass='Sensor' and DeviceName like '%GNSS%')"
            }
        return query

    def _get_info(self):
        w  =  wmi.WMI()
        self.target_wmi_classes = {
            'bios':'Win32_BIOS',
            'cs':'Win32_ComputerSystem',
            'os':'Win32_OperatingSystem',
        }
        self.target_wmi_class_properties_list = {
            'bios':['Caption','SerialNumber'],
            'cs':['Model','OEMStringArray','SystemSKUNumber'],
            'os':['Version','OSArchitecture'],
        }
        self.wmi_class_where_conditions={
            'bios':{},
            'cs':{},
            'os':{},
        }
        self.info = {key:getattr(w,value)(self.target_wmi_class_properties_list[key],**self.wmi_class_where_conditions[key]) for key,value in self.target_wmi_classes.items()}

    def _get_drivers(self):
        w  =  wmi.WMI()
        self.drivers = {k:w.query(self.devquery_dict['base']+v) for k,v in self.devquery_dict.items() if k != 'base'}

    # def _get_drivers_pool(self):
    #     pythoncom.CoInitialize()
    #     tasks = {k:threading.Thread(target = wmi.WMI().query,args=(self.devquery_dict['base']+v,)) for k,v in self.devquery_dict.items() if k != 'base'}
        
    #     _ = [task.start() for task in tasks.values()]
    #     _ = [task.join() for task in tasks.values()]
    #     tasks
    #     pythoncom.CoUninitialize()
    def get_all_info(self):
        self._get_info()
        import datetime
        now = datetime.datetime.now
        start = now()
        self._get_drivers()
        finish = now()
        print(f'elapse {(finish-start).seconds}s')

    @property
    def _get_wwan_firmware(self):
        data = re.findall('Firmware Version       :(.+)\s',os.popen('netsh mbn sh inter').read())
        if data:
            return data[0].strip()
        else:
            return ''
    def print_properties(self,wmi_object:wmi._wmi_object):
        for p in wmi_object.properties:
            v = getattr(wmi_object,p)
            if v:
                print(p,v)

    def dump(self):
        self.get_all_info()
        data = dict()
        convert = lambda x:{typ:{cnt:{p:getattr(obj,p,None) for p in obj.properties} for cnt,obj in enumerate(objs)} for typ,objs in x.items()}
        data.update(convert(self.info))
        data.update(convert(self.drivers))
        if data.get('wwan_net',None):
            data['wwan_net'][0].update({'Firmware':self._get_wwan_firmware})
        data.update({'wwan':{'wwan_cat':data.pop('wwan_cat')}})
        data['wwan'].update({'wwan_net':data.pop('wwan_net')})
        data['wwan'].update({'modem':data.pop('modem')})
        return data

    def to_csv(self,filename='uutinfo.csv'):
        self.get_all_info()
        with open(filename,'w+') as f:
            f.write(json.dumps(self.dump(),indent=4))

    def query_to_json(self):
        content = json.dumps(self.devquery_dict,indent=4)
        with open('DeviceQuery.json','w+') as f:
            f.write(content)
            print(f'output: {os.path.realpath(f.name)}')

    def to_json(self,filename='uutinfo.json'):
        with open(filename,'w+') as f:
            f.write(json.dumps(self.dump(),indent=4))
            print(f'output: {os.path.realpath(f.name)}')

# def run():
#     catuut = Catuutinfo()    
#     catuut.to_json()
#     # try:
#     #     m = Member.get(Member.user==7)
#     #     print(m.usernameincompany)
#     # except Exception as e:
#     #     print(e)
#     # print('hello')
        
help='''
dump                |  print uutinfo data
dump                |  print uutinfo data
query               |  print wmi query string
export json         |  export uutinfo data as json file
       query-json   |  export wmi query string as json file
'''


if __name__ == "__main__":
    cmds=['help','export','query','dump']
    pp = pprint.PrettyPrinter(indent=4)
    if argv and len(argv)>1 and argv[1] in cmds:
        if argv[1] == 'export':
            if argv[2] in ['json','query-json']:
                if argv[2] == 'json':
                    Catuutinfo().to_json()
                elif argv[2] == 'query-json':
                    Catuutinfo().query_to_json()
        elif argv[1] == 'dump':
            pp.pprint(Catuutinfo().dump())
        elif argv[1] == 'query':
            pp.pprint(Catuutinfo().devquery_dict)
        else:
            print(help)
    else:
        print(help)

query = 
'''
{
    "base":"SELECT * FROM WIN32_PNPSIGNEDDRIVER WHERE ",
    "wlan":{
        "class":["deviceclass='net'"],
        "intel":[
            "description like '%intel%' and description like '%wireless%'",
            "description like '%intel%' and description like '%wi-fi%'"
        ],
        "realtek":[
            "description like '%realtek%' and description like '%802.11%'"
        ]
    },
    "modem":{
        "class":["deviceclass='System'"],
        "modem":[
            "Description like '%ModemControl%'"
        ]
    },
    "bordband":{
        "class":["deviceclass='net'"],
        "bordband":[
            "Description like '%Mobile Broadband%'"
        ]
    },
    "ude":{
        "class":["deviceclass='net'","deviceclass='usb'"],
        "bordband":[
            "Description like '%UDE%'"
        ]
    },
    "gnss":{
        "class":["deviceclass='net'","deviceclass='usb'"],
        "bordband":[
            "Description like '%UDE%'"
        ]
    },
    "qmux":{
        "class":["deviceclass='net'","deviceclass='usb'"],
        "bordband":[
            "Description like '%UDE%'"
        ]
    },
    "wwan_root":{
        "class":["deviceclass='sample'","deviceclass='usb'"],
        "bordband":[
            "Description like '%UDE%'"
        ]
    },
    "nfc":{
        "class":[],
        "nfc":[

        ]
    },
    "rfid":{
        "class":[],
        "rfid":[
            
        ]
    }
}
'''
    

    





            



            
