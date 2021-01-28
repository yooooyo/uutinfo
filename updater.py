from os.path import realpath
import pathlib
from traceback import print_tb
from win32com.client import Dispatch
from pathlib import Path
import re
from typing import List
from uutinfo import Catuutinfo
from O365 import FileSystemTokenBackend,Account
import os
import json
from distutils.version import LooseVersion
import zipfile
import concurrent.futures
from concurrent.futures import as_completed
import subprocess
import sys
import os

class CommSite:
    def __init__(self) -> None:
        self.account = self.get_account

    @property
    def get_credential(self):
        try:
            source = os.path.join(self._resource_path,'credentials.json')
            with open(source,'r') as f:
                data = json.load(f)
                credentials = (data['appid'],data['secret'])
                return credentials
        except:
            return None

    @property
    def _resource_path(self):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return base_path

    @property
    def get_account(self):
        token_backend = FileSystemTokenBackend(token_path=self._resource_path,token_filename='o365_token.txt')
        credential = self.get_credential
        if token_backend.check_token():
            print('Authenticated')
            return Account(credentials=credential,token_backend = token_backend)
        else:
            if credential:
                account = Account(credential)
                if account.authenticate(scopes=['basic','users','address_book','message_all','onedrive_all','sharepoint']):
                    print('Authenticated')
                    return account
            else:
                print('Authenticate Fail !')
                return None

    @property
    def sharepoint(self):
        return self.account.sharepoint() if self.account else None

    @property
    def commsite(self):
        ret = self.sharepoint.search_site('comm tech')
        if len(ret)>0:return ret[0]
        else:None

    @property
    def get_validation_lib(self):
        if self.account:
            validation_lib = [lib for lib in self.commsite.list_document_libraries() if lib.name == 'Validation and Quality Program'][0]            
            return validation_lib
        return None

    @property
    def get_tool_root(self):
        if self.account:      
            return self.get_validation_lib.get_item_by_path('/LAB Regular Test Tool')
        return None
        

    def get_folder_under_validation_lib(self,path):
        return self.get_validation_lib.get_item_by_path(path)

    @property
    def get_winpvt_list(self):
        items = self.get_folder_under_validation_lib('/LAB Regular Test Tool/WinPVT').get_items()
        return [item for item in items]

    @property
    def get_winpvtarm_list(self):
        items = self.get_folder_under_validation_lib('/LAB Regular Test Tool/WinPVTarm').get_items()
        return [item for item in items]

    @property
    def get_pws_list(self):
        items = self.get_folder_under_validation_lib('/LAB Regular Test Tool/PowerStress').get_items()
        return [item for item in items]

    winpvt_regex = '(?P<name>WinPVT)\s?(?P<full_ver>(?P<ver>(?:\d+\.?)+)(?P<alph>[A-Z]?))\s?(\((x64|x86)\))?(.exe)??'
    pws_regex = '(?P<name>PowerStressTest)-(?P<full_var>(?P<ver>(?:\d+\.?)+\d+))(.zip)?'

    def _version_compartor(self,v1,v2):
        num1,alph1 = v1
        num2,alph2 = v2
        if num1 > num2:
            return v1
        elif num1 == num2:
            if alph1 > alph2:
                return v1
        return v2

    def _get_latest(self,files):
        if len(files) == 0: return None
        if len(files) == 1: return files[0]
        regex_str = None
        # temp_ver = None
        # temp_alph = None
        v2 = None
        latest = None
        for cnt,file in enumerate(files):
            if not regex_str:
                if file.name.lower().find('winpvt')>=0:
                    regex_str = self.winpvt_regex
                elif file.name.lower().find('power')>=0:
                    regex_str = self.pws_regex
            if regex_str:
                match = re.match(regex_str,file.name).groupdict()
                v1 = LooseVersion(match.get('ver')),match.get('alph',None)
                if cnt == 0:
                    v2 = v1
                    continue
                if self._version_compartor(v1,v2) == v1:
                    v2 = v1
                    latest = file
            else:
                return None
        return latest

    @property
    def get_latest_winpvt(self):
        return self._get_latest(self.get_winpvt_list)

    @property
    def get_latest_pws(self):
        return self._get_latest(self.get_pws_list)

    @property
    def get_latest_winpvtarm(self):
        return self._get_latest(self.get_winpvtarm_list)


