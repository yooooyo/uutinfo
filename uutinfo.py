import wmi
from json import loads,dumps
from os import path,popen
import sys
from re import findall
import argparse
import pythoncom
import pathlib


import threading
from time import sleep
class Info(threading.Thread):
  def __init__ (self,query):
    threading.Thread.__init__ (self)
    self.query = query
  def run(self):
    pythoncom.CoInitialize()
    try:
      c = wmi.WMI()
      self.instances = c.query(self.query)
    except Exception as e:
        print(e)
    finally:
      pythoncom.CoUninitialize()

class Catuutinfo():

    def __init__(self):
        '''
        Win32_BIOS
        Win32_ComputerSystem
        Win32_OperatingSystem
        Win32_PnPSignedDriver
        Win32_NetworkAdapter
        '''
    @property
    def _resource_path(self):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = path.abspath(".")
        return base_path

    def devquery_dict(self,query = None):
        if query:
            pass
        else:
            queryStrFile     = path.join(path.dirname(__file__),'DeviceQuery.json')
            queryStrFile_res = path.join(self._resource_path,'DeviceQuery.json')
            queryStrFile = queryStrFile_res if path.exists(queryStrFile_res) else queryStrFile
            if path.exists(queryStrFile):
                with open(queryStrFile,'r') as query:
                    print('Use DeviceQuery.json')
                    try:
                        query = query.read()
                        query = dict(loads(query))
                        base = ''
                        for k1,v1 in query.items():
                            if k1 != 'base':
                                values = []
                                for value in v1.values():
                                    v = r' or '.join(value)
                                    v = r'(' + v + r')' if v else v
                                    if v:
                                        values.append(v)
                                values = base + r' and '.join(values)
                                query.update({k1:values})
                            else:
                                base = v1
                        query.pop('base')
                        return query
                    except Exception as e:
                        print(e)
            else:
                print('Use default query string')
                query = {
                    'wlan': r"SELECT * FROM WIN32_PNPSIGNEDDRIVER WHERE ((deviceclass='net')) and ((description like '%intel%' and description like '%wireless%') or (description like '%intel%' and description like '%wi-fi%') or (description like '%realtek%' and description like '%802.11%'))",                
                    'modem': r"SELECT * FROM WIN32_PNPSIGNEDDRIVER WHERE ((deviceclass='System')) and ((Description like '%ModemControl%'))",                
                    'bordband': r"SELECT * FROM WIN32_PNPSIGNEDDRIVER WHERE ((deviceclass='net')) and ((Description like '%Mobile Broadband%'))",
                    'ude': r"SELECT * FROM WIN32_PNPSIGNEDDRIVER WHERE ((deviceclass='net') or (deviceclass='usb')) and ((Description like '%UDE%'))",                
                    "wwan_net":r"(deviceclass='net' and (Description like '%Mobile Broadband%'))",
                    'gnss': r"SELECT * FROM WIN32_PNPSIGNEDDRIVER WHERE ((deviceclass='system') or (deviceclass='sensor')) and ((Description like '%GNSS%'))",
                    'qmux': r"SELECT * FROM WIN32_PNPSIGNEDDRIVER WHERE ((deviceclass='system')) and ((Description like '%QMUX%'))",                
                    'nfc': r"SELECT * FROM WIN32_PNPSIGNEDDRIVER WHERE ((deviceclass='Proximity'))",
                    'rfid': r"SELECT * FROM WIN32_PNPSIGNEDDRIVER WHERE ((deviceclass='HIDClass')) and ((HardWareID like '%0C27%'))"
                }
        return query

    def update_device_query(self):
        pass

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
        self.drivers = dict()
        for k,v in self.devquery_dict().items():
            instance = Info(v)
            instance.start()
            self.drivers.update({k:instance})

        for k,v in self.drivers.items():
            v.join()
            self.drivers.update({k:v.instances})

        

    # def _get_drivers_pool(self):
    #     pythoncom.CoInitialize()
    #     tasks = {k:threading.Thread(target = wmi.WMI().query,args=(self.devquery_dict()['base']+v,)) for k,v in self.devquery_dict().items() if k != 'base'}
        
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
        data = findall('\s*Firmware\s*Version\s*:\s*(.+)\s*',popen('netsh mbn sh inter').read())
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
        data.update({'firmware':self._get_wwan_firmware})
        merge=['wwan_root','modem','bordband','ude','gnss','qmux','firmware']
        wwan = {}
        for i in merge:
            wwan.update({i:data.pop(i)})
        data.update({'wwan':wwan})
        return data
    
    def dump_to_json(self):
        return dumps(self.dump(),indent=4)

    def query_to_json(self):
        return dumps(self.devquery_dict(),indent=4)

    def to_csv(self,filename='uutinfo.csv'):
        self.get_all_info()
        with open(filename,'w+') as f:
            f.write(dumps(self.dump(),indent=4))

    def query_save_to_json(self,file_name='DeviceQuery.json',data=None):
        data = self.query_to_json()
        with open(file_name,'w+') as f:
            f.write(data)
            print(f'output: {path.realpath(f.name)}')

    def dump_save_to_json(self,filename='uutinfo.json',data = None):
        if not data:
            data = self.dump_to_json()
        with open(filename,'w+') as f:
            f.write(data)
            print(f'output: {path.realpath(f.name)}')

    



def run():
    catuut = Catuutinfo()    
    catuut.to_json()
    # try:
    #     m = Member.get(Member.user==7)
    #     print(m.usernameincompany)
    # except Exception as e:
    #     print(e)
    # print('hello')
        
help='''
dump                |  print uutinfo data
dump                |  print uutinfo data
query               |  print wmi query string
export json         |  export uutinfo data as json file
       query-json   |  export wmi query string as json file
'''


def run():
    uutinfo = Catuutinfo()
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(title = 'UUT INFO',dest='cmd')
    dump_parser = subparser.add_parser('dump',help='print or export module info')
    dump_parser.add_argument('-export',help='export module info as json data',action='store_true')
    query_parser = subparser.add_parser('query',help='print query string')
    query_parser.add_argument('-export',help='export query stringas json data',action='store_true')
    args = parser.parse_args()

    if args.cmd == 'dump':
        data = uutinfo.dump_to_json()
        print(data)
        if args.export:
            uutinfo.dump_save_to_json(dump=data)
    elif args.cmd == 'query':
        data = uutinfo.query_to_json()
        print(data)
        if args.export:
            uutinfo.query_save_to_json(data=data)

def test():
    # print('In Main Thread')
    # c = wmi.WMI()
    # Info().start()
    # for process in c.Win32_Process():
    #     print('M',process.ProcessId, process.Name)

    # info = Catuutinfo()
    # info._get_drivers()
    # print(info.drivers)
    # query = Catuutinfo().devquery_dict()
    # instances = []
    # for v in query.values():
    #     instance = Info(v)
    #     instances.append(instance)
    #     instance.start()
    uutinfo = Catuutinfo()
    # uutinfo.get_all_info()
    data = dumps(uutinfo.dump(),indent=4)
    print(data)
    
if __name__ == "__main__":
    run()
    

    





            



            
