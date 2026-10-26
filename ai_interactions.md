# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

Build PawPal+ from the starter repo and the assignment brief: the UML, the class logic, a CLI demo, tests, and the Streamlit wiring. That included a third algorithmic capability (Challenge 1): a "next available slot" finder.

**What did the agent do?**

1. Read the starter `app.py`, `README.md`, and `reflection.md`.
2. Created `pawpal_system.py` with `Task`, `Pet`, `Owner`, `Scheduler`, `DailyPlan`, and `ScheduledItem`, including `Scheduler.next_available_slot()`, which finds the earliest gap in the day that fits a task's duration.
3. Created `main.py` (CLI demo) and `tests/test_pawpal.py`, then ran `python main.py` and `python -m pytest` to check the results.
4. Rewired `app.py` to keep the `Owner` in `st.session_state` and display the plan with `st.table`, `st.warning`, and `st.error`.
5. Wrote `diagrams/uml.mmd` and `diagrams/uml_final.mmd`, and filled in the README.

**What did you have to verify or fix manually?**

1. The first version didn't match the assignment's required names (`get_all_tasks`, `sort_by_time` on tasks, a separate `main.py`), so I had it updated.
2. A recurrence bug: the next copy of a completed daily task showed up on today's plan. It was fixed in `Task.is_due_on()` and covered by a new test.
3. I read through `main.py`'s output to confirm conflicts, skips, and moved tasks made sense.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->