######## IMPORTS ########
import random
import uuid
import datetime
import os
import Queen
import json

class Hive:
    """A hive represents a chat session. Each hive has a queen bee and 0 or more worker bees"""
    def __init__(self, hiveName):
        self.hiveID = str(uuid.uuid1())
        self.hiveName = hiveName
        print("[Debug] Hive " + self.hiveName + " created with id " + self.hiveID +"\n")

        
        self.models = []

        self.bees = []
        self.queen = Queen.Queen()
        self.history = []
        
        self.sequential = True
        self.randomize = False

        self.lastModified = datetime.datetime.now().isoformat()

        
        self.save() 

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

    def getModels(self):
        return self.models

    def getBees(self):
        return self.bees

    def query(self, prompt, n):
        assert self.queen.get_model() is not None, "Could not query " + self.hiveName + ": Queen model not attached"
        assert len(self.bees) > 0, "Could not query " + self.hiveName + ": No bees in hive"

        print("[Debug] Hive " + self.hiveName + " is querying with prompt: " + prompt)
        print("[Debug] Number of bees: " + str(len(self.bees)))
        print("[Debug] Number of rounds: " + str(n))
        logs = []
        bees = self.bees.copy()

        context = self.queen.extractContext(prompt, self.history)

        for i in range(n):
            print("\nRound " + str(i+1))
            if self.randomize:
                random.shuffle(bees)
            for bee in bees:
                response = bee.query(prompt, context, logs)
                entry = {"round": i, "beeId": bee.beeId, "name": bee.name, "role": bee.role, "response": response }
                logs.append(entry)
        
        aggregated_response = self.queen.aggregate_response(prompt, logs)
        self.updateHistory(prompt, logs, aggregated_response)
        self.updateLastModified()
        self.save()
        return aggregated_response

    def updateLastModified(self):
        self.lastModified = datetime.datetime.now().isoformat()
    
    def updateHistory(self, prompt, logs, response):
        self.history.append({"prompt": prompt, "logs": logs, "response": response})
        print("[Debug] Hive " + self.hiveName + " history updated")
    
    def save(self):
        #if hives directory does not exist create it
        if not os.path.exists("hives"):
            os.makedirs("hives")
        
        #save hive to file
        with open("hives/" + "hive_" + self.hiveID + ".json", "w") as f:
            json.dump(self.to_dict(), f)
        print("[Debug] Hive " + self.hiveName + " saved")
            
        
