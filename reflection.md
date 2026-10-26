# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

Three core actions a user should be able to do:

1. Add their pets and the hours they're free today.
2. Add care tasks for each pet (walks, feeding, meds) with how long they take, how important they are, and optionally a set time.
3. See today's schedule, in order, with a note on why each task is where it is.

My UML has four core classes. `Owner` holds the owner's name, the hours they're free (`day_start` to `day_end`), and their pets. `Pet` holds a name, a species, and that pet's list of tasks. `Task` is one care item: a title, a duration, a priority (high, medium or low), an optional set time, and how often it repeats. `Scheduler` takes an Owner and turns all the pets' tasks into a plan for one day. Each class owns its own data: a Task knows whether it's due on a given day, a Pet manages its own tasks, and only the Scheduler decides what goes where.

**b. Design changes**

I added two classes I didn't plan at first: `DailyPlan` and `ScheduledItem`. My first idea was for `build_plan()` to return a plain list of tasks, but that list couldn't say *when* each task happens, *why* it was placed there, or what got skipped. `ScheduledItem` pairs a task with a start time and a reason, and `DailyPlan` collects the scheduled items, the skipped tasks, and the conflict warnings. This made it easy for the Streamlit app to show the "Why" column and the skipped and warning messages without any extra logic in `app.py`.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler looks at four things:

1. **Time available:** nothing can be scheduled outside the owner's start and end time.
2. **Priority:** high-priority tasks get placed first.
3. **Set time:** a task with a set time (like breakfast at 7:30) keeps that slot if it's free.
4. **Recurrence:** only tasks due that day are included (daily, weekly on the right weekday, or a one-off on its date).

I ranked priority highest because for pet care, missing meds or feeding is worse than missing a puzzle-toy session. Set time comes second because it's what makes the plan realistic. Duration is only a tiebreaker: shorter tasks go first so more tasks fit.

**b. Tradeoffs**

The scheduler is greedy. It places tasks one at a time in priority order and never goes back to rearrange them. That means it doesn't always fit the *most* tasks possible. For example, a long low-priority task might get skipped when a smarter rearrangement could have squeezed it in. I think this is reasonable here: the plan is easy to explain ("high priority went first"), it's fast, and when time runs out it's the low-priority tasks that get dropped, which is what a pet owner would want anyway.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude as an agent. It read the starter repo and the assignment brief, then drafted the UML, the class skeletons, the full logic, `main.py`, the tests, and the Streamlit wiring. It ran the tests and the demo script as it went. I then added each file to my own repo in VS Code, ran it on my machine, and made the commits myself.

1. **Most effective features:** agent mode, because it could edit several files and then run `pytest` and `python main.py` to check its own work. The most useful prompts were specific. Giving it the full assignment brief worked much better than a short request, because it then caught requirements it had missed (like needing a separate `main.py` and a `get_all_tasks()` method).
2. **Sessions:** I mostly worked in one long conversation. Next time I'd use separate chats for design, implementation, and testing, because the one long chat made it harder to keep track of which version of a file was current.
3. **Being the lead architect:** the UML and the assignment brief were my contract. I checked AI output against them, asking whether the logic lived in the right class and whether the Scheduler read from `Owner.get_all_tasks()` instead of reaching into one pet.

**b. Judgment and verification**

The first version didn't fully match the assignment. The demo lived inside `pawpal_system.py`, the Owner method was called `all_tasks()`, and `sort_by_time()` sorted scheduled items instead of tasks. Once I gave it the full brief, I had it move the demo into `main.py`, rename the method to `get_all_tasks()`, and make `sort_by_time()` work on tasks. While re-testing, it also caught a real bug: after a daily task was marked complete, its next copy showed up on *today's* plan too. `is_due_on()` was fixed to check the due date, and a test was added for it. I verified everything by running `python -m pytest` (18 passing) and `python main.py` on my own Mac and reading the output: the conflict warning, Luna's breakfast moved to 07:40, and the skipped play session.

---

## 4. Testing and Verification

**a. What you tested**

There are 18 tests in `tests/test_pawpal.py`. They cover:

1. `mark_complete()` changes a task's status, and adding a task increases a pet's task count.
2. `sort_by_time()` returns tasks in chronological order.
3. High-priority tasks are scheduled before low-priority ones.
4. The final plan comes out in time order.
5. Tasks that don't fit in the day are skipped.
6. Duplicate or overlapping set times produce a warning, and the lower-priority task is moved so nothing overlaps.
7. A set time outside the owner's hours is moved inside them.
8. Weekly tasks only show up on their weekday.
9. Completing a daily task creates tomorrow's copy, completing a weekly task creates next week's, and a one-off task just ends.
10. Filtering by pet and by completion status.
11. Bad input (zero duration, unknown priority, end time before start time) raises an error.

These matter because they're the promises the app makes to the user: important things happen first, nothing double-books, and nothing gets planned when you aren't available.

**b. Confidence**

I'm fairly confident (4 out of 5). All 18 tests pass, and the core rules are covered. Next I'd test:

1. Tasks that run past midnight.
2. Two tasks with the same title on the same pet.
3. A day packed with only set-time tasks, so every one has to move.
4. Weekly tasks completed late, to check the next due date is still correct.

---

## 5. Reflection

**a. What went well**

I'm happiest with the explanations. Every scheduled task says why it's there ("at its set time", "earliest open slot", or "moved from 07:30"), and skipped tasks say why they were skipped. The plan is something a user can trust, not just a list.

**b. What you would improve**

I'd replace the greedy approach with one that tries to fit more tasks, and let owners block out times during the day (like work from 9 to 5) instead of only a single start and end time. I'd also save pets and tasks to a file so they survive closing the app.

**c. Key takeaway**

AI can produce working code fast, but it only creates what you ask for. The first version worked but didn't match the assignment until I gave it the full brief and checked the output against it. Designing the classes first and verifying each piece myself (running the tests and the demo on my own machine) is what kept the project correct.