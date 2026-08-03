# Presentation Narrative Guide (5–10 Minutes)

## How to Tell the Story

This guide provides the narrative flow for each key slide — what to **say** and **why**.

---

## Slide 1: Why Am I Working on This?

**Say:**

> Many researchers still manage multi-step computational campaigns using ad-hoc scripts and manual job submission. As workflows become more complex, this leads to increased manual effort, reduced reproducibility, and difficulty monitoring large campaigns.

> After attending the NERSC workflow automation training, I started exploring workflow technologies and AI-assisted workflow approaches that could potentially benefit S3DF users.

**Why this matters:** Don't start with Maestro or dashboards. Start with the **problem**.

---

## Slide 2: What Problem Am I Trying to Solve?

**Say:**

> Today, many users need to:
>
> - Create workflow definitions
> - Write Slurm scripts
> - Submit jobs
> - Monitor progress
> - Troubleshoot failures
> - Document results
>
> These activities can take significant time and often require substantial HPC experience.

**Then:**

> The goal of this project is to reduce this overhead and improve user productivity.

---

## Slide 3: Key Insight — AI Coordinates, Doesn't Replace

**When the slide says:** *"AI coordinates existing tools, doesn't replace them"*

**Say:**

> We already have excellent tools: Slurm, Maestro, Merlin, AiiDA. The idea is not to replace these systems. Instead, AI acts as an assistant that helps users create, manage, monitor, and troubleshoot workflows while leveraging existing infrastructure.

**Anticipate the question:** *"Are we introducing yet another workflow framework?"*

**Answer:**

> No. We're trying to make existing workflow technologies easier to use.

---

## Slide 4: Framework is Application-Agnostic

**Say:**

> ACE3P is currently the demonstration application because it's familiar to me and provides realistic workflow examples. However, the framework is intended to be application-agnostic. The same concepts could apply to:
>
> - ACE3P electromagnetic simulations
> - AI/ML training workflows
> - Data-analysis pipelines
> - Geant4 simulations
> - LCLS workflows
> - Any other S3DF application

**Why this is critical:** SCS is interested in **benefit to many users**, not benefit to ACE3P only. This slide connects your work to the broader S3DF mission.

---

## Slide 5: What Have I Built?

**Say:**

> I've developed a prototype that demonstrates the concept end-to-end:
>
> 1. A user describes their workflow in plain English
> 2. The AI generates a complete, validated workflow specification
> 3. The workflow submits to S3DF Slurm and runs autonomously
> 4. Results and plots are generated automatically
>
> I've validated this with real ACE3P simulations — eigenvalues match reference to 8 digits, and multipacting analysis produces physically meaningful results.

---

## Slide 6: Live Demo or Results

**Say:**

> Let me show you what this looks like in practice.

Then either run the live demo or show pre-captured results (see [demo-steps.md](demo-steps.md)).

**Key point to make:**

> From a one-line English description to physics results and plots — in about 5 minutes of wall time.

---

## Closing (30 seconds)

**Say:**

> My goal is to explore whether workflow automation, agentic AI, and user-friendly workflow interfaces can become a reusable capability that benefits the broader S3DF and SLAC community, with ACE3P serving as the initial demonstration application.

---

## Key Messages to Reinforce Throughout

| Message | Why It Matters |
|---------|---------------|
| AI assists, doesn't replace infrastructure | Avoids "yet another framework" concern |
| Application-agnostic | Shows broad value beyond ACE3P |
| Already working with real results | This isn't a proposal — it's a prototype with validated output |
| Reduces user learning curve | Connects to SCS mission of serving users |
| Reproducibility built in | Workflow YAML = executable documentation |
