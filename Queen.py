# queen is responsible for aggregating all bee responses after the round ends and delivering the final response to the user
# a larger model

class Queen:
    def __init__(self):
        self.name = "Queen"
        self.role = "Your role is to aggregate all bee responses after the round ends and deliver the final response to the user"
        self.model = None

        print("Queen created with role: " +  self.role)


    @staticmethod
    def from_dict(d):
        queen = Queen()
        queen.name = d.get("name", "Queen")
        queen.role = d.get("role", "Your role is to aggregate all bee responses after the round ends and deliver the final response to the user")
        # model is likely not serializable or is re-attached separately, 
        # but we can set it if provided, or leave as None (default)
        if "model" in d:
            queen.model = d["model"]
        return queen

    def to_dict(self):
        return {
            "name": self.name,
            "role": self.role,
            "model": self.model
        }

    def attach_model(self, model):
        self.model = model

    def detach_model(self):
        self.model = None


    def set_role(self, role):
        self.role = role

    def aggregate_response(self, prompt, logs):
        print("[Debug] Queen aggregating hive respose for query: " + prompt)
        assert self.model is not None, "Could not query " + self.name + ": Model not attached to queen"

        promptTemplate = ""
        #code to invoke model

        return "[Debug] <Aggregated Queen Response>"

    def extractContext(self, prompt, history):
        print("[Debug] Queen aggregating hive respose for query: " + prompt)
        assert self.model is not None, "Could not query " + self.name + ": Model not attached to queen"
        
        promptTemplate = ""
        #code to invoke model

        return "Debug <Context Fetched by Queen>" 
        