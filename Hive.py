######## IMPORTS ########
import random
import uuid
import datetime
import os
import Queen
import Bee
import json

class Hive:
    """A hive represents a chat session. Each hive has a queen bee and 0 or more worker bees"""
    def __init__(self, hiveName):
        self.hiveID = str(uuid.uuid1())
        self.hiveName = hiveName
        
        self.models = []

        self.bees = []
        self.queen = Queen.Queen()
        self.history = []
        
        self.sequential = True
        self.randomize = False

        self.lastModified = datetime.datetime.now().isoformat()

    @staticmethod
    def deleteHive(id):
        #code here to delete a hive try except
        try:
            os.remove("hives/" + "hive_" + id + ".json")
            print("[Debug] Hive " + id + " deleted")
        except FileNotFoundError:
            print("[Debug] Hive " + id + " not found")

    def to_dict(self):
        return {
            "hiveID": self.hiveID,
            "hiveName": self.hiveName,
            "models": self.models,
            "bees": [bee.to_dict() for bee in self.bees],
            "queen": self.queen.to_dict(),
            "history": self.history,
            "sequential": self.sequential,
            "randomize": self.randomize,
            "lastModified": self.lastModified
        }

    @staticmethod
    def from_dict(d):
        hive = Hive(d["hiveName"])
        hive.hiveID = d["hiveID"]
        hive.models = d["models"]
        hive.bees = [Bee.Bee.from_dict(bee) for bee in d["bees"]]
        hive.queen = Queen.Queen.from_dict(d["queen"])
        hive.history = d["history"]
        hive.sequential = d["sequential"]
        hive.randomize = d["randomize"]
        hive.lastModified = d["lastModified"]
        
        #attach models to bees
        for bee in hive.bees:
            for model in hive.models:
                if model == bee.model:
                    bee.attach_model(model)
        return hive

    
    def load(self, id):
        #load hive from file
        with open("hives/" + "hive_" + id + ".json", "r") as f:
            data = json.load(f)

        self.hiveID = data["hiveID"]
        self.hiveName = data["hiveName"]
        self.models = data["models"]
        self.bees = [Bee.Bee.from_dict(bee) for bee in data["bees"]]
        self.queen = Queen.Queen.from_dict(data["queen"])
        self.history = data["history"]
        self.sequential = data["sequential"]
        self.randomize = data["randomize"]
        self.lastModified = data["lastModified"]
        
        #attach models to bees
        for bee in self.bees:
            for model in self.models:
                if model == bee.model:
                    bee.attach_model(model)


    def add_bee(self, bee):
        self.bees.append(bee)
        self.updateLastModified()
        print("[Debug] Bee " + bee.name + " added to hive " + self.hiveName)
        self.save()


    def remove_bee(self, bee):
        #if bee is not queen
        self.updateLastModified()
        self.bees.remove(bee)

        self.save()

    def add_model(self, model):
        self.updateLastModified()
        self.models.append(model)
        self.save()
    
    def remove_model(self, model):
        #warning, all bees with this model will have it detached
        self.updateLastModified()
        self.models.remove(model)

        #detach from each bee
        for bee in self.bees:
            if bee.model == model:
                bee.detach_model()

        self.save()
    
    def set_sequential(self, sequential):
        self.updateLastModified()
        self.sequential = sequential
        self.save()
    
    def set_randomize(self, randomize):
        self.updateLastModified()
        self.randomize = randomize
        self.save()

    def getQueen(self):
        return self.queen

    def attach_model_to_queen(self, model):
        self.queen.attach_model(model)
    
    def detach_model_from_queen(self, model):
        self.queen.detach_model(model)

    def getModels(self):
        return self.models

    def getBees(self):
        return self.bees

    def getHistory(self):
        return self.history

    def query(self, prompt, n, callback=None):
        assert self.queen.get_model() is not None, "Could not query " + self.hiveName + ": Queen model not attached"
        assert len(self.bees) > 0, "Could not query " + self.hiveName + ": No bees in hive"

        print("############################# HIVE CONFIGURATION ########################################")
        print(f"[Debug] Querying {self.hiveName} with prompt: " + prompt)
        print("[Debug] Number of bees: " + str(len(self.bees)))
        print("[Debug] Number of rounds: " + str(n))
        print("############################ FETCH CONTEXT #########################################")
        logs = []
        bees = self.bees.copy()

        context = self.queen.extractContext(prompt, self.history)
        print(f"[Debug] {context}")
        print("############################## START OF DISCUSSION #######################################")

        for i in range(n):
            print("\n### Round " + str(i+1) + " ###")
            if self.randomize:
                random.shuffle(bees)
            for bee in bees:
                response = bee.query(prompt, context, logs, callback)
                print(f"[Debug] {response}\n")
                entry = {"round": i, "beeId": bee.beeId, "name": bee.name, "role": bee.role, "response": response }
                logs.append(entry)
        print("\n############################# END OF DISCUSSION ########################################")
        aggregated_response = self.queen.aggregate_response(prompt, logs, callback)
        print("[Debug] Queen 👑: " + aggregated_response)
        self.updateHistory(prompt, len(bees), n, logs, aggregated_response, )
        self.updateLastModified()
        self.save()
        return aggregated_response

    def updateLastModified(self):
        self.lastModified = datetime.datetime.now().isoformat()
    
    def updateHistory(self, prompt, nBees, nRounds, logs, response):
        self.history.append({"prompt": prompt, "nBees": nBees, "nRounds": nRounds , "logs": logs, "response": response})
        print("[Debug] " + self.hiveName + " history updated")
    
    def save(self):
        #if hives directory does not exist create it
        if not os.path.exists("hives"):
            os.makedirs("hives")
        
        #save hive to file
        with open("hives/" + "hive_" + self.hiveID + ".json", "w") as f:
            json.dump(
                self.to_dict(),
                f,
                indent=4,
                separators=(',', ': ')
            )
        print("[Debug] " + self.hiveName + " saved")

    def log_properties(self):
        print(json.dumps(self.to_dict(), indent=4))

    def clear_history(self):
        self.history = []
        self.save()