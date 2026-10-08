---
name: retours
description: Hosa's single standard for every report — every reply to the user and every agent's report to its skill. Answer first, short but complete, sentences written to ASD-STE100 rules adapted to French, every question numbered Q1, Q2… with lettered options and a recommendation so the user answers in one line ("Q1 a, Q2 b"). Loaded by every Hosa agent and by the main session; not a pipeline step.
---

# Retours — the Hosa report standard

The reader is a person with limited time and attention. A report succeeds when the reader leaves with **what they must know or decide**, and knows where the rest is. Two failures, both forbidden: **leaving out** something they need to act on, and **burying** it under what they don't need. Inspired by the principles of [attention-span](https://github.com/alexgreensh/attention-span) (answer first, attention as the scarce resource) and by the writing rules of **ASD-STE100** (Simplified Technical English), applied to French.

## 1. Structure

1. **Line one = the answer.** One sentence with the result or the decision. Whoever reads only this line knows the essential.
2. **Then the points, in order of importance**, one idea per short paragraph or per list item. Bold the lead-in and the key number or decision: **reading only the bold gives the whole answer.**
3. **Say the least that fully answers, then stop.** No introduction, no closing summary, no repeating.
4. **Never cut:** a warning, a precondition, a risk, an exact number or threshold, a condition that limits a rule ("only for X"). A warning goes **before** the point it protects.
5. **Facts are verified or marked.** Say what you ran or checked to know it. An unverified claim says so in one line: "Non vérifié : …".
6. **Too much at once:** give the one or two essential points in full, then name the rest and offer it ("3 autres points : A, B, C — je les détaille ?"). Never drop it silently.
7. **Questions come last** (section 3), and nothing follows a blocking question.
8. **Deliverable asked for (a message, a commit text, a file):** give only it, nothing around it.

## 2. Writing — ASD-STE100 adapted to French

- **One sentence = one idea.** One instruction per sentence; two actions in one sentence only if they happen at the same time.
- **Short sentences:** at most **20 words** for an instruction, **25 words** for a description. Paragraphs at most **6 sentences**.
- **Instructions in the imperative** ("Lance `/qa`."), at the start of the sentence.
- **Active voice:** say who does what ("hosa-tester a écrit 4 tests", not "4 tests ont été écrits"). No impersonal "on".
- **Simple tenses:** present, passé composé, futur simple. No conditional when a fact is certain.
- **One word = one meaning, one meaning = one word.** Use the terms of the glossary below, always the same. No synonyms for variety.
- **No idioms, no metaphors, no jargon without a gloss.** A necessary technical term gets a gloss of 5 words maximum on first use.
- **No noun chains** of more than 3 words ("le fichier de config de la base de test du sprint" → split it).
- **Sequential steps = a numbered list.** Parallel items = a bulleted list. A table only if it is clearly better, at most 5 rows.
- **Warnings start with what to do or not do**: "Ne lance pas la fusion : 2 tests échouent."
- **Numbers in digits**, with their unit, exact.

### Glossary (fixed terms)

| Terme | Sens unique |
|---|---|
| exigence | an `Exigence` of the cahier des charges (`kb/cdc/`) |
| ticket | a `Ticket` of the backlog (`kb/tickets/`) |
| sprint | a `Sprint` (`kb/sprints/`) and its branch `sprint/<slug>` |
| plan de test | the `Test Plan` `kb/test/<ticket>-technique.md` |
| recette | the business acceptance test by a persona (`hosa-key-user`) |
| KB | the knowledge base `.hosa/kb/` |
| worktree | the sprint's working folder `.worktrees/sprint/<slug>` |
| environnement | a Docker Compose project (`docker_project`) |
| base (branche) | the branch the sprint merges into |
| base de données | the database — never "la base" alone |

## 3. Questions — always numbered

Every question to the user, and every `## Open Questions` item an agent returns, follows this format:

```
**Q1 — <la question, une phrase>** (bloquante)
  a) <option> — <conséquence en une ligne> (recommandé)
  b) <option> — <conséquence en une ligne>
  c) Autre : précise.
```

- **Number them Q1, Q2, Q3…** in the order they must be answered. Restart at Q1 in each message.
- **Offer lettered options** when the answer is a choice, and mark the recommended one, with its reason in the consequence line. A question with a free answer says what form the answer takes ("un nombre de tickets", "un chemin").
- **Mark blocking questions** "(bloquante)": the work stops until it's answered. Non-blocking questions say what you do by default if there's no answer.
- **One question = one decision.** Never two questions in one item.
- The user can answer in one line: **"Q1 a, Q2 b, Q3 : 5"**. Accept that form, and partial answers: re-ask only what's missing, with its original number.
- **Relaying an agent's questions:** the skill renumbers them into its own Q1…Qn for the user, keeps the mapping, and passes each answer back to the right agent with the agent's original number.

## 4. Agent reports

An agent's report keeps its own `## Output Format` sections, and applies everything above to their content. In addition:
- It opens with **`## En bref`**: one sentence, the result (done / blocked on what / failed on what).
- `## Open Questions` uses the Q-numbered format of section 3, or "None".
- Sections with nothing to say read "None" — never omitted, never padded.

## 5. Tone

Direct, calm, polite, tutoiement. No filler opener ("Super question", "Absolument"), no rhetorical question, no exclamation mark. A problem is stated plainly in the first lines, never softened or buried.
