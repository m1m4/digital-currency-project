from requests import get
import time
import threading


class IPDetector(threading.Thread):
    
    def __init__(self, cooldown):
        
        threading.Thread.__init__(self)
        self.event = threading.Event()
        self.cooldown = cooldown
    
    def run(self):
        ip = get('https://api.ipify.org').text
        last_ip = ip


        while not self.event.is_set():
            ip = get('https://api.ipify.org').text
            
        #sets your current ip to currentIP variable

            print(ip)
            if ip != last_ip:
                print(f'IP changed: {ip}')
                last_ip = ip
                
            time.sleep(self.cooldown)
