import requests
from requests.auth import HTTPBasicAuth
from uutinfo import Catuutinfo
import datetime
import uuid

class TaskServer(Catuutinfo):

    uuts_url = 'http://127.0.0.1:8000/api/uuts/'
    tasks_url = 'http://127.0.0.1:8000/api/tasks/'
    scripts_url = 'http://127.0.0.1:8000/api/scripts/'
    aps_url = 'http://127.0.0.1:8000/api/aps/'
    task_status_url = 'http://127.0.0.1:8000/api/taskstatus/'

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

    def get_task_by_taskgroup(self,uuid):
        r = requests.get(self.aps_url,params={'task_group':uuid}).json()
        if r['count'] == 1: return r['results']
        else:
            print('not task group on server')
            return None

    def add(self,script_name,task_group=None,ssid=None):
        sn = self.info['bios'][0].serialnumber
        script = script_name
        uutinfo = self.dump()
        r = requests.post(self.tasks_url,json={"sn":sn,"script":script,"ssid":ssid,"task_group":task_group,"uut_info":uutinfo},auth = self.auth)
        print(r.status_code)#200
        return r

    def edit(self,task_id,script_name=None,task_group=None,group_series=None,uut_info=None,power_cycle_info=None,start=False,finish=False,log=None):
        data ={}
        script = script_name
        if start:
            data.update({'start_time':datetime.datetime.now()})
        if finish:
            data.update({'finish_time':datetime.datetime.now()})

        data.update({
            'script':script_name,
            'task_group':task_group,
            'group_series':group_series,
            'uut_info':uut_info,
            'power_cycle_info':power_cycle_info,
        })
        r = requests.put(self.tasks_url+rf'{task_id}/',data=data)
        print(r.status_code)#200
        return r

    def delete(self,task_id):
        r = requests.delete(self.tasks_url+rf'{task_id}/')
        print(r.status_code)#204
        return r

    def add_issue(self,task_id):
        pass

    def edit_issue(self,issue_id):
        pass

    def delete_issue(self,issue_id):
        pass


    # def change(self,)

def testpost():
    task = TaskServer('admin','admin')
    r = task.add('Interface+Web+om')

def testedit():
    task = TaskServer('admin','admin')
    r = task.edit(4,finish=True)

def testedit():
    task = TaskServer('admin','admin')
    r = task.delete(4)

if __name__ == '__main__':
    testedit()
