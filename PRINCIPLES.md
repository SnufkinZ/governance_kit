# Core Design Principles

> The criteria by which any design proposal in this project is judged. Not style
> preferences — gates.
>
> **PORTING NOTE:** Principle 1 (Decoupling) is domain-neutral — keep it as is.
> Principle 2 below is a *placeholder* for your project's domain principle. The
> origin project used a "Complexity / emergence" principle grounded in biology.
> Replace §2 with your domain's equivalent, or delete it and keep Decoupling
> alone. The two-principle *structure* (one for code, one for behavior) is the
> transferable idea, not the specific second principle.

---

## TL;DR

1. **Decoupling Principle** — Modules depend on each other through narrow
   interfaces, never through internal implementation. Code can be modified,
   replaced, or extended locally without rippling through the system. This is
   what makes the codebase maintainable by both humans and AI.

2. **<Your domain principle>** — (placeholder) The rule that governs how the
   system *behaves*, as opposed to how its code is *structured*. See porting note.

The two look opposed but are complementary: decoupling governs **code
structure**; the domain principle governs **behavioral relationship**. In the
origin project they met at one answer: **narrow interfaces that allow rich state
reading** — code-wise A does not depend on B's internals; behavior-wise A's
output is deeply shaped by B's current state.

---

## 1. Decoupling Principle

### 1.1 Statement

Different functions and modules should be as decoupled as possible at the code
level. Modifying, adding, or removing one module should not require changes to
the internals of others.

### 1.2 Why this matters more in the AI-coding era

Traditional software engineering has always valued decoupling, but AI-assisted
development sharpens it:

- When AI modifies code, it loads relevant context into its context window. The
  tighter the coupling, the larger the surface AI must understand, the more
  tokens consumed, and the higher the error rate.
- In tightly coupled systems, "add one feature" often becomes "refactor half the
  codebase." AI fails at that kind of task at high rates.
- Decoupled systems let AI work **locally**: changing one module does not require
  re-understanding the whole system.

**Decoupling is not only for human collaboration; it is for human-AI
collaboration efficiency.** It is the property that makes the whole doc-driven
control model in `WORKFLOW.md` affordable — the human can stay at the design
layer only because a local code change stays local.

### 1.3 How decoupling should show up

- **Narrow cross-module interfaces.** Push every piece of information back to its
  proper owner instead of widening a shared message/struct "just in case."
- **Explicit state ownership.** Every mutable variable has one clear owner. You
  cannot reach into state from a position that does not own it. Make ownership
  obvious in names and type signatures.
- **Layered update frequencies.** Fast inner loops should not need to know what
  slow outer loops are doing; outer layers influence inner ones through a defined
  channel, not by reaching into their internal state.

### 1.4 Anti-pattern signals (decoupling is being violated)

- A module imports another module's private internals.
- A message/struct carrying fields that belong to a specific module's state.
- A field whose owner is unclear or split across components.
- A change to one module that requires "while you're there, also change…".
- A "controller"/"manager" that reaches into many modules' internals.

---

## 2. <Domain Principle — replace this section>

*(Placeholder. Example from the origin project, for shape only:)*

> **Complexity Principle** — No component is an island. Every part participates
> in the system's regulatory network, so complex capability emerges from simple
> rules interacting. Prefer emergence over hardcoded caps; use domain grounding
> as the constraint that tells you which mechanisms are principled.

Your project may not need a second principle at all. If it does, state it as a
rule about **behavior/relationships** (to complement Decoupling's rule about
**code structure**), give it a one-line test, and list its anti-patterns the way
§1.4 does.

---

## 3. How the two fit together

- Decoupling constrains **code dependency** — A's source must not import B's
  private internals.
- A behavioral principle constrains **behavioral coupling** — how deeply A's
  behavior may depend on B's current state.

Both can hold at once through **a narrow, well-defined interface that allows rich
state reading.** The interface is a knife edge; through it a rich state read is
possible.

---

## 4. Operating procedure

### 4.1 When proposing a new mechanism, ask in order

1. What problem in the system creates pressure for this mechanism? (No regulatory
   gap → maybe not needed.)
2. Can the desired behavior emerge from existing dynamics? Try that first.
3. If a hard mechanism is needed, what is its grounding? Without one, it is
   probably an island.
4. What is the narrowest interface that lets it participate? Resist adding fields
   to shared structures.
5. Who owns each new state variable? State without an owner is a future bug.

### 4.2 When AI is doing the work

- Keep modules small enough that one module + its direct interface partners fit
  comfortably in context.
- Document control locus (state ownership) at the top of each module.
- Use names/types that make ownership obvious.
- When asking AI to change something, point to the module and its interface, not
  the whole system.

---

## 5. One-sentence summary

> **The Decoupling Principle lets code be modified independently; the domain
> principle lets the system produce capability no one could design directly.**

The first solves the engineering problem. The second solves the capability
problem. Together, through "narrow interfaces + rich state reading," they form
one architecture the AI can safely work inside.
