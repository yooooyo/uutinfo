import server_models
import client_models
import json
from uutinfo import Catuutinfo


class Transfer(Catuutinfo):

    @property
    def server_connection(self):
        return server_models.database.connect()

    @property
    def client_connection(self):
        return client_models.database.connect()

    def _update_uutinfo_server(self,data):
        if self.server_connection:    
            pass
        else:
            pass

    def _update_uutinfo_client(self,data):
        pass

    def update_uutinfo(self):
        data  = self.dump()
        
        
    



if __name__ == "__main__":
    pass