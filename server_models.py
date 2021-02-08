from traceback import print_tb
import requests
from requests.auth import HTTPBasicAuth
from uutinfo import Catuutinfo
import datetime
import sys
import json

class TaskServer(Catuutinfo):

    server = 'lab:8089'
    test = 'localhost:8000'

    uuts_url = f'http://{test}/api/uuts/'
    tasks_url = f'http://{test}/api/tasks/'
    scripts_url = f'http://{test}/api/scripts/'
    aps_url = f'http://{test}/api/aps/'
    task_status_url = f'http://{test}/api/taskstatus/'
    task_issue_url = f'http://{test}/api/taskissues/'

    def __init__(self,user,password):
        self.auth = HTTPBasicAuth(user,password)
        self._get_info()

    @property
    def get_uut(self):
        sn = self.info['bios'][0].SerialNumber
        r = requests.get(self.uuts_url,params={'sn':sn}).json()
        if r['count'] == 1 :return r['results']
        else:
            print('not found uut on server') 
            return None
        
    def get_script(self,script_name):
        r = requests.get(self.scripts_url,params={'name':script_name}).json()
        if r['count'] == 1: return r['results']
        else:
            print('not found script on server')
            return None

    def get_ap_by_ssid(self,ssid):
        r = requests.get(self.aps_url,params={'ssid':ssid}).json()
        if r['count'] == 1: return r['results']
        else:
            print('not found ssid on server')
            return None

    def get_taskstatus(self,status):
        r = requests.get(self.task_status_url,params={'status':status}).json()
        if r['count'] == 1: return r['results']
        else:
            print('not found status on server')
            return None

    def get_tasks_by_groupuuid(self,uuid):
        r = requests.get(self.aps_url,params={'group_uuid':uuid}).json()
        if r['count'] == 1: return r['results']
        else:
            print('not found group_uuid on server')
            return None

    def get_tasks_by_groupname(self,name):
        r = requests.get(self.aps_url,params={'group_name':name}).json()
        if r['count'] == 1: return r['results']
        else:
            print('not found group name on server')
            return None

    def add(self,script_name,group_uuid=None,group_name=None,ssid=None):
        sn = self.info['bios'][0].serialnumber
        script = script_name
        uutinfo = self.dump()
        r = requests.post(self.tasks_url,json={"sn":sn,"script":script,"ssid":ssid,"group_uuid":group_uuid,"group_name":group_name,"uut_info":uutinfo},auth = self.auth)
        print(r.status_code)#201
        return r

    def edit(self,task_id,script_name=None,status=None,ssid=None,group_uuid=None,group_name=None,uut_info=None,power_cycle_info=None,start=False,finish=False,log=None):
        data ={}
        script = script_name
        if start:
            data.update({'start_time':datetime.datetime.now()})
        if finish:
            data.update({'finish_time':datetime.datetime.now()})

        data.update({
            'script':script_name,
            'status':status,
            'group_uuid':group_uuid,
            'group_name':group_name,
            'ssid':ssid,
            'uut_info':uut_info,
            'power_cycle_info':power_cycle_info,
        })
        r = requests.put(self.tasks_url+rf'{task_id}/',data=data)
        print(r.status_code)#200
        return r

    @property
    def tasks(self):
        sn = self.info['bios'][0].serialnumber
        r = requests.get(self.tasks_url,params={'sn':sn})
        return r

    @property
    def current(self):
        sn = self.info['bios'][0].SerialNumber
        r = requests.get(self.tasks_url,params={"sn":sn,"task":"current"})
        pass


    def delete(self,task_id):
        r = requests.delete(self.tasks_url+rf'{task_id}/')
        print(r.status_code)#204
        return r

    #task status
    def run(self,task_id):
        self.edit(task_id,status='run',start=True)

    def run_error(self,task_id):
        self.edit(task_id,status='run_error')

    def finish(self,task_id):
        self.edit(task_id,status='finish',finish=True)

    def pause(self,task_id):
        self.edit(task_id,status='pause')

    def skip(self,task_id):
        self.edit(task_id,status='skip')

    def script_not_found(self,task_id):
        self.edit(task_id,status='script not found on local')

    def add_issue(self,task_id:int,title:str=None,level:str=None,power_state:str=None,device_driver:dict=None,function:str=None,description:str=None):
        data={
            'task':task_id,
            'title':title,
            'level':level,
            'power_state':power_state,
            'device_driver':device_driver,
            'function':function,
            'description':description
        }
        r = requests.post(self.task_issue_url,data=data)
        print(r.status_code)
        return r
    def edit_issue(self,issue_id):
        pass

    def delete_issue(self,issue_id):
        pass

    # def change(self,)

def testpost():
    task = TaskServer('admin','admin')
    r = task.add('Auto+Random')

def testedit():
    task = TaskServer('admin','admin')
    r = task.edit(4,finish=True)

def testdelete():
    task = TaskServer('admin','admin')
    r = task.delete(4)

def testcurrent():
    task = TaskServer('admin','admin')
    r = task.delete(4)

help='''
add                 
run                 
run_error                
finish              
pause               
skip                
script_not_found    
tasks               
current             
'''

def run():
    cmds = sys.argv
    cmds.pop(0)

def test():
    task = TaskServer('admin','admin')
    print(json.dumps(task.tasks.json(),indent=4))

if __name__ == '__main__':
    test()
