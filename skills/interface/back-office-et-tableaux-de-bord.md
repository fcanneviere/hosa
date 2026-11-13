# Back office and dashboards

How `hosa-ux-designer` designs the screens of the people who run the application. Read it for `round: directions`, `round: page`, 3a, 3b and Review — not for `round: styles`. `interface_check` enforces the two tables at the end; the rest is the method behind them.

## The sources — never yours to invent

- **What the back office manages:** each object of `kb/cdc/modele-metier.md` (`## <Objet>`), its life cycle (the actions that move it) and its `### Droits` table (who may create, read, change, delete it). Read it with `kb_query.py .hosa/kb --type "Modèle Métier" --sections "<Objet>"` per object, not the whole file at once.
- **What a dashboard shows:** the indicators `INn` under `## Indicateurs` of the `stable` exigences (`kb_query.py .hosa/kb --type Exigence --where status=stable --sections Indicateurs`). Each one has its calculation, source, period, target or threshold, and the action the role takes when it drifts.
- An object with no rights decided, or a dashboard asked for with no indicator defined → Open Question proposing `fondamentaux`: the indicators are the user's business decisions, never a guess.

## Back office: one pattern per object, the same everywhere

1. **List** — the object's screen of entry: a dense table, the columns the role decides on, search, filters on its states, sort, pagination, a count of results. Bulk actions when the role treats many at once (validate, assign, archive). Export when `fondamentaux` kept it. Saved filters for a daily queue.
2. **Record** — one screen per object: its fields grouped as the role reads them, its state and the actions the life cycle allows from that state (only those), the related objects as links.
3. **History** — on the record: who changed what, when, before and after (`Historique des modifications`), and the object's audit events. A tab or a section of the record is enough: name the record screen in the table.
4. **Create and edit** — a form per object, the fields the `### Droits` table lets this role change; a deletion is an archive when the history must stay, with a confirmation that names the record.
5. **Queues** — a validation or moderation step of the life cycle is its own filtered list (« À valider »), its count in the menu, oldest first, with the action and the reason on each row.
6. **Reference data and settings** — the closed lists and the parameters the CDC makes editable: one screen each, grouped under a « Paramètres » entry, never mixed with the work.

The menu follows the work, not the database: the queues and the objects the role touches daily first, reference data and settings last. A role sees only the entries its rights allow. The back office opens on the role's work (queue or dashboard), never on a welcome page.

## Dashboards: a question, a number, a way down

1. **One dashboard per role that steers** — its question first (« Est-ce que la semaine est remplie ? »). Its indicators are the ones its exigence lists, at most 4–6 at first glance.
2. **Each indicator tile:** the name, the value with its unit, the comparison that gives it meaning (period before, target, threshold) and the period it covers. A threshold crossed shows in words and colour, never colour alone.
3. **Down to the records:** each tile leads to the list filtered on the records behind the number (« 4 réservations à payer » → the list of those 4). That screen is the indicator's `Détail`.
4. **The right chart, or none:** a number alone for a level, a line for a trend over time, bars for a comparison between categories, a table for exact values. No pie with more than 3 parts, no gauge, no 3D, no decorative chart. Each chart has its values available as text (a table or a label) for screen readers.
5. **Freshness and states:** the data's date (« mis à jour à 9 h 12 »), a loading state, an empty state that says why (« aucune réservation cette semaine ») and an error state with a retry.
6. **Below the indicators, the work:** what to handle now (the queue, the next action). A dashboard that only shows is half a screen.

In `round: styles`, a project with a dashboard gets one card with `ecran: "tableau-de-bord"` and `contenu.indicateurs`: the real indicators' names, plausible values and their series.

## Scaffold (3b): shared components first

Build once, in the shared component library, and use everywhere: the data table (search, filters, sort, pagination, selection, bulk action bar, export), the record view with its history panel, the form with field errors, the confirmation dialog, the indicator tile (value, comparison, link to its detail, its states). Each back-office list and record is these components with the object's columns and fields — never a hand-made table per screen. An indicator not computed yet shows its tile with a marked placeholder value and its detail link working.

## The two tables of `kb/interface/navigation.md` (3a)

```markdown
## Gestion back office
| Objet | Liste | Fiche | Historique | Actions |
|---|---|---|---|---|
| Réservation | Réservations | Réservation | Réservation | créer, annuler, marquer payée, exporter |
| Tarif | Non applicable : liste fixe de 3 tarifs, dans Paramètres | Paramètres | Non applicable : pas d'historique demandé | modifier |

## Tableaux de bord
| Indicateur | Exigence | Écran | Détail |
|---|---|---|---|
| IN1 Places vendues | [Pilotage de l'atelier](../cdc/pilotage-atelier.md) | Tableau de bord | Réservations |
```

- `Objet`: the exact `## <Objet>` heading of the business model, one row each.
- `Liste`, `Fiche`: the name of a back-office screen of `## Écrans`; `Historique`: a screen (often the record); or `Non applicable : <raison>`.
- `Indicateur`: its `INn`; `Exigence`: the link to the exigence that defines it; `Écran`: the screen of `## Écrans` that shows it; `Détail`: the screen (or route) of the records behind it, or `Non applicable : <raison>` for an indicator with no records (a rate from an outside source).

## Review: what the best tools do

- The back office opens on work; a list shows enough rows to decide (dense, aligned numbers, tabular figures); filters and actions are where the eye starts; nothing is reached in more than two clicks from the menu.
- A dashboard answers its question at a glance: few tiles, each with a comparison and a way down; no chart without a decision behind it; no number without its period.
- Penalise: a dashboard of vanity charts, a tile without comparison or detail, a list without filters or counts, a record whose actions don't follow its state, a back office that copies the front office's layout.
