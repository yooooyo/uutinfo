from win32com.client import Dispatch
from pathlib import Path
import re
from typing import List
from uutinfo import Catuutinfo
from O365 import FileSystemTokenBackend,Account
import os
import json
from distutils.version import LooseVersion
import rarfile
import threading
import multiprocessing as mp
class CommSite:
    def __init__(self) -> None:
        self.account = self.get_account

    @property
    def get_credential(self):
        try:
            with open('credentials.json','r') as f:
                data = json.load(f)
                credentials = (data['appid'],data['secret'])
                return credentials
        except:
            return None

    @property
    def get_account(self):
        os.path.realpath('__file__')
        token_backend = FileSystemTokenBackend(token_path='.',token_filename='o365_token.txt')
        credential = self.get_credential
        if token_backend.check_token():
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
                # print(match)
                # ver,alph = LooseVersion(match.get('ver')),match.get('alph',None)
                # if cnt == 0:
                #     temp_ver,temp_alph = ver,alph
                #     continue
                # if ver > temp_ver:
                #     latest = file
                #     temp_ver,temp_alph = ver,alph
                # elif ver == temp_ver:
                #     if alph > temp_alph:
                #         latest = file
                #         temp_ver,temp_alph = ver,alph

                v1 = LooseVersion(match.get('ver')),match.get('alph',None)
                if cnt == 0:
                    v2 = v1
                    continue
                # print(v1,v2)
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
    def get_current_winpvt(self):
        pvt_path = None
        if self.is_arm:
            pvt_path = r'C:\Program Files (x86)\Hewlett-Packard'
        else:
            pvt_path = r'C:\Program Files\Hewlett-Packard'

        winpvt = Path(pvt_path)
        if winpvt.exists() and len([i for i in winpvt.glob('Winpvt.exe')])>0:
            return winpvt.name
        return None

    def get_file_version(self,path):
        parser = Dispatch("Scripting.FileSystemObject")
        return parser.GetFileVersion(path)

    @property
    def get_current_pws(self):
        pws_path = r'C:\Release\PowerStressTest.exe'
        if os.path.exists(pws_path):
            return self.get_file_version(pws_path)
        return None

    @property
    def get_latest_winpvt(self):
        if self.is_arm:
            return super().get_latest_winpvtarm
        else:
            return super().get_latest_winpvt

    ver_convert = lambda regex_str,source: re.match(regex_str,source).groupdict()

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
        c_pws = self.ver_convert(regex_str,self.get_current_winpvt)
        v1 = LooseVersion(s_pws.get('ver')),s_pws.get('alph',None)
        v2 = LooseVersion(c_pws.get('ver')),c_pws.get('alph',None)

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
    def wait_animation(self,arg):
        import time
        while not self.animation_complete:
            print(self.animation[self.animation_cnt % len(self.animation)], end='\r')
            time.sleep(.1)
            self.animation_cnt += 1
        print('done !                                             ',end='\r')

    def download(self,dest_path,file):
        file_name = file.name
        with open(os.path.join(dest_path,file_name),'wb') as f:
            file.download(output=f)
            return f

    def check(self):
        download_files_proc = []
        dest_path = 'C:'

        if self.pws_can_update:
            download_files_proc.append(threading.Thread(target = self.download,args=(dest_path,self.get_latest_pws)))
# 
        if self.winpvt_can_update:
            download_files_proc.append(threading.Thread(target = self.get_latest_winpvt.download,args=(dest_path,)))

        animation_task = threading.Thread(target=self.wait_animation,args=(None,))
        if len(download_files_proc)>0:
            self.animation_complete = False
            for  _,task in enumerate(download_files_proc):
                task.start()
        animation_task.start()
        for _,task in enumerate(download_files_proc):
            task.join()
        self.animation_complete = True
        animation_task.join()

        
    

if __name__ == "__main__":
    Updater().check()
    