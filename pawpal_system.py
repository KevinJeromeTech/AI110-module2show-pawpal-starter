"""PawPal+ logic layer: owners, pets, care tasks, and a daily scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}
VALID_FREQUENCIES = ("once", "daily", "weekly")
END_OF_DAY = 24 * 60


def to_minutes(hhmm: str) -> int:
    """Convert an 'HH:MM' string to minutes after midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def to_hhmm(total: int) -> str:
    """Convert minutes after midnight to an 'HH:MM' string."""
    return f"{total // 60:02d}:{total % 60:02d}"


@dataclass
class Task:
    """A single pet care activity."""

    title: str
    duration_minutes: int
    priority: str = "medium"
    time: Optional[str] = None            # "HH:MM" if the task should happen at a set time
    frequency: str = "daily"              # once | daily | weekly
    weekday: Optional[int] = None         # 0=Mon..6=Sun, used when frequency == "weekly"
    pet_name: Optional[str] = None
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Validate the task's fields."""
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be one of {list(PRIORITY_RANK)}")
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}")
        if self.time is not None:
            to_minutes(self.time)  # raises if the format is wrong

    @property
    def priority_rank(self) -> int:
        """Return 3 for high, 2 for medium, 1 for low."""
        return PRIORITY_RANK[self.priority]

    def is_due_on(self, day: date) -> bool:
        """Return True if this task belongs on the plan for `day`."""
        if self.completed:
            return False
        if self.frequency == "daily":
            return self.due_date <= day
        if self.frequency == "weekly":
            target = self.weekday if self.weekday is not None else self.due_date.weekday()
            return self.due_date <= day and day.weekday() == target
        return self.due_date == day  # once

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task done and return the next occurrence if it repeats."""
        self.completed = True
        if self.frequency == "once":
            return None
        step = timedelta(days=1 if self.frequency == "daily" else 7)
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            time=self.time,
            frequency=self.frequency,
            weekday=self.weekday,
            pet_name=self.pet_name,
            due_date=self.due_date + step,
        )


@dataclass
class Pet:
    """A pet and its list of care tasks."""

    name: str
    species: str = "dog"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """Remove all tasks with this title; return True if any were removed."""
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.title != title]
        return len(self.tasks) < before

    def mark_task_complete(self, title: str) -> Optional[Task]:
        """Complete the first open task with this title and queue its next occurrence."""
        for task in self.tasks:
            if task.title == title and not task.completed:
                next_task = task.mark_complete()
                if next_task:
                    self.tasks.append(next_task)
                return next_task
        raise KeyError(f"No open task titled {title!r} for {self.name}")


@dataclass
class Owner:
    """A pet owner, their free hours for the day, and their pets."""

    name: str
    day_start: str = "08:00"
    day_end: str = "20:00"
    pets: list[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate that the day ends after it starts."""
        if to_minutes(self.day_end) <= to_minutes(self.day_start):
            raise ValueError("day_end must be after day_start")

    @property
    def available_minutes(self) -> int:
        """Return how many minutes the owner has free today."""
        return to_minutes(self.day_end) - to_minutes(self.day_start)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Return the pet with this name, or None."""
        return next((p for p in self.pets if p.name == name), None)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [t for p in self.pets for t in p.tasks]


@dataclass
class ScheduledItem:
    """A task placed at a start time, with the reason it landed there."""

    task: Task
    start: int  # minutes after midnight
    reason: str

    @property
    def end(self) -> int:
        """Return the end time in minutes after midnight."""
        return self.start + self.task.duration_minutes

    @property
    def start_str(self) -> str:
        """Return the start time as 'HH:MM'."""
        return to_hhmm(self.start)

    @property
    def end_str(self) -> str:
        """Return the end time as 'HH:MM'."""
        return to_hhmm(self.end)


@dataclass
class DailyPlan:
    """The scheduler's output: scheduled items, skipped tasks, and warnings."""

    day: date
    items: list[ScheduledItem] = field(default_factory=list)
    skipped: list[tuple[Task, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def total_minutes(self) -> int:
        """Return the total minutes of scheduled tasks."""
        return sum(i.task.duration_minutes for i in self.items)

    def to_rows(self) -> list[dict]:
        """Return the plan as a list of dicts for display in a table."""
        return [
            {
                "Time": f"{i.start_str}–{i.end_str}",
                "Pet": i.task.pet_name or "",
                "Task": i.task.title,
                "Minutes": i.task.duration_minutes,
                "Priority": i.task.priority,
                "Why": i.reason,
            }
            for i in self.items
        ]

    def explain(self) -> str:
        """Return a readable, multi-line text version of the plan."""
        lines = [f"Today's Schedule — {self.day.isoformat()} ({self.total_minutes} min planned)"]
        for i in self.items:
            pet = f"{i.task.pet_name}: " if i.task.pet_name else ""
            lines.append(
                f"  {i.start_str} — {pet}{i.task.title} ({i.task.duration_minutes} min)"
                f" [priority: {i.task.priority}] — {i.reason}"
            )
        for task, why in self.skipped:
            lines.append(f"  SKIPPED — {task.pet_name}: {task.title}: {why}")
        for w in self.warnings:
            lines.append(f"  ⚠️  WARNING — {w}")
        return "\n".join(lines)


class Scheduler:
    """The 'brain': reads every pet's tasks from the Owner and builds a daily plan.

    Strategy (greedy):
      1. Keep only open tasks that are due today.
      2. Sort by priority (high first), then by set time, then shortest first.
      3. A task with a set time keeps it if the slot is free and inside the owner's day;
         otherwise it moves to the next open slot.
      4. Flexible tasks fill the earliest open slot.
      5. Anything that doesn't fit is skipped, with a reason.
    """

    def __init__(self, owner: Owner):
        """Create a scheduler for this owner."""
        self.owner = owner

    # --- sorting -------------------------------------------------------------
    @staticmethod
    def sort_by_time(tasks: list[Task]) -> list[Task]:
        """Return tasks in chronological order by 'HH:MM' time; flexible tasks go last."""
        return sorted(tasks, key=lambda t: to_minutes(t.time) if t.time else END_OF_DAY)

    @staticmethod
    def sort_by_priority(tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by priority (high first), then time, then shortest first."""
        return sorted(
            tasks,
            key=lambda t: (
                -t.priority_rank,
                to_minutes(t.time) if t.time else END_OF_DAY,
                t.duration_minutes,
            ),
        )

    # --- filtering -----------------------------------------------------------
    def tasks_due(self, day: date) -> list[Task]:
        """Return all open tasks across the owner's pets that are due on `day`."""
        return [t for t in self.owner.get_all_tasks() if t.is_due_on(day)]

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        priority: Optional[str] = None,
    ) -> list[Task]:
        """Return the owner's tasks matching a pet name, completion status, and/or priority."""
        return [
            t
            for t in self.owner.get_all_tasks()
            if (pet_name is None or t.pet_name == pet_name)
            and (completed is None or t.completed == completed)
            and (priority is None or t.priority == priority)
        ]

    # --- conflicts -----------------------------------------------------------
    @staticmethod
    def find_conflicts(tasks: list[Task]) -> list[str]:
        """Return a warning for each pair of set-time tasks whose time windows overlap."""
        fixed = [t for t in Scheduler.sort_by_time(tasks) if t.time]
        warnings = []
        for i, a in enumerate(fixed):
            a_start = to_minutes(a.time)
            a_end = a_start + a.duration_minutes
            for b in fixed[i + 1:]:
                if to_minutes(b.time) >= a_end:
                    break
                same = "at the same time as" if b.time == a.time else "overlaps"
                warnings.append(
                    f"{a.pet_name}'s '{a.title}' ({a.time}) {same} "
                    f"{b.pet_name}'s '{b.title}' ({b.time}); the lower-priority one will be moved."
                )
        return warnings

    # --- slot finding --------------------------------------------------------
    def next_available_slot(
        self, busy: list[tuple[int, int]], duration: int, earliest: Optional[int] = None
    ) -> Optional[int]:
        """Return the earliest start (minutes) at or after `earliest` that fits `duration`, or None."""
        day_end = to_minutes(self.owner.day_end)
        cursor = to_minutes(self.owner.day_start) if earliest is None else earliest
        for start, end in sorted(busy):
            if cursor + duration <= start:
                break
            cursor = max(cursor, end)
        return cursor if cursor + duration <= day_end else None

    @staticmethod
    def is_free(busy: list[tuple[int, int]], start: int, end: int) -> bool:
        """Return True if [start, end) doesn't overlap anything in `busy`."""
        return all(end <= s or start >= e for s, e in busy)

    # --- planning ------------------------------------------------------------
    def build_plan(self, day: Optional[date] = None) -> DailyPlan:
        """Build the daily plan for `day` (defaults to today)."""
        day = day or date.today()
        day_start = to_minutes(self.owner.day_start)
        day_end = to_minutes(self.owner.day_end)

        due = self.tasks_due(day)
        plan = DailyPlan(day=day, warnings=self.find_conflicts(due))
        busy: list[tuple[int, int]] = []

        for task in self.sort_by_priority(due):
            dur = task.duration_minutes
            start, reason = None, ""
            if task.time:
                want = to_minutes(task.time)
                if day_start <= want and want + dur <= day_end and self.is_free(busy, want, want + dur):
                    start, reason = want, f"{task.priority} priority, at its set time"
                else:
                    start = self.next_available_slot(busy, dur, max(day_start, min(want, day_end)))
                    if start is None:
                        start = self.next_available_slot(busy, dur)
                    reason = f"{task.priority} priority; moved from {task.time} (slot taken or outside your hours)"
            else:
                start = self.next_available_slot(busy, dur)
                reason = f"{task.priority} priority, earliest open slot"

            if start is None:
                plan.skipped.append((task, "not enough free time left in the day"))
            else:
                busy.append((start, start + dur))
                plan.items.append(ScheduledItem(task, start, reason))

        plan.items.sort(key=lambda i: i.start)
        return plan