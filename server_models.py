import requests
from uutinfo import Catuutinfo
import datetime
import uuid

class TaskServer(Catuutinfo):

    uuts_url = 'http://127.0.0.1:8000/api/uuts/'
    tasks_url = 'http://127.0.0.1:8000/api/tasks/'
    scripts_url = 'http://127.0.0.1:8000/api/scripts/'
    aps_url = 'http://127.0.0.1:8000/api/aps/'
    task_status_url = 'http://127.0.0.1:8000/api/taskstatus/'

    def __init__(self):
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

    def add(self,script_name,status='wait',assigner=None,task_group=None,power_cycle_info=None,ap=None):
        uut = self.get_uut
        script = self.get_script(script_name)
        task_status = self.get_taskstatus(status)
        uutinfo = self.dump()
        start_time = datetime.datetime.now()
        series=None
        if not task_group:
            task_group = uuid.uuid4()
        else:
            tasks = self.get_task_by_taskgroup(task_group)
            if tasks:
                task_group = tasks[0]['task_group'] 
                series = max([task['group_series'] for task in tasks]) + 1
        
        


        r = requests.post(self.tasks_url,data={"uut":uut,"script":script,"status":task_status,"ap":ap,"assigner":assigner,"task_group":task_group,"group_series":series})
        print(r)

    # def change(self,)


if __name__ == '__main__':
    task = Task()
    # print(task.get_script('Interface+Web+Random'))
    r = requests.put(task.task_status_url,data={"id":7,"task_status":"QUICK"})
    print(r.json())
    print(r.content)
