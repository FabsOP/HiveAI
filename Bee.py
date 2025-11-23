######## IMPORTS ########
import uuid
import random

class Bee:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.model = None
        self.injections = []
        self.beeId = str(uuid.uuid1())

        print("[Debug] Bee " + self.name + " created with id " + self.beeId + " and role " + self.role)
    
    def to_dict(self):
        return {
            "name": self.name,
            "role": self.role,
            "model": self.model,
            "injections": self.injections,
            "beeId": self.beeId
        }

    @staticmethod
    def from_dict(d):
        bee = Bee(d.get("name"), d.get("role"))
        bee.model = d.get("model")
        bee.injections = d.get("injections")
        bee.beeId = d.get("beeId")
        return bee

    def attach_model(self, model):
        self.model = model

    def detach_model(self):
        self.model = None

    def addInjection(self, behaviour, interval):
        injectionId = str(uuid.uuid4())
        self.injections.append({"id": injectionId, "behaviour": behaviour, "interval": interval})
        print("[Debug] Injection added to " + self.name + " with id " + injectionId)

    def remove_injection(self, injectionId):
        self.injections.remove(injectionId)
    
    def update_injection_behaviour(self, injectionId, behaviour):
        for injection in self.injections:
            if injection['id'] == injectionId:
                injection['behaviour'] = behaviour
    
    def update_injection_interval(self, injectionId, interval):
        for injection in self.injections:
            if injection['id'] == injectionId:
                injection['interval'] = interval

    def log_injections(self):
        print("[Debug] Injections for " + self.name + ":")
        for injection in self.injections:
            print(injection)

    def query(self, prompt, context, log):
        assert self.model is not None, "Could not query " + self.name + ": Model not attached to bee"

        #### a) Roll injections
        successfull_injections = []
        for injection in self.injections:
            target = injection['interval']
            roll = random.randint(1, target)
            if roll == target:
                successfull_injections.append(injection)
                print("[Debug] 🎲 Injection " + injection['id'] +  " with behaviour " + injection['behaviour'] + " successful for " + self.name)

        injection = None

        #### b) Pick a single successful injection
        if successfull_injections:
            if len(successfull_injections) == 1:
                injection = successfull_injections[0]
                print("[Debug] Only one injection successful for " + self.name + ": " + injection['behaviour'])
            else:
                #pick injection with highest interval. If all succesfull injections have the same interval, pick one at random
                maxInterval = max(injection['interval'] for injection in successfull_injections)
                injection = random.choice([injection for injection in successfull_injections if injection['interval'] == maxInterval])
                print("[Debug] There were " + str(len(successfull_injections)) + " injections successful for " + self.name + ", picked " + injection['behaviour'] + " with interval " + str(injection['interval']) + " out of the following injections: " + str(successfull_injections))


        #### c) Generate response
        print("[Debug] Bee " + self.name + " is thinking...")
        promptTemplate = ""

        #code to invoke model

        return  f"<Bee {self.name} Reply>"

        
        

    def inferModel(self, prompt, max_output_tokens=1024, verbose=True):
        assert self.model is not None, "Could not query " + self.name + ": Model not attached to bee"
        # Request payload
        payload = {
            "max_tokens": max_output_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        try:
            #Send POST request
            response = requests.post(f"{self.model}/v1/chat/completions", json=payload)
            response.raise_for_status() # Raise an exception for bad status codes

            #Parse and print output
            data = response.json()
            content = data["choices"][0]["messages"]["content"]
            reasoning = content.split("<think>")[1].split("</think>")[0].strip() #everything between <think></think>
            reply = content.split("</think>")[1].strip() #everything after </think>

            if verbose:
                print(f"Response Json: {data}\n")
                print(f"User: {prompt}\n")
                print(f"Reasoning:\n{reasoning}\n")
                print(f"Reply:\n{reply}\n")

            return {"reasoning": reasoning, "reply": reply}

        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return None


    def get_name(self):
        return self.name
    
    def get_role(self):
        return self.role

    def get_injections(self):
        return self.injections
    
    def get_model(self):
        return self.model

    def get_beeId(self):
        return self.beeId

    def set_name(self, name):
        self.name = name
        print("[Debug] Bee " + self.name + " renamed to " + name)
    
    def set_role(self, role):
        self.role = role
        print("[Debug] Bee " + self.name + " role changed to " + role)
    