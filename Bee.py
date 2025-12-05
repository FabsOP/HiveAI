######## IMPORTS ########
import uuid
import random
import time
import math
import vector
import asyncio
import numpy as np
import requests
import re


def extract_final_response(content):
    """
    Extracts the final message from model output, handling formats for:
    - Qwen3/Qwen2.5 (Instruct & Thinking)
    - Kimi-K2 (Instruct & Thinking)  
    - openai/gpt-oss (20b, 120b, safeguard)
    - DeepSeek (V3, V2.5, R1)
    - GLM-4.x (zai-org)
    - MiniMax-M2
    - Llama-3.x (nvidia)
    """
    if not content:
        return content
    
    original = content.strip()
    result = original
    
    # === Pattern 1: OpenAI/gpt-oss channel format ===
    # Format: <|channel|>analysis<|message|>...<|end|><|start|>assistant<|channel|>final<|message|>RESPONSE
    final_channel_pattern = r'<\|channel\|>final<\|message\|>(.*?)(?:<\|end\|>|<\|start\|>|$)'
    final_match = re.search(final_channel_pattern, content, re.DOTALL)
    if final_match:
        return final_match.group(1).strip()
    
    # Also handle: <|start|>assistant<|channel|>...<|message|>RESPONSE
    simple_channel = r'<\|message\|>([^<]+)(?:<\|end\|>|$)'
    simple_match = re.search(simple_channel, content, re.DOTALL)
    if simple_match and '<|channel|>' in content:
        # Get the last message content
        all_messages = re.findall(simple_channel, content, re.DOTALL)
        if all_messages:
            return all_messages[-1].strip()
    
    # === Pattern 2: Thinking models (Qwen3-Thinking, Kimi-K2-Thinking, DeepSeek-R1) ===
    # Format: <think>internal reasoning</think>actual response
    think_pattern = r'<think>.*?</think>\s*'
    if '<think>' in result:
        result = re.sub(think_pattern, '', result, flags=re.DOTALL).strip()
        if result:
            return result
    
    # Also handle: <|think|>...<|/think|> variant
    think_pipe_pattern = r'<\|think\|>.*?<\|/think\|>\s*'
    if '<|think|>' in result:
        result = re.sub(think_pipe_pattern, '', result, flags=re.DOTALL).strip()
        if result:
            return result
    
    # === Pattern 3: GLM-4.x format ===
    # Format: <|assistant|>response or <|assistant|>\nresponse
    glm_pattern = r'<\|assistant\|>\s*(.*)$'
    glm_match = re.search(glm_pattern, content, re.DOTALL)
    if glm_match:
        return glm_match.group(1).strip()
    
    # === Pattern 4: Qwen ChatML format ===
    # Format:  <|im_start|>assistant\nresponse<|im_end|>
    chatml_pattern = r'<\|im_start\|>assistant\n(.*?)(?:<\|im_end\|>|$)'
    chatml_match = re.search(chatml_pattern, content, re.DOTALL)
    if chatml_match:
        return chatml_match.group(1).strip()
    
    # === Pattern 5: Llama format ===
    # Format: [INST]prompt[/INST]response or just response after [/INST]
    llama_pattern = r'\[/INST\]\s*(.*)$'
    llama_match = re.search(llama_pattern, content, re.DOTALL)
    if llama_match:
        return llama_match.group(1).strip()
    
    # === Pattern 6: Generic cleanup ===
    # Remove stray special tokens at boundaries
    cleanup_patterns = [
        r'^<\|[^|]+\|>',           # Leading special tokens
        r'<\|[^|]+\|>$',           # Trailing special tokens  
        r'^\[INST\].*?\[/INST\]',  # Full INST blocks at start
        r'<\|endoftext\|>$',       # End of text marker
        r'<\|eot_id\|>$',          # Llama3 end token
        r'<\|end\|>$',             # Generic end token
    ]
    
    result = original
    for pattern in cleanup_patterns:
        result = re.sub(pattern, '', result, flags=re.DOTALL).strip()
    
    return result if result else original


