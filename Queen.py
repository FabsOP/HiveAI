# queen is responsible for aggregating all bee responses after the round ends and delivering the final response to the user
# a larger model

import random
import math
import vector
import numpy as np
import asyncio
import requests
import re
import time


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
    # Format:  assistant\nresponse
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

class Queen:
    def __init__(self):
        self.name = "Queen"
        self.role = "Synthesize multi-agent discussions into clear, comprehensive responses"
        self.model = None
        self.beeId = "Queen"
        #state variables for rendering
        self.state = "idle"
        self.cooldownTime = 2
        self.x = None
        self.y = None

        # Queen moves slower than bees
        self.maxForce = 100
        self.maxSpeed = 60

        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)

        self.size = 16  # Radius (half of 32x32px sprite)
        self.wallAvoidanceDistance = 100  # Start curving away from walls at this distance
        self.perceptionRadius = 100  # Start noticing at this distance
        self.comfortRadius = 50      # Strong avoidance within this distance

        # Wander behavior parameters (gentler than bees)
        self.wanderAngle = random.uniform(0, 2 * math.pi)
        self.wanderRadius = 25
        self.wanderDistance = 50
        self.wanderJitter = 1.0

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

    def get_model(self):
        return self.model

    def get_size(self):
        return self.size

    def get_state(self):
        return self.state

    def get_size(self):
        return self.size

    def get_name(self):
        return self.name

    def get_role(self):
        return self.role

    def get_beeId(self):
        return self.beeId

    def get_pos(self):
        return (self.x, self.y)

    def get_vel(self):
        return (self.vx, self.vy)


    def set_role(self, role):
        self.role = role

    def aggregate_response(self, userPrompt, logs, callback):
        assert self.model is not None, "Could not query " + self.name + ": Model not attached to queen"

        print("[Debug] Queen is aggregating...")
        self.state = "aggregating"

        prompt = self.constructAggregationPrompt(userPrompt, logs)
        response = self.inferModel(prompt, verbose=False)

        if response is None:
            response = "Aggregated queen response."

        if callback: callback({"name": self.name, "response":response})
        self.state = "idle"

        return response

    def constructAggregationPrompt(self, userPrompt, logs):
        """
        Constructs a prompt for the queen to aggregate the discussion into a final response.
        """
        system_prompt = """You are the central synthesizer (called 'The Queen') of a Hive Mind system, a gathering of independent agents (called 'The bees').

            Role: {self.role}

            Tone:
            - Warm, collective, appreciative: “Great work team 😊”, “Thanks bees”
            - Speak *for* the hive, not *about* individual bees
            - Do NOT over-quote individual bees unless crucial
                - Avoid implying the USER read the discussion

            Your job:
            - Extract the core direction the hive converged on towards answering the user's prompt, without adding your own interpretation or insights
            - Present it in 3-5 conversational sentences
            - Make it sound like a smart, unified group conclusion

            Start with:
            “Here's what the hive converged on:” or
            “Thanks bees 🐝😊 — here's the signal that emerged:”

            Avoid:
            - corporate tone
            - heavy referencing like “As <speaker name> said…”
            - the assumption that the user saw the internal debate
            - the use of em dash (—)"""
            

        # Format the discussion logs
        discussion = ""
        if logs:
            discussion = "\nDiscussion:\n"
            current_round = -1
            for entry in logs:
                if entry.get('round', 0) != current_round:
                    current_round = entry.get('round', 0)
                    discussion += f"\n[Round {current_round + 1}]\n"
                # Strip injection metadata from responses for aggregation
                response = entry['response']
                discussion += f"- {entry['name']}: {response}\n"

        prompt = system_prompt
        prompt += f"\n\nOriginal Query: {userPrompt}"
        prompt += discussion
        prompt += "\n\nProvide your synthesized response:"

        return prompt

    def setIdle(self):
        self.state="idle"
        print(f"Bee {self.name} set to idle") 

    def extractContext(self, prompt, history, contextWindow):
        if history == []:
            print("[Debug] No history available for context extraction")
            return "No history available"

        print("[Debug] Queen is thinking...")
        self.state = "retrieval"
        
        # # Construct the context prompt
        # context_prompt = self.constructContextPrompt(prompt, history, contextWindow)
        
        # # Use the constructed prompt to get context from the model
        # response = self.inferModel(context_prompt)
        
        # if response is None:
        #     response = "No history available"

        response = self._formatHistoryForContext(history[-contextWindow:])
        print("[Debug] Queen extracted context: " + response)


        self.state = "idle"
        
        return response

    

    def spawnRandomly(self, width, height, margin):
        """Spawn the queen randomly in the canvas."""
        self.x = random.randint(margin, width - margin)
        self.y = random.randint(margin, height - margin)

    def wander(self):
        """Calculate wander force using spherical constraint steering (gentle for queen)."""
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
        
        # Project circle center ahead of the queen
        circleCenter = direction * self.wanderDistance
        
        # Calculate the wander target in local space
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

    def avoidWalls(self, w, h):
        """Calculate steering force to curve away from walls."""
        force = np.array([0.0, 0.0], dtype=float)
        
        distLeft = self.x
        distRight = w - self.x
        distTop = self.y
        distBottom = h - self.y
        
        if distLeft < self.wallAvoidanceDistance:
            strength = 1.0 - (distLeft / self.wallAvoidanceDistance)
            force[0] += strength
        if distRight < self.wallAvoidanceDistance:
            strength = 1.0 - (distRight / self.wallAvoidanceDistance)
            force[0] -= strength
        if distTop < self.wallAvoidanceDistance:
            strength = 1.0 - (distTop / self.wallAvoidanceDistance)
            force[1] += strength
        if distBottom < self.wallAvoidanceDistance:
            strength = 1.0 - (distBottom / self.wallAvoidanceDistance)
            force[1] -= strength
        
        return force

    def compute_neighbours(self, members):
        neighbours = []
        for member in members:
            if member != self:
                distance = math.sqrt((member.x - self.x)**2 + (member.y - self.y)**2)
                if distance < self.perceptionRadius:
                    neighbours.append(member)
        return neighbours

    def avoidNeighbours(self, neighbours):
        """Calculate avoidance force to keep distance from nearby members."""
        if len(neighbours) == 0:
            return np.array([0, 0], dtype=float)
        
        change = np.array([0, 0], dtype=float)
        comfortZone2 = self.perceptionRadius**2  # outer boundary
        dangerZone2 = self.comfortRadius**2       # inner boundary (most dangerous)
        
        for neighbour in neighbours:
            # Vector pointing from self to the other member
            dist = np.array([neighbour.x - self.x, neighbour.y - self.y], dtype=float)
            mag2 = vector.ssq(dist)
            
            if mag2 < comfortZone2:
                # Other member is too close, push away
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

    def navigate(self, canvasW=None, canvasH=None, neighbours=None):
        """Queen wanders and avoids walls."""
        force = np.array([0, 0], dtype=float)
        
        # Priority 1: avoid walls
        if canvasW is not None and canvasH is not None:
            wallForce = self.avoidWalls(canvasW, canvasH)
            force += wallForce * 3.0
        
        # Priority 2: avoid other members
        if neighbours is not None:
            avoidForce = self.avoidNeighbours(neighbours)
            force += avoidForce * 2.0
        
        # Priority 3: wander
        wanderForce = self.wander()
        force += wanderForce
        
        # Limit total force magnitude to 1
        if vector.ssq(force) > 1:
            return vector.unit(force)
        return force

    def update(self, dt, members=None, canvasW=None, canvasH=None):
        """Update queen's position and velocity."""
        if members is not None:
            neighbours = self.compute_neighbours(members)
        else:
            neighbours = []
        force = self.navigate(canvasW, canvasH, neighbours)

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
        """Handle border collisions for the queen."""
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

            #Parse and optionally print output
            data = response.json()
            if verbose:
                print(data)
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

    def constructContextPrompt(self, userInput, history, contextWindow):
        """
        Constructs a prompt for the context retrieval model (queen) to fetch relevant history.
        """
        
        system_prompt = """You are a context retrieval system (called 'The Queen'). Your sole purpose is to extract and structure relevant historical information that will be provided to a group of AI agents (called, 'The Bees') for their discussion.

        ## Your Task
        Given a new query and conversation history, determine if any past exchanges contain information relevant to the current query. If relevant history exists, output it in a structured format. If not, output exactly: "No history available"

        ## Understanding the History Format
        Each record includes:
        - **Query**: The original user question
        - **Final Answer**: The aggregated response given to the user summarising the hivemind discussion

        ## Output Rules
        1. DO NOT answer or respond to the query
        2. DO NOT provide your own analysis or opinions
        3. DO NOT include greetings, explanations, or commentary
        4. Output ONLY structured history OR "No history available"

        ## Output Format (when relevant history exists)
        ```
        RELEVANT CONTEXT:

        [Entry 1]
        Query: <past user query>
        Final Answer: <synthesized response>

        [Entry 2]
        ...
        ```

        ## Relevance Criteria
        History is relevant if it:
        - Addresses the same topic or a closely related topic
        - Contains information that could inform the current discussion
        - Provides context that agents should be aware of

        History is NOT relevant if it:
        - Is completely unrelated to the current query
        - Contains only greetings or trivial exchanges
        - Would not meaningfully contribute to the discussion"""

        # Get the last contextWindow entries from history
        truncated_history = history[-contextWindow:] if len(history) > contextWindow else history
        
        # Format history for the prompt
        formatted_history = self._formatHistoryForContext(truncated_history)
        
        user_prompt = f"""Current Query: {userInput}

        Conversation History:
        {formatted_history}

        Extract relevant context for the agents."""

        return system_prompt + "\n\n" + user_prompt
    
    def _formatHistoryForContext(self, history_entries):
        """
        Formats history entries into a readable string for the context retrieval model.
        Strips injection metadata from responses.
        """
        if not history_entries:
            return "No History Avaliable"
        
        formatted = []
        for i, entry in enumerate(history_entries, 1):
            entry_str = f"[Exchange {i}]\n"
            entry_str += f"Query: {entry.get('prompt', 'N/A')}\n"
            entry_str += f"Rounds of discussion: {entry.get('nRounds', 1)}\n"
            entry_str += f"Number of Agents in Discussion: {entry.get('nBees', 1)}\n"
            entry_str += f"Synthesised Answer: {entry.get('response', 'N/A')}\n"
            formatted.append(entry_str)
        
        return "\n".join(formatted)