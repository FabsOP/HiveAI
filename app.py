############## IMPORTS ##############################
import requests
import Hive
import Bee

if __name__ == "__main__":
    tunnel_url = "https://distant-guardian-starts-salaries.trycloudflare.com"   # Replace with your SSH-tunneled local port
    prompt = "Hi, I'm Fabio"

    n = 5 #rounds    
    hive = Hive.Hive()
    Q = Queen("Q", "queen")
    b1 = Bee.Bee("Creative", "worker")
    b2 = Bee.Bee("b2", "worker")
    b3 = Bee.Bee("b3", "worker")
    hive.add_bee(b1)
    hive.add_bee(b2)
    hive.add_bee(b3)

    hive.query(prompt, n)
    
    