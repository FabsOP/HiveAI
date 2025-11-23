############## IMPORTS ##############################
import Hive
import Bee


if __name__ == "__main__":

    ### Configure Hive ###
    modelA = "https://distant-guardian-starts-salaries.trycloudflare.com"   # Replace with your SSH-tunneled local port
    modelB = "https://golden-angel-tunnel.trycloudflare.com"

    h = Hive.Hive("Hive 1")
    h.set_randomize(False)

    h.add_model(modelA)
    h.add_model(modelB)

    ### Configure Queen ###
    h.getQueen().attach_model(h.getModels()[0])

    ### Configure Bees ###
    b1 = Bee.Bee("Creative", "Think outside the box")
    b2 = Bee.Bee("Pragmatic", "Think step by step")
    b3 = Bee.Bee("Analytical", "Think logically")

    #attach models
    b1.attach_model(h.getModels()[1])
    b2.attach_model(h.getModels()[1])
    b3.attach_model(h.getModels()[1])

    #define injections
    b1.addInjection("Disagree with previous speaker", 3)
    b1.addInjection("Agree with previous speaker", 3)
    b1.addInjection("Summarise what's discussed so far", 3)

    b2.addInjection("Agree with previous speaker", 3)
    b2.addInjection("Disagree with previous speaker", 5)
    b2.addInjection("Summarise what's discussed so far", 3)

    b3.addInjection("Summarise what's discussed so far", 3)
    
    ### Add bees to hive ###
    h.add_bee(b1)
    h.add_bee(b2)
    h.add_bee(b3)

    prompt = "How to survive a beer attack in a dark forest?"
    # h.query(prompt, 5)

    
    