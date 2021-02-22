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
        self._print_status_json(r)
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
        ret = r.status_code == 204
        return ret

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
        r = requests.post(self.task_issue_url,data=data,auth=self.auth)
        self._print_status_json(r)
        return r

    def edit_issue(self,issue_id,title:str=None,level:str=None,power_state:str=None,device_driver:dict=None,function:str=None,description:str=None):
        data={
            'title':title,
            'level':level,
            'power_state':power_state,
            'device_driver':device_driver,
            'function':function,
            'description':description
        }
        r = requests.put(self.task_issue_url+f'{issue_id}/',auth=self.auth,data=data)
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

help='''
help                                                                print help
add                 /script </group_uuid> </group_name> </ssid>     add task by group_uuid or group_name 
edit                /id </group_uuid> </group_name> </ssid>         add task by group_uuid or group_name 
run                 /id                                             edit task status run
run_error           /id                                             edit task status run_error
finish              /id                                             edit task status finish
pause               /id                                             edit task status pause
skip                /id                                             edit task status skip
script_not_found    /id                                             edit task status script not found
tasks                                                               list tasks
current                                                             get current task
'''

def test():
    testeditissue()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers(title='TASK',dest = 'cmd')
    add_parsers = sub_parsers.add_parser('create',help='create a task')
    add_parsers.add_argument('script',type=str,help='script name')
    add_parsers.add_argument('-ssid',type=str,help='wifi ssid')
    addtask_exclu_gro = add_parsers.add_mutually_exclusive_group()
    addtask_exclu_gro.add_argument('-group_uuid',type=str)
    addtask_exclu_gro.add_argument('-group_name',type=str)

    edit_parsers = sub_parsers.add_parser('update',help='update a task')
    edit_parsers.add_argument('id',type=int,help='task id')
    edit_parsers.add_argument('-script',type=str,help='script name')
    edit_parsers.add_argument('-status',type=str,help='script status',choices=['run','wait','finish','pause','skip','script not found','run error'])
    edit_parsers.add_argument('-ssid',type=str,help='wifi ssid')
    edit_parsers.add_argument('-uutinfo',type=str,help='unit info format as json')
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

    edit_parsers = sub_parsers.add_parser('run_error',help='report a task run error when start or running')
    edit_parsers.add_argument('id',help='task id')

    edit_parsers = sub_parsers.add_parser('finish',help='report a task finish')
    edit_parsers.add_argument('id',help='task id')

    edit_parsers = sub_parsers.add_parser('pause',help='report a task pause')
    edit_parsers.add_argument('id',help='task id')

    edit_parsers = sub_parsers.add_parser('skip',help='report a task be skipped')
    edit_parsers.add_argument('id',help='task id')

    edit_parsers = sub_parsers.add_parser('script_not_found',help='report a script not found in local')
    edit_parsers.add_argument('id',help='task id')

    issuecreate_parsers = sub_parsers.add_parser('issuecreate',help='create a issue')
    issuecreate_parsers.add_argument('id',help='task id')
    issuecreate_parsers.add_argument('-title',help='issue title')
    issuecreate_parsers.add_argument('-level',help='issue level')
    issuecreate_parsers.add_argument('-power_state',help='what power state occur issue')
    issuecreate_parsers.add_argument('-device_driver',help='what device and driver occur issue')
    issuecreate_parsers.add_argument('-function',help='what function issues occur, format as json')
    issuecreate_parsers.add_argument('-description',help='issue description')

    issueupdate_parsers = sub_parsers.add_parser('issueupdate',help='update issue info')
    issueupdate_parsers.add_argument('id',help='issue id')
    issueupdate_parsers.add_argument('-title',help='issue title')
    issueupdate_parsers.add_argument('-level',help='issue level')
    issueupdate_parsers.add_argument('-power_state',help='what power state occur issue')
    issueupdate_parsers.add_argument('-device_driver',help='what device and driver occur issue')
    issueupdate_parsers.add_argument('-function',help='what function issues occur, format as json')
    issueupdate_parsers.add_argument('-description',help='issue description')

    sub_parsers.add_parser('list',help='list tasks')
    sub_parsers.add_parser('current',help='list current task')

    args = parser.parse_args()

    task = TaskServer('admin','admin')
    if args.cmd == 'create':
        task.add(args.script,args.group_uuid,args.group_name,args.ssid)
    elif args.cmd =='update':
        task.edit(args.id,args.script,args.status,args.ssid,args.group_uuid,args.group_name,args.uutinfo,args.power_cycle_info,args.start,args.finish)
    elif args.cmd == 'delete':
        task.delete(args.id)
    elif args.cmd == 'run':
        task.run(args.id)
    elif args.cmd == 'run_error':
        task.run_error(args.id)
    elif args.cmd == 'finish':
        task.finish(args.id)
    elif args.cmd == 'pause':
        task.pause(args.id)
    elif args.cmd == 'skip':
        task.skip(args.id)
    elif args.cmd == 'script_not_found':
        task.script_not_found(args.id)
    elif args.cmd == 'list':
        task.tasks
    elif args.cmd == 'current':
        task.current
    elif args.cmd == 'list':
        task.tasks
    