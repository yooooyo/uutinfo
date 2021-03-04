from traceback import print_tb
import requests
from requests import auth
from requests.auth import HTTPBasicAuth
from uutinfo import Catuutinfo
import datetime
import sys
import json
import argparse

class TaskServer(Catuutinfo):

    server = 'lab:8089'
    test = 'localhost:8000'

    uuts_url = f'http://{server}/api/uuts/'
    tasks_url = f'http://{server}/api/tasks/'
    scripts_url = f'http://{server}/api/scripts/'
    aps_url = f'http://{server}/api/aps/'
    task_status_url = f'http://{server}/api/taskstatus/'
    task_issue_url = f'http://{server}/api/taskissues/'

    def __init__(self,user,password):
        self.auth = HTTPBasicAuth(user,password)
        self._get_info()

    def _print_status_json(self,r:requests):
        print(r.status_code)
        print(json.dumps(r.json(),indent=4))

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
    @property
    def get_scripts(self):
        r = requests.get(self.scripts_url,params={'scripts':'scripts'}).json()
        scripts = []
        while True:
            scripts.extend([script['name'] for script in r['results']])
            if not r['next']: break
            r = requests.get(r['next']).json()
        else:
            print('not found scripts on server')
            return None
        return scripts

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

    def add(self,script_name,status='wait',group_uuid=None,group_name=None,ssid=None):
        sn = self.info['bios'][0].serialnumber
        script = script_name
        uutinfo = self.dump()
        start_time=None if not (status=='run') else str(datetime.datetime.now())
        r = requests.post(self.tasks_url,json={"sn":sn,"script":script,"status":status,"ssid":ssid,"group_uuid":group_uuid,"group_name":group_name,"uut_info":uutinfo,"start_time":start_time},auth = self.auth)
        self._print_status_json(r)
        return r

    def edit(self,task_id=None,script_name=None,status=None,ssid=None,group_uuid=None,group_name=None,uutinfo:bool=False,power_cycle_info=None,start=False,finish=False,log=None):
        data ={}
        if not task_id:
            task_id = self.get_current_id
        script = script_name
        if start:
            data.update({'start_time':datetime.datetime.now()})
        if finish:
            data.update({'finish_time':datetime.datetime.now()})
        if uutinfo:
            uutinfo = self.dump()
            uutinfo = json.dumps(uutinfo)
        else:
            uutinfo =None
        data.update({
            'script':script,
            'status':status,
            'group_uuid':group_uuid,
            'group_name':group_name,
            'ssid':ssid,
            'uut_info':uutinfo,
            'power_cycle_info':power_cycle_info,
        })
        r = requests.put(self.tasks_url+rf'{task_id}/',data=data,auth=self.auth)
        self._print_status_json(r)
        return r

    @property
    def tasks(self):
        sn = self.info['bios'][0].serialnumber
        r = requests.get(self.tasks_url,params={'sn':sn})
        self._print_status_json(r)
        return r

    @property
    def current(self):
        sn = self.info['bios'][0].SerialNumber
        r = requests.get(self.tasks_url,params={"sn":sn,"task":"current"})
        self._print_status_json(r)
        return r


    def delete(self,task_id):
        r = requests.delete(self.tasks_url+rf'{task_id}/',auth=self.auth)
        print(r.status_code)
        #204  no resource
        return r

    #task status
    def run(self,task_id):
        return self.edit(task_id,status='run',start=True)

    @property
    def get_current_id(self):
        current = self.current.json()
        if current.get('count',None) == 1:
            return current['results'][0]['id']
        return None

    def run_error(self,task_id=None):
        if not task_id:
            task_id = self.get_current_id
        return self.edit(task_id,status='run_error')

    def finish(self,task_id=None):
        if not task_id:
            task_id = self.get_current_id
        return self.edit(task_id,status='finish',finish=True)

    def pause(self,task_id=None):
        if not task_id:
            task_id = self.get_current_id
        return self.edit(task_id,status='pause')

    def skip(self,task_id=None):
        if not task_id:
            task_id = self.get_current_id
        return self.edit(task_id,status='skip')

    def script_not_found(self,task_id=None):
        if not task_id:
            task_id = self.get_current_id
        return self.edit(task_id,status='script not found on local')

    def add_issue(self,task_id:int=None,title:str=None,level:str=None,power_state:str=None,device_driver:str=None,function:dict=None,description:str=None):
        task_id = self.get_current_id if not task_id else task_id
        device_driver_info = self.dump()
        select_device = device_driver_info.get(device_driver,None)
        device_driver = device_driver_info if not select_device else select_device
        data={
            'task':task_id,
            'title':title,
            'level':level,
            'power_state':power_state,
            'device_driver':device_driver,
            'function':function,
            'description':description
        }
        r = requests.post(self.task_issue_url,json=data,auth=self.auth)
        self._print_status_json(r)
        return r

    def edit_issue(self,issue_id,title:str=None,level:str=None,power_state:str=None,device_driver:str=None,function:str=None,description:str=None):
        device_driver_info = self.dump()
        select_device = device_driver_info.get(device_driver,None)
        device_driver = device_driver_info if not select_device else select_device
        data={
            'title':title,
            'level':level,
            'power_state':power_state,
            'device_driver':device_driver,
            'function':function,
            'description':description
        }
        r = requests.put(self.task_issue_url+f'{issue_id}/',auth=self.auth,json=data)
        self._print_status_json(r)
        return r

    def delete_issue(self,issue_id):
        r = requests.delete(self.task_issue_url+f'{issue_id}/',auth=self.auth)
        self._print_status_json(r)
        return r

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