class Bee:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.model = None
        self.injections = []
        self.beeId = str(uuid.uuid1())

        #state variables for rendering
        self.state = "idle"
        self.x = None
        self.y = None

        self.maxForce = 200
        self.maxSpeed = 100

        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)

        self.size = 12

        self.perceptionRadius = 100  # Start noticing at this distance
        self.comfortRadius = 200      # Strong avoidance within this distance
        self.wallAvoidanceDistance = 100  # Start curving away from walls at this distance

        # Wander behavior parameters
        self.wanderAngle = random.uniform(0, 2 * math.pi)
        self.wanderRadius = 30
        self.wanderDistance = 50
        self.wanderJitter = 1.5

        print("[Debug] Bee " + self.name + " created with id " + self.beeId + " and role " + self.role)
    
    def to_dict(self):
        return {
            "name": self.name,
            "beeId": self.beeId,
            "role": self.role,
            "model": self.model,
            "injections": self.injections
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
        print("[Debug] Injection added to " + self.name + " Bee with id " + injectionId)

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
        print("[Debug] Injections for " + self.name + "Bee :")
        for injection in self.injections:
            print(injection)

    def query(self, userPrompt, context, log, callback=None):
        assert self.model is not None, "Could not query " + self.name + ": Model not attached to bee"

        print("[Debug] " + self.name + " bee is thinking...")
        self.state = "thinking"
        
        # Send callback when bee starts thinking
        if callback:
            callback({"name": "__bee_thinking__", "response": None, "bee_id": self.beeId})
        
        #### a) Roll injections
        successfull_injections = []
        for injection in self.injections:
            target = injection['interval']
            roll = random.randint(1, target)
            if roll == target:
                successfull_injections.append(injection)
                print("[Debug] 🎲 Injection " + f"'{injection['behaviour']}'" + " successful for " + self.name + " Bee")

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
                print("[Debug] There were " + str(len(successfull_injections)) + " injections successful for the" + self.name + " Bee, picked " + "'"+ injection['behaviour'] +"' with interval " + str(injection['interval']))

        #### c) Generate response
        prompt = self.constructPrompt(userPrompt, context, log, injection)
        response = self.inferModel(prompt, verbose=False) 
        
        if response is None:
            response = f"Bee Reply"
        if injection:
            response += f"\nInjection: {injection}\n\n"

        if callback: callback({"name": self.name, "response":response})

        self.state = "idle"

        
        return response

    def constructPrompt(self, userPrompt, context, logs, injection=None):
        """
        Constructs a prompt for the bee to participate in the round-table discussion.
        """
        # Find the most recent bee before this one
        previousBee = None
        if logs:
            for entry in reversed(logs):
                if entry['name'] != self.name:
                    previousBee = entry['name']
                    break

        system_prompt = f"""You are {self.name}, one conscious thread within a shared Hive Mind of agents (called the Bees).  

        You do NOT speak as an isolated expert — you speak as part of a living network.

        ROLE: {self.role}

        Your communication style MUST follow these rules:

        1. Always sound like part of a shared hivemind.
        - In your first sentence, you may choose to naturally reference another bee from the active discussion.
        - * You may reference any bee, not just the previous speaker. *
        - If you decide to reference the immediately previous speaker, speak directly using 'you' or "you're".
            Eg. "I see what you're getting at"  or "I want to add to what you mentioned ..." 
        - If you reference a non previous speaker, use their name naturally:
            Eg. "Building on what <speaker name> said" or "I like <speaker name>'s angle"
        - You may disagree with a bee if their point conflicts with your role's expertise or the facts.
            Eg. "I see your point <speaker name>, but from my angle..." or "I'd push back on that because..."
        - Keep the reference natural and vary your phrasing
        - If you are the first to speak, begin by saying "I'll start us off" or "I'll begin"

        2. Only reference bees whose names appear in the discussion log.  
        - Never invent or guess new names.


        3. Keep responses short (1-2 sentences), BUT conversational and connective.  
        Your job is to *continue the thread of thinking*, not to provide isolated insights.

        4. Use hive-like language subtly:
        “we're syncing on…”, “the hive seems aligned…”, “building collective clarity…”

        5. NO lists, NO tables, NO formatting.  
        Speak like fast back-and-forth thinking within a team.

        6. Provide one clear addition, correction, or challenge to the ongoing thread.

        7. Add personality using emojis related to your role.

        If a special directive is active, incorporate it naturally without breaking the conversational tone."""

        # Add injection if present
        if injection:
            system_prompt += f"\n\nSpecial Directive (must follow): {injection['behaviour']}"

        # Format the discussion logs
        discussion = ""
        if logs:
            discussion = "\n\nDiscussion so far:\n"
            for entry in logs:
                # Strip injection metadata from responses to prevent other bees from seeing them
                response = entry['response']
                if '\nInjection:' in response:
                    response = response.split('\nInjection:')[0].strip()
                discussion += f"- {entry['name']}: {response}\n"
        else:
            discussion = "\n\nYou are the first to speak."

        # Build the full prompt
        prompt = system_prompt
        
        if context and context != "No history available":
            prompt += f"\n\nRelevant Context from Previous Sessions:\n{context}"
        
        prompt += f"\n\nTopic: {userPrompt}"
        prompt += discussion
        prompt += f"\n\n{self.name}, share your perspective:"

        return prompt

    def setIdle(self):
        self.state="idle"
        print(f"Bee {self.name} set to idle")  
        

    def inferModel(self, prompt, max_output_tokens=1024, verbose=True):
        assert self.model is not None, "Could not query " + self.name + ": Model not attached to bee"
        # Request payload
        payload = {
            "max_tokens": max_output_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": False}
        }

        try:
            #Send POST request
            # Ensure no double slash in URL
            model_url = self.model.rstrip('/') + '/v1/chat/completions'
            response = requests.post(model_url, json=payload)
            response.raise_for_status() # Raise an exception for bad status codes

            #Parse and print output
            data = response.json()
            # print(data)
            content = data["choices"][0]["message"]["content"]
            
            # Extract final response (handles various model output formats)
            reply = extract_final_response(content)

            if verbose:
                print(f"Response Json: {data}\n")
                print(f"User: {prompt}\n")
                print(f"Reply:\n{reply}\n")

            return reply

        except requests.exceptions.RequestException as e:
            print(f"Error making request to model: {e}")
            return None

    def get_pos(self):
        return (self.x, self.y)

    def get_vel(self):
        return (self.vx, self.vy)

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

    def get_state(self):
        return self.state

    def get_size(self):
        return self.size

    def spawnRandomly(self, width, height, margin):
        #spawn a bee randomly in a box or canvas 
        #margin to avoid bees spawning too close to the edges
        self.x = random.randint(margin, width - margin)
        self.y = random.randint(margin, height - margin)
        
    def avoidWalls(self, w, h):
        """Calculate steering force to curve away from walls."""
        force = np.array([0.0, 0.0], dtype=float)
        
        # Distance to each wall
        distLeft = self.x
        distRight = w - self.x
        distTop = self.y
        distBottom = h - self.y
        
        # Apply force away from walls within avoidance distance
        if distLeft < self.wallAvoidanceDistance:
            strength = 1.0 - (distLeft / self.wallAvoidanceDistance)
            force[0] += strength  # Push right
        if distRight < self.wallAvoidanceDistance:
            strength = 1.0 - (distRight / self.wallAvoidanceDistance)
            force[0] -= strength  # Push left
        if distTop < self.wallAvoidanceDistance:
            strength = 1.0 - (distTop / self.wallAvoidanceDistance)
            force[1] += strength  # Push down
        if distBottom < self.wallAvoidanceDistance:
            strength = 1.0 - (distBottom / self.wallAvoidanceDistance)
            force[1] -= strength  # Push up
        
        return force

    def compute_neighbours(self, bees):
        neighbours = []
        for bee in bees:
            if bee != self:
                distance = math.sqrt((bee.x - self.x)**2 + (bee.y - self.y)**2)
                if distance < self.perceptionRadius:
                    neighbours.append(bee)
        return neighbours

    def wander(self):
        """Calculate wander force using spherical constraint steering."""
        # Add small random displacement to wander angle
        self.wanderAngle += random.uniform(-self.wanderJitter, self.wanderJitter)
        
        # Calculate point on wander sphere
        sphereX = self.wanderRadius * math.cos(self.wanderAngle)
        sphereY = self.wanderRadius * math.sin(self.wanderAngle)
        
        # Get velocity direction (or random if velocity is zero)
        velocity = np.array([self.vx, self.vy], dtype=float)
        speed = vector.magnitude(velocity)
        
        if speed < 0.001:  # velocity is essentially zero
            # Pick a random direction
            randomAngle = random.uniform(0, 2 * math.pi)
            direction = np.array([math.cos(randomAngle), math.sin(randomAngle)], dtype=float)
        else:
            direction = vector.unit(velocity)
        
        # Project circle center ahead of the bee
        circleCenter = direction * self.wanderDistance
        
        # Calculate the wander target in local space
        # We need to rotate the sphere point to align with the direction of motion
        # Using a simple 2D rotation based on the direction vector
        angle = math.atan2(direction[1], direction[0])
        
        # Rotate sphere point by the direction angle
        rotatedX = sphereX * math.cos(angle) - sphereY * math.sin(angle)
        rotatedY = sphereX * math.sin(angle) + sphereY * math.cos(angle)
        
        # Wander target is circle center + rotated sphere point
        wanderTarget = circleCenter + np.array([rotatedX, rotatedY], dtype=float)
        
        # Return steering force (normalized)
        if vector.ssq(wanderTarget) > 1:
            return vector.unit(wanderTarget)
        return wanderTarget

    def avoidNeighbours(self, neighbours):
        """Calculate avoidance force to keep distance from nearby bees."""
        if len(neighbours) == 0:
            return np.array([0, 0], dtype=float)
        
        change = np.array([0, 0], dtype=float)
        comfortZone2 = self.perceptionRadius**2  # outer boundary
        dangerZone2 = self.comfortRadius**2       # inner boundary (most dangerous)
        
        for neighbour in neighbours:
            # Vector pointing from self to the other bee
            dist = np.array([neighbour.x - self.x, neighbour.y - self.y], dtype=float)
            mag2 = vector.ssq(dist)
            
            if mag2 < comfortZone2:
                # Other bee is too close, push away
                # Decide how strongly to accelerate away
                pushStrength = (comfortZone2 - mag2) / (comfortZone2 - dangerZone2)
                
                if pushStrength > 1:
                    pushStrength = 1
                    
                dist = vector.unit(dist) * pushStrength
                change -= dist  # Push away (subtract because we want to move opposite direction)
        
        # Limit change magnitude to 1
        if vector.ssq(change) > 1:
            return vector.unit(change)
        return change

    def navigate(self, neighbours, canvasW=None, canvasH=None):
        # compute netForce
        force = np.array([0, 0], dtype=float)

        # Priority 1: avoid walls (highest priority)
        if canvasW is not None and canvasH is not None:
            wallForce = self.avoidWalls(canvasW, canvasH)
            force += wallForce * 3.0  # Walls get extra weight

        # Priority 2: avoid other bees
        avoidForce = self.avoidNeighbours(neighbours)
        force += avoidForce
        
        # Priority 3: wander
        wanderForce = self.wander()
        force += wanderForce
        
        # Limit total force magnitude to 1
        if vector.ssq(force) > 1:
            return vector.unit(force)
        return force

    def update(self, dt, bees, canvasW=None, canvasH=None):
        neighbours = self.compute_neighbours(bees)
        force = self.navigate(neighbours, canvasW, canvasH)

        # Scale force by maxForce and apply with dt
        self.vx += force[0] * self.maxForce * dt
        self.vy += force[1] * self.maxForce * dt

        # Limit velocity to maxSpeed
        if vector.ssq([self.vx, self.vy]) > self.maxSpeed**2:
            newV = self.maxSpeed * vector.unit([self.vx, self.vy])
            self.vx = newV[0]
            self.vy = newV[1]
        
        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt
           
    def handleBorders(self, w, h, borderType="Bounce"):
        if borderType == "Wrap":
            if self.x > w or self.x < 0:
                self.x = self.x % w
            if self.y > h or self.y < 0:
                self.y = self.y % h
        elif borderType == "Bounce":
            # size is treated as radius (half of sprite width)
            # x coords
            hitLeft = self.x - self.size <= 0 and self.vx < 0
            hitRight = self.x + self.size >= w and self.vx > 0
            if hitLeft or hitRight:
                self.x = (self.size if hitLeft else w - self.size)
                self.vx *= -1
                # Reset wander angle to point away from wall
                self.wanderAngle = math.atan2(self.vy, self.vx)
            
            # y coords   
            hitBottom = self.y + self.size >= h and self.vy > 0
            hitTop = self.y - self.size <= 0 and self.vy < 0
            if hitBottom or hitTop:
                self.y = (self.size if hitTop else h - self.size)
                self.vy *= -1
                # Reset wander angle to point away from wall
                self.wanderAngle = math.atan2(self.vy, self.vx)