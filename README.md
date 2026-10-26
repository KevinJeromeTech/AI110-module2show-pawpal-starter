# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🛠️ What I Built

PawPal+ keeps its logic in `pawpal_system.py`, separate from the Streamlit UI in `app.py`:

1. **`Task`** (dataclass): one care activity, with a title, duration, priority, optional set time (`"HH:MM"`), frequency (`once`, `daily` or `weekly`), due date, and completion status.
2. **`Pet`** (dataclass): a pet's name, species, and its list of tasks. It can add or remove tasks and mark them complete.
3. **`Owner`** (dataclass): the owner's free hours for the day and their pets. `get_all_tasks()` returns every pet's tasks in one list.
4. **`Scheduler`**: reads all tasks through `Owner.get_all_tasks()`. It sorts and filters them, detects conflicts, and builds a `DailyPlan`.
5. **`DailyPlan` / `ScheduledItem`**: the scheduler's output. Each item records the task, its start time, and *why* it was placed there. The plan also lists skipped tasks and conflict warnings.

`main.py` is a CLI demo that exercises all of this in the terminal. `app.py` keeps the `Owner` in `st.session_state`, so pets and tasks survive Streamlit reruns.

## ✨ Features

1. **Sorting by time:** `Scheduler.sort_by_time()` orders tasks by their `"HH:MM"` time, with flexible tasks last.
2. **Priority scheduling:** `Scheduler.sort_by_priority()` places high before medium before low, then by time, then shortest first (Challenge 3).
3. **Filtering:** `Scheduler.filter_tasks()` filters by pet, completion status, and/or priority.
4. **Fits your day:** tasks are only placed between the owner's start and end time. Anything that doesn't fit is skipped with a reason.
5. **Conflict warnings:** `Scheduler.find_conflicts()` flags tasks set at the same or overlapping times, across pets. The higher-priority task keeps its slot and the other is moved, so the plan never double-books.
6. **Next available slot:** `Scheduler.next_available_slot()` finds the earliest open gap that fits a task (Challenge 1).
7. **Recurring tasks:** completing a `daily` or `weekly` task creates the next one with `timedelta` (+1 or +7 days). One-off tasks just end.
8. **Explained plans:** every scheduled task shows why it's there ("at its set time", "earliest open slot", "moved from 07:30").

## 🖥️ Sample Output

Output of `python main.py` (owner free 07:00–10:00, two pets, tasks added out of order):

```

All tasks, sorted by time:
  [ ] 07:00 — Mochi: Morning walk (high)
  [ ] 07:30 — Mochi: Breakfast (high)
  [ ] 07:30 — Luna: Breakfast (high)
  [ ] 09:00 — Luna: Litter box (medium)
  [ ] flex  — Mochi: Brush coat (medium)
  [ ] flex  — Mochi: Heartworm pill (high)
  [ ] flex  — Mochi: Puzzle toy (low)
  [ ] flex  — Luna: Play session (low)

Only Luna's tasks:
  [ ] 07:30 — Luna: Breakfast (high)
  [ ] 09:00 — Luna: Litter box (medium)
  [ ] flex  — Luna: Play session (low)

Today's Schedule — 2026-10-26 (100 min planned)
  07:00 — Mochi: Morning walk (30 min) [priority: high] — high priority, at its set time
  07:30 — Mochi: Breakfast (10 min) [priority: high] — high priority, at its set time
  07:40 — Luna: Breakfast (10 min) [priority: high] — high priority; moved from 07:30 (slot taken or outside your hours)
  07:50 — Mochi: Heartworm pill (5 min) [priority: high] — high priority, earliest open slot
  07:55 — Mochi: Brush coat (15 min) [priority: medium] — medium priority, earliest open slot
  08:10 — Mochi: Puzzle toy (20 min) [priority: low] — low priority, earliest open slot
  09:00 — Luna: Litter box (10 min) [priority: medium] — medium priority, at its set time
  SKIPPED — Luna: Play session: not enough free time left in the day
  ⚠️  WARNING — Mochi's 'Breakfast' (07:30) at the same time as Luna's 'Breakfast' (07:30); the lower-priority one will be moved.

Marked Mochi's 'Morning walk' complete → next one due 2026-10-27

Completed tasks:
  [✓] 07:00 — Mochi: Morning walk (high)
```

## 🧪 Testing PawPal+

```bash
python -m pytest
```

The suite in `tests/test_pawpal.py` covers:

