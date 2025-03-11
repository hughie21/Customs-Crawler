import yaml
import sys

class Config:
    def __init__(self):
        self.api_key = ""
        self.importyeti_cookie_searching = ""
        self.importyeti_cookie_details = ""
        self.bing_cookie = ""
        self.load()
    
    def load(self):
        try:
            coniguration = yaml.load(open('./config.yaml', 'r'), Loader=yaml.FullLoader)
        except:
            sys.exit("config.yaml not found")
        self.api_key = coniguration["api_key"] if coniguration["api_key"] else ""
        self.importyeti_cookie_searching = coniguration["importyeti_cookie_searching"] if coniguration["importyeti_cookie_searching"] else ""
        self.importyeti_cookie_details = coniguration["importyeti_cookie_details"] if coniguration["importyeti_cookie_details"] else ""
        self.bing_cookie = coniguration["bing_cookie"] if coniguration["bing_cookie"] else ""
    
    def save(self):
        coniguration = {
            "api_key": self.api_key,
            "importyeti_cookie_searching": self.importyeti_cookie_searching,
            "importyeti_cookie_details": self.importyeti_cookie_details,
            "bing_cookie": self.bing_cookie
        }
        print(coniguration)
        with open('./config.yaml', 'w') as f:
            yaml.dump(coniguration, f)

config = Config()

if __name__ == "__main__":
    config.importyeti_cookie_details = "test"
    config.save()