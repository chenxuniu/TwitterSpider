
class AccountStatus:
    def __init__(self,e,p,u,b = False):
        self.email = e
        self.password = p
        self.username= u
        self.is_block = b

class AccountManager:
    def __init__(self,filename="account.csv"):
        self.account_info = self.loadAccount(filename)

    def loadAccount(self,filename):
        account_info_list = []
        with open("account.csv") as f:
            for line in f.readlines():
                if line.startswith("#"): continue
                line = line.strip().split(",")
                account_info_list.append(AccountStatus(line[0], line[3], line[4]))
        return account_info_list

    def markAccountAsBlock(self,email):
        for item in self.account_info:
            if item.email == email:
                item.is_block = True

    def getAccount(self):
        result = [None,None,None]
        for item in self.account_info:
            if item.is_block == True:
                continue
            result = [item.email,item.password,item.username]
        return result