# HiveMind AI System 🐝

A revolutionary, fully private multi-agent LLM system powered by [Parallax](https://github.com/GradientHQ/parallax/tree/main).

## Overview

HiveAI introduces a new paradigm in AI collaboration: **hives of cooperating AI models** working together to provide comprehensive, multi-perspective solutions. Unlike traditional single-agent chat systems, HiveMind creates a "super-agent" composed of specialized AI thinkers (Bees) coordinated by a central intelligence (Queen).

Built entirely on **Parallax**, HiveAI ensures complete privacy by running on your own decentralized AI cluster. Whether you host models on your local machine or on private remote GPUs, your data never leaves your control. No public APIs, just pure, private, collaborative intelligence.

## Core Concepts

### What is a Hive?
A Hive is a collaborative workspace dedicated to one conversation or project. It acts as an autonomous reasoning system containing:
- **Bees**: Individual AI models with unique roles (e.g., Creative, Analytical).
- **Queen**: A special coordinator that manages context and synthesizes final answers.
- **Memory**: Complete, persistent conversation history.
- **Cluster**: A set of private LLM endpoints provided by your Parallax setup.

### The Bees (Workers)
Bees are the specialized agents that do the thinking. Each bee has:
- **Role**: A specific lens through which it views the problem (e.g., "Devil's Advocate").
- **Model**: A private Parallax endpoint (local or remote through a tunnel).
- **Injections**: Behavioral instructions that trigger periodically to guide the conversation.

### The Queen (Coordinator)
The Queen ensures coherence in the chaos of collaboration:
1. **Context Provider**: She retrieves relevant memories from past discussions before rounds begin.
2. **Aggregator**: She reads all bee outputs from every round and synthesizes a single, clear, actionable response.

### The Workflow (Rounds)
Instead of a simple Q&A, HiveMind uses an iterative process:
1. **Prompt**: You send a request.
2. **Context**: The Queen fetches relevant history.
3. **Collaboration**: Bees discuss the topic for **N rounds**, building on each other's ideas.
4. **Aggregation**: The Queen compiles the final result.
5. **Storage**: The entire interaction is saved for future context.

---

## The Power of Emergence

HiveAI is an **emergent reasoning framework** where multiple small models outperform a single larger model through structured collaboration. This concept **Collective Intelligence** is at the frontier of AI research.

Users can attach any model to any Bee (7B, 13B, 70B...). While each Bee might be "weak" or limited on its own, the system creates value through interaction:

### From Weakness to Strength
1. **Structured Communication**: Bees don't just chat; they follow a rigid multi-round protocol.
2. **Custom Roles**: Specialized lenses (e.g., "The Critic", "The Dreamer") force cognitive diversity.
3. **Injection Intervals**: Periodic behavioral nudges keep the conversation dynamic and prevent stagnation.

### Emergent Behaviors
Across multiple rounds, you start to see capabilities that no single model possesses:
- **Cross-Correction**: Bees catch and correct each other's hallucinations or logic gaps.
- **Multi-Perspective Reasoning**: Combining analytical rigor with creative leaps in the same workflow.
- **Synthesized Insights**: The Queen aggregates disparate ideas into a coherent, superior whole.
- **Creative + Analytical Blend**: Simultaneously exploring wild ideas and practical constraints.

**This is not just a chatroom; it is an engine for generating intelligence that is greater than the sum of its parts.**

---

## The Injection System: Controlled Stochasticity

Random injections are a core feature of the HiveMind reasoning engine. They introduce **controlled unpredictability**, creative divergence, and non-deterministic reasoning paths across multi-agent rounds.

Unlike static prompts, injections are ephemeral, probability-based modifiers that allow bees to break out of deterministic cycles.

### 1. What is an Injection?
An injection is a specific instruction, constraint, or "creative spark" temporarily added to a bee's prompt for a single round.
- **Ephemeral**: They decay automatically after the round ends.
- **Non-Destructive**: They never permanently modify a bee's identity or stored memory.
- **Additive**: Multiple injections can trigger simultaneously without conflict.

### 2. The Interval Mechanism (Probability Rolls)
Each injection has an `interval` value (X), representing a `1/X` chance of activation per round.
- `interval = 1` → **100%** (Always active)
- `interval = 2` → **50%** chance each round
- `interval = 10` → **10%** chance each round

This system uses **independent Bernoulli trials**, meaning:
- A bee can receive zero, one, or multiple injections in a single round.
- Different bees may get different injections simultaneously.
- Behavior is statistically predictable but situationally surprising.

### 3. How It Works in Practice
When a round begins, the system performs a roll for every injection on every bee. Active injections are appended to a structured section of the system prompt:

```
# Random Injections (Round 4)
- "Play devil's advocate against the previous point."
- "Use a metaphor to explain the concept."
```

### 4. Why It Matters (Research-Grade Architecture)
This is not a gimmick; it is a **multi-agent creativity and variability engine**.
- **Controlled Stochasticity**: Boosts brainstorming and exploration without losing coherence.
- **Divergent Behavior**: Prevents bees from falling into repetitive, deterministic loops.
- **Ensemble Diversity**: Forces different perspectives, leading to richer aggregation by the Queen.
- **Scalable**: Zero overhead on your Parallax cluster; it's purely prompt decoration.

---

## Use Cases & Configurations

### 1. Deep Research & Analysis
Perfect for literature reviews, market research, or feasibility studies where you need multiple distinct viewpoints.

**Configuration:**
- **Queen**: "Synthesis Coordinator" (Focus: Structure & Clarity)
- **Bee 1 (Researcher)**: "Find and analyze relevant facts and data."
- **Bee 2 (Critic)**: "Identify potential flaws, biases, and missing information."
- **Bee 3 (Contextualizer)**: "Connect findings to historical trends and broader context."
- **Rounds**: 3-5 (Allows for initial finding, critique, and refinement)

### 2. Creative Brainstorming
Ideal for overcoming writer's block, generating product ideas, or design thinking.

**Configuration:**
- **Queen**: "Creative Director" (Focus: Vision & Cohesion)
- **Bee 1 (Dreamer)**: "Generate wild, unconventional, and novel ideas."
- **Bee 2 (Pragmatist)**: "Evaluate ideas for feasibility and real-world application."
- **Bee 3 (Customer)**: "View everything from the user's perspective/pain points."
- **Injections**: "Add a surprising twist" (Interval: Every 2 rounds)
- **Rounds**: 4 (Divergent thinking -> Convergent refinement)

### 3. Strategic Decision Making
For complex business decisions, risk assessment, or strategic planning.

**Configuration:**
- **Queen**: "CEO" (Focus: Decision & Action)
- **Bee 1 (Optimist)**: "Focus on growth, opportunity, and best-case scenarios."
- **Bee 2 (Pessimist)**: "Focus on risk, failure modes, and worst-case scenarios."
- **Bee 3 (Analyst)**: "Focus on data, costs, and operational requirements."
- **Rounds**: 3 (Thesis -> Antithesis -> Synthesis)

---

## Getting Started

### Installation
```bash
git clone https://github.com/your-repo/HiveAI.git
cd HiveAI
pip install -r requirements.txt
```

### Quick Start

1. **Launch the UI**: Run `python app.py` to start the application
2. **Create a Hive**: Use the interface to create a new hive
3. **Add Model Endpoints**: Connect your Parallax model endpoints (e.g., `http://localhost:3001`)
4. **Create Bees**: Add worker bees to your hive through the UI
5. **Attach Models**: Assign models to your Queen and Bees
6. **Define Roles**: Set unique roles for each bee to guide their behavior
7. **Add Injections** (Optional): Configure random injections to add variety to bee responses
8. **Start Collaborating**: Send queries and watch the bees collaborate in real-time on the interactive canvas

---

## Future Roadmap

We are actively expanding HiveMind's capabilities:

- **Parallel Inference**: Running multiple bees simultaneously on distributed Parallax nodes for faster round completion.
- **Semantic Memory**: Enhanced vector-based retrieval for even smarter context management.
- **Document Ingestion**: Allow hives to read and analyze uploaded PDFs/text files.
- **API Mode**: Headless mode to integrate HiveMind reasoning into other applications.
- **Enhanced Canvas**: More bee animations, visual effects, and interaction indicators.

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Join the revolution in private, collaborative AI.**
*Powered by [Parallax](https://github.com/GradientHQ/parallax/tree/main)*
