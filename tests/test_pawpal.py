from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

MONDAY = date(2030, 1, 7)  # a future Monday, so tasks created "today" are already due


def make_owner(start="08:00", end="12:00"):
    owner = Owner("Jordan", day_start=start, day_end=end)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    return owner, pet


# --- Basics ------------------------------------------------------------------
def test_mark_complete_changes_status():
    task = Task("Walk", 20)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    _, pet = make_owner()
    assert len(pet.tasks) == 0
    pet.add_task(Task("Walk", 20))
    assert len(pet.tasks) == 1
    assert pet.tasks[0].pet_name == "Mochi"


def test_owner_get_all_tasks_spans_pets():
    owner, mochi = make_owner()
    luna = Pet("Luna", "cat")
    owner.add_pet(luna)
    mochi.add_task(Task("Walk", 20))
    luna.add_task(Task("Litter", 10))
    assert {t.pet_name for t in owner.get_all_tasks()} == {"Mochi", "Luna"}


def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):
        Task("Walk", 0)
    with pytest.raises(ValueError):
        Task("Walk", 10, priority="urgent")
    with pytest.raises(ValueError):
        Owner("Jordan", day_start="18:00", day_end="08:00")


# --- Sorting -----------------------------------------------------------------
def test_sort_by_time_is_chronological():
    tasks = [
        Task("Dinner", 10, time="18:00"),
        Task("Play", 10),  # flexible, goes last
        Task("Breakfast", 10, time="07:30"),
        Task("Lunch", 10, time="12:00"),
    ]
    assert [t.title for t in Scheduler.sort_by_time(tasks)] == ["Breakfast", "Lunch", "Dinner", "Play"]


def test_high_priority_scheduled_before_low():
    owner, pet = make_owner()
    pet.add_task(Task("Play", 30, "low"))
    pet.add_task(Task("Meds", 5, "high"))
    plan = Scheduler(owner).build_plan(MONDAY)
    assert [i.task.title for i in plan.items] == ["Meds", "Play"]


def test_plan_is_in_chronological_order():
    owner, pet = make_owner()
    pet.add_task(Task("Dinner", 10, "high", time="11:00"))
    pet.add_task(Task("Walk", 30, "low"))
    starts = [i.start for i in Scheduler(owner).build_plan(MONDAY).items]
    assert starts == sorted(starts)


# --- Filtering ---------------------------------------------------------------
def test_filter_by_pet_and_status():
    owner, mochi = make_owner()
    luna = Pet("Luna", "cat")
    owner.add_pet(luna)
    mochi.add_task(Task("Walk", 20, "high"))
    luna.add_task(Task("Litter", 10, "low", frequency="once"))
    luna.mark_task_complete("Litter")
    s = Scheduler(owner)
    assert [t.title for t in s.filter_tasks(pet_name="Luna")] == ["Litter"]
    assert [t.title for t in s.filter_tasks(completed=True)] == ["Litter"]
    assert [t.title for t in s.filter_tasks(completed=False)] == ["Walk"]


def test_tasks_that_do_not_fit_are_skipped():
    owner, pet = make_owner("08:00", "09:00")
    pet.add_task(Task("Walk", 45, "high"))
    pet.add_task(Task("Grooming", 30, "low"))
    plan = Scheduler(owner).build_plan(MONDAY)
    assert [i.task.title for i in plan.items] == ["Walk"]
    assert plan.skipped[0][0].title == "Grooming"


def test_pet_with_no_tasks_gives_empty_plan():
    owner, _ = make_owner()
    plan = Scheduler(owner).build_plan(MONDAY)
    assert plan.items == [] and plan.skipped == []


# --- Conflicts ---------------------------------------------------------------
def test_duplicate_times_are_flagged():
    owner, mochi = make_owner()
    luna = Pet("Luna", "cat")
    owner.add_pet(luna)
    mochi.add_task(Task("Breakfast", 10, "high", time="08:00"))
    luna.add_task(Task("Breakfast", 10, "medium", time="08:00"))
    plan = Scheduler(owner).build_plan(MONDAY)
    assert len(plan.warnings) == 1
    assert "same time" in plan.warnings[0]
    by_pet = {i.task.pet_name: i for i in plan.items}
    assert by_pet["Mochi"].start_str == "08:00"  # higher priority keeps its slot
    assert by_pet["Luna"].start >= by_pet["Mochi"].end


def test_no_scheduled_items_overlap():
    owner, pet = make_owner()
    pet.add_task(Task("Walk", 30, "high", time="08:00"))
    pet.add_task(Task("Feed", 10, "high", time="08:15"))
    pet.add_task(Task("Play", 20, "low"))
    items = Scheduler(owner).build_plan(MONDAY).items
    for a, b in zip(items, items[1:]):
        assert a.end <= b.start


def test_set_time_outside_hours_is_moved_in():
    owner, pet = make_owner("08:00", "12:00")
    pet.add_task(Task("Late walk", 20, "high", time="21:00"))
    plan = Scheduler(owner).build_plan(MONDAY)
    assert len(plan.items) == 1 and plan.items[0].end <= 12 * 60


# --- Recurrence --------------------------------------------------------------
def test_completing_daily_task_creates_next_day_task():
    _, pet = make_owner()
    pet.add_task(Task("Feed", 10, "high", due_date=MONDAY))
    nxt = pet.mark_task_complete("Feed")
    assert pet.tasks[0].completed
    assert nxt.due_date == MONDAY + timedelta(days=1)
    assert len(pet.tasks) == 2


def test_completing_weekly_task_creates_next_week_task():
    _, pet = make_owner()
    pet.add_task(Task("Bath", 30, frequency="weekly", weekday=MONDAY.weekday(), due_date=MONDAY))
    nxt = pet.mark_task_complete("Bath")
    assert nxt.due_date == MONDAY + timedelta(days=7)


def test_completing_one_off_task_creates_nothing():
    owner, pet = make_owner()
    pet.add_task(Task("Vet visit", 60, "high", frequency="once", due_date=MONDAY))
    assert pet.mark_task_complete("Vet visit") is None
    assert Scheduler(owner).build_plan(MONDAY).items == []


def test_weekly_task_only_on_its_weekday():
    owner, pet = make_owner()
    pet.add_task(Task("Bath", 30, frequency="weekly", weekday=MONDAY.weekday(), due_date=MONDAY))
    s = Scheduler(owner)
    assert len(s.build_plan(MONDAY).items) == 1
    assert len(s.build_plan(MONDAY + timedelta(days=1)).items) == 0


def test_next_occurrence_not_scheduled_today():
    owner, pet = make_owner()
    pet.add_task(Task("Feed", 10, "high", due_date=MONDAY))
    pet.mark_task_complete("Feed")
    s = Scheduler(owner)
    assert s.build_plan(MONDAY).items == []
    assert len(s.build_plan(MONDAY + timedelta(days=1)).items) == 1