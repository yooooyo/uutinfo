import server_models
import client_models
from uutinfo import Catuutinfo

class Transfer(Catuutinfo):

    def update_uutinfo(self):
        info = self.get_all_info()

    def update_info(self):
        info = self._get_info()

    def update_drivers(self):
        info = self._get_drivers()



if __name__ == "__main__":
    pass