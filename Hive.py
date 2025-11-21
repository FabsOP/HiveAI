class Hive:
    """A hive represents a chat session. Each hive has a queen bee and 0 or more worker bees"""
    def __init__(self):
        self.bees = [] # add queen
        self.models = []
        self.messages = []
        
        self.sequential = True

    def add_bee(self, bee):
        self.bees.append(bee)

    def remove_bee(self, bee):
        #if bee is not queen
        self.bees.remove(bee)

    def add_model(self, model):
        self.models.append(model)
    
    def remove_model(self, model):
        # warn if model is in use, all those bees will be removed
        self.models.remove(model)

    def query(self, prompt, n):
        #prompt goes to each bee in the hive
        
        # if sequential inference is enabled, prompt goes to each bee in order
        # if parallel inference is enabled, prompt goes to all bees at the same time
        
        #send to queen to aggregate responses
        #if success, return response
        #if failure, return error to chat "gpu out of memory, please decrease hive size, user a smaller model or use sequential inference"
        return "The consensus is that dogs are better than cats"