def testaddissue():
    task = TaskServer('admin','admin')
    r = task.add_issue(task_id=17,power_state='S0')
    print(json.dumps( r.json(),indent=4))

def testeditissue():
    task = TaskServer('admin','admin')
    r = task.edit_issue(issue_id=5,power_state='S4',level='Critical')
    print(json.dumps( r.json(),indent=4))

def testdeleteissue():
    task = TaskServer('admin','admin')
    r = task.delete_issue(issue_id=4)
    if r.status_code != 204:
        print(json.dumps( r.json(),indent=4))

def testgetscripts():
    task = TaskServer('admin','admin')
    scripts = task.get_scripts
    print(scripts)

def test():
    testgetscripts()

def main():
    task = TaskServer('admin','admin')
    scripts = task.get_scripts
    parser = argparse.ArgumentParser()

    sub_parsers = parser.add_subparsers(title='TASK',dest = 'cmd')
    add_parsers = sub_parsers.add_parser('create',help='create a task')
    add_parsers.add_argument('script',type=str,help='script name',choices=scripts)
    add_parsers.add_argument('-ssid',type=str,help='wifi ssid')
    add_parsers.add_argument('-status',type=str,help='task status',choices=['run','wait','finish','pause','skip','script not found','run error'],default='wait')
    addtask_exclu_gro = add_parsers.add_mutually_exclusive_group()
    addtask_exclu_gro.add_argument('-group_uuid',type=str,help='add a task to a task group by group uuid')
    addtask_exclu_gro.add_argument('-group_name',type=str,help='add a task to a task group by group name')
    addtask_exclu_gro.add_argument('-run',action='store_true',help='create a task then set status to run')

    edit_parsers = sub_parsers.add_parser('update',help='update a task')
    edit_parsers.add_argument('-id',type=int,help='task id')
    edit_parsers.add_argument('-script',type=str,help='script name',choices=scripts)
    edit_parsers.add_argument('-status',type=str,help='task status',choices=['run','wait','finish','pause','skip','script not found','run error'])
    edit_parsers.add_argument('-ssid',type=str,help='wifi ssid')
    edit_parsers.add_argument('-uutinfo',help='unit info format as json',action='store_true')
    edit_parsers.add_argument('-power_cycle_info',type=str,help='unit power cycle info format as json')
    edit_parsers.add_argument('-start',type=bool,help='change task status start')
    edit_parsers.add_argument('-finish',type=bool,help='change task status finish')
    edittask_exclu_gro = edit_parsers.add_mutually_exclusive_group()
    edittask_exclu_gro.add_argument('-group_uuid',help='group uuid')
    edittask_exclu_gro.add_argument('-group_name',help='group name')

    edit_parsers = sub_parsers.add_parser('delete',help='delete a task')
    edit_parsers.add_argument('id',help='task id')

    edit_parsers = sub_parsers.add_parser('run',help='report run a task')
    edit_parsers.add_argument('id',help='task id')

    edit_parsers = sub_parsers.add_parser('run_error',help='report a task run error when starting or running')
    edit_parsers.add_argument('-id',help='task id')

    edit_parsers = sub_parsers.add_parser('finish',help='report a task finish')
    edit_parsers.add_argument('-id',help='task id')

    edit_parsers = sub_parsers.add_parser('pause',help='report a task pause')
    edit_parsers.add_argument('-id',help='task id')

    edit_parsers = sub_parsers.add_parser('skip',help='report a task be skipped')
    edit_parsers.add_argument('-id',help='task id')

    edit_parsers = sub_parsers.add_parser('script_not_found',help='report a script not found in local')
    edit_parsers.add_argument('-id',help='task id')

    issuecreate_parsers = sub_parsers.add_parser('issuecreate',help='create a issue')
    issuecreate_parsers.add_argument('-id',help='task id')
    issuecreate_parsers.add_argument('-title',help='issue title')
    issuecreate_parsers.add_argument('-level',help='issue level')
    issuecreate_parsers.add_argument('-power_state',help='what power state occur issue',choices=['s0','s0i3','s3','s4','s5','g3','restart'])
    device_choices = ['wlan','bt','wwan','lan','nfc','rfid','all']
    issuecreate_parsers.add_argument('-device_driver',help='what device and driver occur issue',choices=device_choices)
    issuecreate_parsers.add_argument('-function',help='what function issues occur, format as json')
    issuecreate_parsers.add_argument('-description',help='issue description')   

    issueupdate_parsers = sub_parsers.add_parser('issueupdate',help='update issue info')
    issueupdate_parsers.add_argument('id',help='issue id')
    issueupdate_parsers.add_argument('-title',help='issue title')
    issueupdate_parsers.add_argument('-level',help='issue level')
    issueupdate_parsers.add_argument('-power_state',help='what power state occur issue',choices=['s0','s0i3','s3','s4','s5','g3','restart'])
    issueupdate_parsers.add_argument('-device_driver',help='what device and driver occur issue',choices=device_choices)
    issueupdate_parsers.add_argument('-function',help='what function issues occur, format as json')
    issueupdate_parsers.add_argument('-description',help='issue description')

    sub_parsers.add_parser('list',help='list tasks')
    sub_parsers.add_parser('current',help='list current task')
    # sub_parsers.add_parser('scripts',help='list scripts')

    args = parser.parse_args()
    pass_code_list = [200,201,204]

    if args.cmd == 'create':
        status = args.status
        if args.run:
            status = 'run'
        r = r = task.add(args.script,status,args.group_uuid,args.group_name,args.ssid)
    elif args.cmd =='update':
        r = task.edit(args.id,args.script,args.status,args.ssid,args.group_uuid,args.group_name,args.uutinfo,args.power_cycle_info,args.start,args.finish)
    elif args.cmd == 'delete':
        r = task.delete(args.id)
    elif args.cmd == 'run':
        r = task.run(args.id)
    elif args.cmd == 'run_error':
        r = task.run_error(args.id)
    elif args.cmd == 'finish':
        r = task.finish(args.id)
    elif args.cmd == 'pause':
        r = task.pause(args.id)
    elif args.cmd == 'skip':
        r = task.skip(args.id)
    elif args.cmd == 'script_not_found':
        r = task.script_not_found(args.id)
    elif args.cmd == 'list':
        r = task.tasks
    elif args.cmd == 'current':
        r = task.current
    elif args.cmd == 'issuecreate':
        r = task.add_issue(args.id,args.title,args.level,args.power_state,args.device_driver,args.function,args.description)
    elif args.cmd == 'issueupdate':
        r = task.edit_issue(args.id,args.title,args.level,args.power_state,args.device_driver,args.function,args.description)
        
    if r.status_code in pass_code_list:
        sys.exit(0)
    else:
        sys.exit(r.status_code)
        
if __name__ == '__main__':
    main()
    # test()