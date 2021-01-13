from os.path import realpath
import pathlib
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
    pws_regex = '(?P<name>PowerStressTest)-(?P<full_var>(?P<ver>(?:\d+\.?)+))'

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
    def get_current_pws(self):
        pws_list = self.get_local_pws_list
        if not pws_list: return None
        else:
            versions = [self.get_file_version(f.absolute()) for f in self.get_local_pws_list]
        return 'PowerStressTest-'+max(versions)


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

    def download(self,dest_path,file):
        file_name = file.name
        file_path = os.path.join(dest_path,file_name)
        print(f'download at {file_path}')
        if not os.path.exists(file_path):
            with open(file_path,'wb') as f:
                file.download(output=f)
                return f
        else:
            with open(file_path,'r') as f:
                return f

    def find_file_and_dezip(self,path,file):
        
        with zipfile.ZipFile(os.path.join(path,file),'r') as zipper:
            zipper.extractall(path)
        


    def check(self):
        download_files = []
        dest_path = 'C:\\'
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            if self.pws_can_update:
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


if __name__ == "__main__":
    cmd = sys.argv
    cmd.pop()
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
        input('Press Enter to finish')
    else:
        pass
    