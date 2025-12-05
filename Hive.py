######## IMPORTS ########
import random
import uuid
import datetime
import os
import Queen
import Bee
import json
import re

class Hive:
    """A hive represents a chat session. Each hive has a queen bee and 0 or more worker bees"""
    def __init__(self, hiveName):
        self.hiveID = str(uuid.uuid1())
        self.hiveName = hiveName

        self.contextWindow = 10
        
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
            "contextWindow": self.contextWindow,
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
        # Create instance without calling __init__ to avoid generating new ID and saving
        hive = object.__new__(Hive)
        hive.hiveID = d["hiveID"]
        hive.hiveName = d["hiveName"]
        hive.contextWindow = d.get("contextWindow", 7)  # Default to 3 for backward compatibility
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
        self.contextWindow = data.get("contextWindow", 7)  # Default to 7 for backward compatibility
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

        #load history into vector store


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
        #warning, all bees and queen with this model will have it detached
        self.updateLastModified()
        self.models.remove(model)

        #detach from each bee
        for bee in self.bees:
            if bee.model == model:
                bee.detach_model()
        
        #detach from queen if she has this model
        if self.queen.model == model:
            self.queen.detach_model()

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

        context = self.queen.extractContext(prompt, self.history, self.contextWindow)
        # Truncate context log to avoid very large prints impacting UI responsiveness
        if isinstance(context, str) and len(context) > 300:
            context_preview = context[:300] + "..."
        else:
            context_preview = context
        print(f"[Debug] RAG: {context_preview}")
        
        # Signal that context is ready - this triggers the UI to show "Thinking" animation
        if callback:
            callback({"name": "__context_ready__", "response": None})
        
        print("############################## START OF DISCUSSION #######################################")
        
        # Signal discussion start - transitions animation from retrieval to discussion phase
        if callback:
            callback({"name": "__discussion_start__", "response": None})

        for i in range(n):
            print("\n### Round " + str(i+1) + " ###")
            if self.randomize:
                random.shuffle(bees)
            for bee in bees:
                response = bee.query(prompt, context, logs, callback)
                # Avoid printing full responses to keep logging lightweight
                print(f"[Debug] {bee.name} responded.")
                entry = {"round": i, "beeId": bee.beeId, "name": bee.name, "role": bee.role, "response": response }
                logs.append(entry)
        print("\n############################# END OF DISCUSSION ########################################")
        aggregated_response = self.queen.aggregate_response(prompt, logs, callback)
        # Keep queen log lightweight as well
        print("[Debug] Queen 👑: response generated.")
        
        self.updateHistory(prompt, len(bees), n, logs, aggregated_response, )
        self.updateLastModified()
        self.save()
        return aggregated_response



    def updateLastModified(self):
        self.lastModified = datetime.datetime.now().isoformat()
    
    def updateHistory(self, prompt, nBees, nRounds, logs, response):
        # Create history entry
        history_entry = {
            "prompt": prompt, 
            "nBees": nBees, 
            "nRounds": nRounds, 
            "logs": logs, 
            "response": response,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Add to history
        self.history.append(history_entry)
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