class Updater(CommSite,Catuutinfo):

    def __init__(self):
        super().__init__()

    @property
    def is_arm(self):
        self._get_info()
        if self.info['os'][0].OSArchitecture.lower().find('arm') >= 0:
            return True
        return False

    @property
    def get_local_winpvt_list(self):
        pvt_path = None
        if self.is_arm:
            pvt_path = r'C:\Program Files (x86)\Hewlett-Packard'
        else:
            pvt_path = r'C:\Program Files\Hewlett-Packard'
        p = Path(pvt_path)
        f = p.rglob('WinPVT.exe')
        return [_f.parent for _f in f]

    @property
    def get_current_winpvt(self):
        current = self._get_latest(self.get_local_winpvt_list)
        if current: return current.name
        else: return None

    def get_file_version(self,path):
        parser = Dispatch("Scripting.FileSystemObject")
        return parser.GetFileVersion(path)

    @property
    def get_local_pws_list(self):
        p = Path('C:\\')
        find_list=['release','powerstresstest*']
        result_list=[]
        pws_list=[]
        for f in find_list:
            result_list.extend(list(p.glob(f)))
        
        if not result_list: return None
        else:
            for r in result_list:
                if r.is_dir:
                    pws_list.extend(list(r.rglob('PowerStressTest.exe')))
        return pws_list

    @property
    def get_current_pws_file(self):
        pws_list = self.get_local_pws_list
        if not pws_list: return None
        versions = [self.get_file_version(f.as_posix()) for f in pws_list]
        return [f for f in pws_list if self.get_file_version(f.absolute()) == max(versions)][0]

    @property
    def get_current_pws(self):
        pws = self.get_current_pws_file
        if not pws: return None
        version = self.get_file_version(pws.as_posix())
        return 'PowerStressTest-'+version


    @property
    def get_latest_winpvt(self):
        if self.is_arm:
            return super().get_latest_winpvtarm
        else:
            return super().get_latest_winpvt

    def ver_convert(self,regex_str,source):
        return re.match(regex_str,source).groupdict()

    @property
    def is_winpvt_installed(self):
        return True if self.get_current_winpvt else False

    @property
    def winpvt_can_update(self)->bool:
        if not self.is_winpvt_installed: return True

        regex_str = self.winpvt_regex
        s_pvt =self.ver_convert(regex_str,self.get_latest_winpvt.name)
        c_pvt = self.ver_convert(regex_str,self.get_current_winpvt)
        v1 = LooseVersion(s_pvt.get('ver')),s_pvt.get('alph',None)
        v2 = LooseVersion(c_pvt.get('ver')),c_pvt.get('alph',None)

        if v1 == v2:
            return False
        else:
            return self._version_compartor(v1,v2) == v1

    @property
    def is_pws_installed(self):
        return True if self.get_current_pws else False

    @property
    def pws_can_update(self) -> bool:
        if not self.is_pws_installed: return True

        regex_str = self.pws_regex
        s_pws =self.ver_convert(regex_str,self.get_latest_pws.name)
        c_pws = self.ver_convert(regex_str,self.get_current_pws)
        v1 = LooseVersion(s_pws.get('ver')),None
        v2 = LooseVersion(c_pws.get('ver')),None

        if v1 == v2:
            return False
        else:
            return self._version_compartor(v1,v2) == v1

    def pws_uninstall(self,version=None,file=None,dest='C:\\'):
        local_pws_list = self.get_local_pws_list
        try:
            uninstall_file = None
            if not local_pws_list: 
                print('No PowerStressTest Tool install') 
                return True
            else:

                if version:
                    for f in local_pws_list:
                        file_version = self.get_file_version(f.as_posix())
                        if file_version == version:
                            uninstall_file = f
                            break
                    else:
                        print('Not find target version')
                        print(f'But currently we have under {dest} :')
                        print("\n".join([self.get_file_version(p.as_posix()) for p in local_pws_list]))
                        return False
                elif file:
                    uninstall_file = file
                else:
                    uninstall_file = self.get_current_pws_file
                delete_folder = None
                if uninstall_file.parent.parent.name.lower().find('powerstress')>=0:
                    delete_folder = uninstall_file.parent.parent
                else: delete_folder = uninstall_file.parent
                from shutil import rmtree
                rmtree(delete_folder.as_posix())
                return not delete_folder.exists()
        except Exception as e:
            print(e)
            return False


    def pws_install(self,version,dest='C:\\'):
        f =  [f for f in self.get_pws_list if self.ver_convert(self.pws_regex,f.name)['ver'] == version]
        print(f)
        if f and len(f) == 1: f = f[0]
        else:
            print(f'not found PowerStress - {version}')
            print('But we have :')
            print('But we have :')
            return False
        f = self.download(dest,f)
        self.find_file_and_dezip(dest,f.name)
        if self.ver_convert(self.pws_regex,self.get_current_pws)['ver'] == version:return True
        return False

    def pws_reinstall(self):
        dest = 'C:\\'
        curr = self.get_current_pws
        if not curr:
            print('Not install PowerStressTest tool under C:\\') 
            return False
        try:
            find_curr = [f for f in self.get_pws_list if f.name.find(curr)>=0]
            if find_curr:
                find_curr = find_curr[0]
                f = self.download(dest,find_curr)
                self.find_file_and_dezip(dest,f.name)
        except Exception as e:
            print(e)
            return False
        return True
        
    def pws_update(self):
        if self.pws_can_update:
            self.pws_uninstall(self.ver_convert(self.pws_regex,self.get_current_pws)['ver'])
            self.pws_install(self.ver_convert(self.pws_regex,self.get_latest_pws)['ver'])

    def winpvt_install(self,file):
        pass

    animation = [
     "downloading [                    ]",
     "downloading [=                   ]",
     "downloading [==                  ]",
     "downloading [===                 ]",
     "downloading [====                ]",
     "downloading [=====               ]",
     "downloading [======              ]",
     "downloading [=======             ]",
     "downloading [========            ]",
     "downloading [=========           ]",
     "downloading [==========          ]",
     "downloading [===========         ]",
     "downloading [============        ]",
     "downloading [=============       ]",
     "downloading [==============      ]",
     "downloading [===============     ]",
     "downloading [================    ]",
     "downloading [=================   ]",
     "downloading [==================  ]",
     "downloading [=================== ]",
     "downloading [====================]",
     "downloading [ ===================]",
     "downloading [  ==================]",
     "downloading [   =================]",
     "downloading [    ================]",
     "downloading [     ===============]",
     "downloading [      ==============]",
     "downloading [       =============]",
     "downloading [        ============]",
     "downloading [         ===========]",
     "downloading [          ==========]",
     "downloading [           =========]",
     "downloading [            ========]",
     "downloading [             =======]",
     "downloading [              ======]",
     "downloading [               =====]",
     "downloading [                ====]",
     "downloading [                 ===]",
     "downloading [                  ==]",
     "downloading [                   =]",
    ]

    animation_cnt=0
    animation_complete = None
    def wait_animation(self):
        import time
        while not self.animation_complete:
            print(self.animation[self.animation_cnt % len(self.animation)], end='\r')
            time.sleep(.1)
            self.animation_cnt += 1
        print('done !                                                ',end='\r')

    def download(self,dest_path,file,overwrite = True):
        try:
            file_name = file.name
            file_path = os.path.join(dest_path,file_name)
            print(f'download at {file_path}')

            mode = 'r'
            if overwrite and os.path.exists(file_path) or not os.path.exists(file_path):
                mode = 'wb'
            
            with open(file_path,mode) as f:
                if mode == 'r':
                    print(f'Already exist {file_name}')
                    return f
                else:
                    file.download(output=f)
                    print('Download finish')
                    return f
        except Exception as e:
            print(e)
            print('Download Fail')
            raise e

    def find_file_and_dezip(self,path,file):
        
        with zipfile.ZipFile(os.path.join(path,file),'r') as zipper:
            zipper.extractall(path)
        


    def check(self):
        download_files = []
        dest_path = 'C:\\'
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            if self.pws_can_update:
                current_pws = self.get_current_pws_file
                if current_pws: self.pws_uninstall(file=self.get_current_pws_file)
                download_files.append(self.get_latest_pws)
            if self.winpvt_can_update:
                download_files.append(self.get_latest_winpvt)

            download_processes = None if not download_files else [executor.submit(self.download,dest_path,file) for file in download_files] 
            if download_processes:
                self.animation_complete = False
                download_animate = executor.submit(self.wait_animation)
                
                for process in download_processes:
                    exception = process.exception() 
                    if exception:
                        self.animation_complete = True
                        print(exception)
                    if as_completed(process):
                        result = process.result()
                        if result.name.lower().find('powerstress')>=0:
                            executor.submit(self.find_file_and_dezip,dest_path,result.name)    
                        if result.name.lower().find('winpvt')>=0:
                            print('install winpvt')
                            try:
                                sb = subprocess.run([os.path.realpath(result.name),'/S','/v/qn'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,timeout=60)
                            except Exception as e:
                                print(e)
                            # executor.submit(subprocess.run())
                    
                self.animation_complete = True
                download_animate.cancel()
            else:
                print('Nothing to update')

help_msg= \
'''
double click for auto-update
-------------------------------------
commands :

-h                         print help
-pws    re                 reinstall pws
        in <version>       install specific version
        up                 update    pws
        un                 uninstall pws
        un <version>       uninstall specific version
        list               list pws versions can be install
-pvt    re                 reinstall winpvt
        in <version>       install specific version
        up                 update    winpvt
        un                 uninstall winpvt
        list               list pvt versions
'''

def run():
    cmd = sys.argv
    cmd.pop(0)
    if not cmd:    
        updater = Updater()
        print(
f'''
                Local                          Server
Winpvt          {updater.get_current_winpvt}   {updater.get_latest_winpvt}
PowerStress     {updater.get_current_pws}      {updater.get_latest_pws}
'''
        )
        updater.check()
        print('for more info please use -h')
        input('Press Enter to finish')
    else:
        updater = Updater()
        cmd_l1 = cmd[0]
        if len(cmd)>1:
            global cmd_l2
            cmd_l2 = cmd[1]
        if cmd_l1 == '-h':
            print(help_msg)
        elif cmd_l1 == '-pws':
            if cmd_l2 == 're':
                updater.pws_reinstall()
            elif cmd_l2 == 'in':
                version = cmd[2]
                updater.pws_install(version)
            elif cmd_l2 == 'up':
                updater.pws_update()
            elif cmd_l2 == 'un':
                if len(cmd) ==3: 
                    updater.pws_uninstall(cmd[2])
                else:
                    updater.pws_uninstall()
            elif cmd_l2 == 'list':
                print('PowerStressTest versions on server :')
                print('\n'.join([updater.ver_convert(updater.pws_regex,f.name)['ver'] for f in updater.get_pws_list]))
        # elif cmd_l1 == '--pvt':
        #     if cmd_l2 == 're':
        #         updater.pvt_reinstall()
        #     elif cmd_l2 == 'in':
        #         version = cmd[2]
        #         updater.pvt_install(version)
        #     elif cmd_l2 == 'up':
        #         updater.pvt_update()
        #     elif cmd_l2 == 'un':
        #         if len(cmd) ==3: 
        #             updater.pvt_uninstall(cmd[2])
        #         else:
        #             updater.pvt_uninstall()
        #     elif cmd_l2 == 'list':
        #         print('WinPVT versions on server :')
        #         print('\n'.join([updater.ver_convert(updater.pws_regex,f.name)['ver'] for f in updater.get_pws_list]))
        else:
            print(help_msg)


def test():
    u = Updater()
    print(u.pws_uninstall())

if __name__ == "__main__":
    run()
    # test()

    