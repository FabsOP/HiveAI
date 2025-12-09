# HiveAI - A Private LLM Hivemind You Can Run Yourself 🐝
<p align="center">
  <img width="683" height="384" alt="hiveai cover" src="https://github.com/user-attachments/assets/af68f69e-6105-451f-85d4-e41e2cf65cdd" />
</p>
<p align="center">
  <a href="https://x.com/Pot4toNinj4/status/1997732232686162257?s=20">Click here to see the hive in action</a>
</p>

## 1. Overview

HiveAI is a **multi-agent LLM hivemind** you can run on your own hardware (or rented GPUs) while keeping everything fully private.

Instead of relying on a single model to answer your questions, HiveAI spins up a **swarm of specialised agents called "bees"** that think together, debate, critique, and refine ideas. At the centre sits **the Queen**, a coordinating agent that manages context and turns the swarm’s raw thinking into a clean, structured answer.

Powered by **[Parallax](https://github.com/GradientHQ/parallax/tree/main)**, HiveAI talks to fully private LLM endpoints (local or remote tunnels), so your data never leaves your control. 

No SaaS APIs, no telemetry, just your own hive.
<img width="1365" height="591" alt="image" src="https://github.com/user-attachments/assets/866b8687-f6f6-48ca-ad84-8730668202fe" />

---

## 2. How It Works 🐝⚙️

At a high level, HiveAI is a **hivemind chat system**:

- You create a **Hive** for a conversation or project.
- Inside that hive you define a set of **Bees** (specialised agents) and a **Queen** (coordinator).
- When you send a prompt, the hive operates in **rounds**: each bee responds, bees discuss and debate, and then the Queen synthesizes the swarm's thinking into a single answer.

### 2.1 The Hive

A Hive is a collaborative reasoning space that bundles:

- **Bees** - individual AI agents with specific roles (e.g. Creative, Critic, Analyst).
- **Queen** - a special agent that manages context and synthesises outputs.
- **Memory** - persistent conversation history that the Queen can pull from.
- **Cluster** - a set of private LLM endpoints exposed by your Parallax setup.

### 2.2 Bees (Workers)

Bees are the specialised workers of the hive. Each bee has:

- **A Role** - the lens it brings to the problem (e.g. "Realist", "Creative").
- **A Model** - a Parallax-backed endpoint (local or remote tunnel).
- **Injections** - probability-based behavioural tweaks that can fire on certain rounds.

### 2.3 The Queen (Coordinator)

The Queen is responsible for turning multi-agent chaos into something useful, while staying neutral:

1. **Context provider** - fetches relevant memories from past discussions before each round and provides it to the bees.
2. **Aggregator** - reads all bee outputs and produces one clear, structured, actionable reply.
3. **Neutral summariser** - does not interpret the prompt herself or take a side; she only synthesises what the bees say back to you.

### 2.4 Rounds of Collaboration

Instead of a single-turn Q&A, HiveAI thinks in rounds:

1. **Prompt** - you send a request.
2. **Context** - the Queen pulls relevant history.
3. **Collaboration** - bees respond over **N rounds**, reading and building on each other.
4. **Aggregation** - the Queen compresses the swarm into a single answer.
5. **Storage** - the whole interaction is saved for future context.

### 2.5 Optional Injections for Extra Variety 🎲

On top of their normal roles, bees can optionally have **injections** attached to them during a discussion. These are small, temporary behavioural nudges that sometimes fire on a given round.

Instead of being part of the core loop, injections sit on top of it: they’re ephemeral, probability-based modifiers that occasionally push a bee to respond in a slightly different way (for example by challenging the previous point or adding a metaphor).

#### a) What Is an Injection?

An injection is a temporary instruction, constraint, or "creative spark" added to a bee’s prompt for a single round.

- **Ephemeral** - automatically removed after the round.
- **Non-destructive** - never permanently changes a bee’s identity or memory.
- **Additive at definition time** - you can define multiple injections for a single bee.

#### b) Interval Mechanism (Probability Rolls)

Each injection has an `interval` value (X), representing a `1/X` chance of activation per round:

- `interval = 1` → **100%** (always hits on the roll)
- `interval = 2` → **50%** chance each round
- `interval = 10` → **10%** chance each round

For a given bee:

1. **Roll independently** for each defined injection using its own `1/X` probability.
2. Collect all injections whose rolls **hit** on this round.
3. If **no** injections hit, the bee behaves normally.
4. If **exactly one** injection hits, apply that injection.
5. If **multiple** injections hit:
   - Prefer the one with the **lowest probability** (i.e. the **largest** `interval` value).
   - If several share the same lowest probability, pick **one of those at random**.

Only **one injection** is ever applied to a bee in a given round. This prevents contradictory instructions (e.g. “Be extra verbose” vs. “Don’t contribute to the discussion this round”) from being active at the same time.

#### c) How It Looks in Practice

When a round begins, the system performs a roll for every injection on every bee. Active injections are appended to a structured section of the system prompt, for example:

```text
# Special directive (Must follow):
Temporarily think out loud this round.
```

#### d) Why injections?

This injection system adds controlled randomness and variation to how bees respond, instead of being a simple prompt tweak:

- **Controlled stochasticity** boosts exploration without losing coherence.
- **Divergent behaviour** stops the hive from collapsing into repetitive loops.
- **Ensemble diversity** forces different perspectives for the Queen to synthesise.

---

## 3. 💡 Why a Hivemind?

A single LLM is good, but it thinks in **one voice**. A hive lets you orchestrate **many perspectives** working together, which:

- Improves reasoning depth and structure.
- Reduces blind spots through critique and debate.
- Produces richer, more creative emergent outputs.

This unlocks patterns like:

- Collaborative workflows where agents play different roles, like a real team.
- Multi-step pipelines where each bee specialises in a stage of the workflow.
- Divergent + convergent thinking, with some bees exploring and others refining.
- Brainstorming swarms that generate, debate, vote, cluster, and evolve ideas.

---

## 4. 🎯 Example Hive Setups

Two concrete examples you can build with HiveAI:

### a) Brainstorm Hive

- **Bees (3):**
  - **Dreamer** - generates wild, unconventional ideas and creative directions.
  - **Pragmatist** - filters ideas for feasibility and real-world constraints.
  - **Scout** - rapidly scans for overlooked angles, constraints, or opportunities that the others missed and brings them back to the hive.

### b) Debate Hive

Based on the `General Debate Hive [3vs3]` config in this repo.

- **Bees (6):**
  - **Team A - Ethics** - argues in favour from values, fairness, and long-term wellbeing.
  - **Team B - Ethics** - argues against from ethical risks, harms, and unfairness.
  - **Team A - Pragmatist** - focuses on practical implementation and feasibility for the pro side.
  - **Team B - Risk & Safety** - surfaces worst-case scenarios and safety concerns for the con side.
  - **Team A - Evidence & Impact** - brings data, evidence, and impact analysis for the pro side.
  - **Team B - Practical Skeptic** - questions feasibility, costs, and unintended side-effects for the con side.

In both setups, the Queen remains neutral and only synthesises the bees’ reasoning back to you.

---

## 5. 🚀 Getting Started

### Installation

```bash
git clone https://github.com/FabsOP/HiveAI.git
cd HiveAI
pip install -r requirements.txt
```

### Quick Start

1. **Launch the UI** - run `python app.py`.
2. **Create a Hive** - use the interface to spin up a new hive.
3. **Add Model Endpoints** - connect your Parallax endpoints (e.g. `http://localhost:3001`).
4. **Create Bees** - add bees to your hive through the UI.
5. **Attach Models** - assign models to your Queen and bees.
6. **Define Roles** - give each bee a clear role to guide behaviour.
7. **Add Injections (Optional)** - configure random injections to add variety.
8. **Start Collaborating** - ask a question and watch the bees think together in real time.






https://github.com/user-attachments/assets/94c84bf7-bd47-46c6-882d-cd665a15fabd







---

## 6. 🗺️ Future Roadmap

Some ideas for where HiveAI could go next:
- **New bee types** - new type of bees such as tool calling abilities
- **Document ingestion** - let hives read and reason over PDFs and text files.
- **Richer memory** - structured, long-term hive memory for projects.

---

## 7. 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

---

**Join the revolution in private, collaborative AI.**

*Powered by [Parallax](https://github.com/GradientHQ/parallax/tree/main)*