1. **Basics:** `mark_complete()` changes status, adding a task increases a pet's task count, and `get_all_tasks()` spans every pet.
2. **Sorting:** `sort_by_time()` returns chronological order, high priority is scheduled before low, and the final plan is in time order.
3. **Filtering:** by pet and by completion status. Tasks that don't fit are skipped, and a pet with no tasks gives an empty plan.
4. **Conflicts:** duplicate times are flagged, the higher-priority task keeps its slot, no scheduled items overlap, and set times outside the owner's hours are moved in.
5. **Recurrence:** daily tasks repeat the next day and weekly tasks 7 days later. One-off tasks don't repeat, weekly tasks only appear on their weekday, and a new occurrence isn't scheduled on the same day.
6. **Validation:** bad durations, priorities, and owner hours raise errors.

```
$ python -m pytest
collected 18 items

tests/test_pawpal.py ..................                                  [100%]

============================== 18 passed in 0.03s ==============================
```

**Confidence level:** ⭐⭐⭐⭐ (4/5). All core behaviors are tested and passing. Not yet covered: tasks that cross midnight, and duplicate task titles on the same pet.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority()` | By `"HH:MM"` time (flexible last); the plan orders by priority, then time, then shortest first. |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.tasks_due()` | By pet name, completion status, or priority. Only open tasks due that day are planned; tasks that don't fit are skipped. |
| Conflict handling | `Scheduler.find_conflicts()`, `Scheduler.next_available_slot()`, `Scheduler.is_free()` | Warns on same or overlapping times across pets; the lower-priority task moves to the next free gap. |
| Recurring tasks | `Task.mark_complete()`, `Pet.mark_task_complete()`, `Task.is_due_on()` | `daily` gives +1 day and `weekly` +7 days via `timedelta`; `once` doesn't repeat. |

## 📸 Demo Walkthrough

**Main UI features:** set your free hours, add pets, add tasks (duration, priority, repeat, optional set time), view tasks sorted and filtered by pet, mark tasks complete or remove them, and generate a plan for any date.

**Example workflow:**

1. Run `streamlit run app.py`.
2. **Owner:** enter your name and your free hours (e.g. 07:00–10:00). The app shows how many minutes that gives you.
3. **Pets:** add Mochi (dog) and Luna (cat).
4. **Tasks:** give Mochi a "Morning walk" at 07:00 (30 min, high) and "Breakfast" at 07:30 (high). Give Luna "Breakfast" at 07:30 (high) and a 120-minute "Play session" (low). The task table is sorted by priority and can be filtered by pet.
5. **Generate schedule:** a timed table appears with a "Why" column for every task.
6. **Scheduler behaviors shown:**
   1. **Sorting:** high-priority tasks are placed first, and the plan reads top to bottom in time order.
   2. **Conflict warning:** a yellow warning says both breakfasts are at 07:30. Luna's breakfast moves to 07:40.
   3. **Skipping:** a red message says the Play session didn't fit in the day.
7. **Mark complete:** complete Mochi's walk, and the next one is created for tomorrow automatically.

**CLI output** (`python main.py`):

```

All tasks, sorted by time:
  [ ] 07:00 — Mochi: Morning walk (high)
  [ ] 07:30 — Mochi: Breakfast (high)
  [ ] 07:30 — Luna: Breakfast (high)
  [ ] 09:00 — Luna: Litter box (medium)
  [ ] flex  — Mochi: Brush coat (medium)
  [ ] flex  — Mochi: Heartworm pill (high)
  [ ] flex  — Mochi: Puzzle toy (low)
  [ ] flex  — Luna: Play session (low)

Only Luna's tasks:
  [ ] 07:30 — Luna: Breakfast (high)
  [ ] 09:00 — Luna: Litter box (medium)
  [ ] flex  — Luna: Play session (low)

Today's Schedule — 2026-10-26 (100 min planned)
  07:00 — Mochi: Morning walk (30 min) [priority: high] — high priority, at its set time
  07:30 — Mochi: Breakfast (10 min) [priority: high] — high priority, at its set time
  07:40 — Luna: Breakfast (10 min) [priority: high] — high priority; moved from 07:30 (slot taken or outside your hours)
  07:50 — Mochi: Heartworm pill (5 min) [priority: high] — high priority, earliest open slot
  07:55 — Mochi: Brush coat (15 min) [priority: medium] — medium priority, earliest open slot
  08:10 — Mochi: Puzzle toy (20 min) [priority: low] — low priority, earliest open slot
  09:00 — Luna: Litter box (10 min) [priority: medium] — medium priority, at its set time
  SKIPPED — Luna: Play session: not enough free time left in the day
  ⚠️  WARNING — Mochi's 'Breakfast' (07:30) at the same time as Luna's 'Breakfast' (07:30); the lower-priority one will be moved.

Marked Mochi's 'Morning walk' complete → next one due 2026-10-27

Completed tasks:
  [✓] 07:00 — Mochi: Morning walk (high)
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->