"""CLI demo for PawPal+: builds an owner with two pets and prints today's schedule."""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def show(title: str, tasks: list[Task]) -> None:
    """Print a short list of tasks under a heading."""
    print(f"\n{title}")
    for t in tasks:
        status = "✓" if t.completed else " "
        print(f"  [{status}] {t.time or 'flex '} — {t.pet_name}: {t.title} ({t.priority})")


def main() -> None:
    owner = Owner("Jordan", day_start="07:00", day_end="10:00")
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added out of order on purpose, to show sorting.
    mochi.add_task(Task("Brush coat", 15, "medium"))
    luna.add_task(Task("Breakfast", 10, "high", time="07:30"))
    mochi.add_task(Task("Morning walk", 30, "high", time="07:00"))
    luna.add_task(Task("Litter box", 10, "medium", time="09:00"))
    mochi.add_task(Task("Breakfast", 10, "high", time="07:30"))  # same time as Luna -> conflict
    mochi.add_task(Task("Heartworm pill", 5, "high", frequency="weekly", weekday=date.today().weekday()))
    mochi.add_task(Task("Puzzle toy", 20, "low"))
    luna.add_task(Task("Play session", 120, "low"))  # too long to fit -> skipped

    scheduler = Scheduler(owner)

    show("All tasks, sorted by time:", scheduler.sort_by_time(owner.get_all_tasks()))
    show("Only Luna's tasks:", scheduler.filter_tasks(pet_name="Luna"))

    print()
    print(scheduler.build_plan().explain())

    next_walk = mochi.mark_task_complete("Morning walk")
    print(f"\nMarked Mochi's 'Morning walk' complete → next one due {next_walk.due_date}")
    show("Completed tasks:", scheduler.filter_tasks(completed=True))


if __name__ == "__main__":
    main()