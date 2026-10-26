from datetime import date, time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan your pets' care for the day — by priority, time available, and preferred times.")

# --- Session state: keep the Owner object alive across reruns -----------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", day_start="08:00", day_end="20:00")
owner: Owner = st.session_state.owner

# --- Owner -------------------------------------------------------------------
st.subheader("1. Owner")
c1, c2, c3 = st.columns(3)
with c1:
    owner_name = st.text_input("Owner name", value=owner.name)
with c2:
    start = st.time_input("Day starts", value=time.fromisoformat(owner.day_start))
with c3:
    end = st.time_input("Day ends", value=time.fromisoformat(owner.day_end))

if end <= start:
    st.error("Day end must be after day start.")
else:
    owner.name = owner_name
    owner.day_start = start.strftime("%H:%M")
    owner.day_end = end.strftime("%H:%M")
    st.caption(f"Available today: {owner.available_minutes} minutes")

# --- Pets --------------------------------------------------------------------
st.subheader("2. Pets")
with st.form("add_pet", clear_on_submit=True):
    p1, p2 = st.columns(2)
    pet_name = p1.text_input("Pet name", value="Mochi")
    species = p2.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.warning("Give your pet a name.")
        elif owner.get_pet(pet_name.strip()):
            st.warning(f"{pet_name} is already added.")
        else:
            owner.add_pet(Pet(pet_name.strip(), species))
            st.success(f"Added {pet_name}.")

if owner.pets:
    st.write(", ".join(f"**{p.name}** ({p.species})" for p in owner.pets))
else:
    st.info("Add a pet to get started.")

# --- Tasks -------------------------------------------------------------------
st.subheader("3. Tasks")
if owner.pets:
    with st.form("add_task", clear_on_submit=True):
        t1, t2, t3 = st.columns(3)
        task_pet = t1.selectbox("Pet", [p.name for p in owner.pets])
        title = t2.text_input("Task", value="Morning walk")
        duration = t3.number_input("Minutes", min_value=1, max_value=240, value=20)
        t4, t5, t6 = st.columns(3)
        priority = t4.selectbox("Priority", ["high", "medium", "low"])
        frequency = t5.selectbox("Repeats", ["daily", "weekly", "once"])
        fixed = t6.checkbox("Set a time?")
        pref = st.time_input("Preferred time (used if 'Set a time?' is checked)", value=time(8, 0))
        if st.form_submit_button("Add task"):
            owner.get_pet(task_pet).add_task(
                Task(
                    title=title.strip() or "Untitled",
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                    time=pref.strftime("%H:%M") if fixed else None,
                    weekday=date.today().weekday() if frequency == "weekly" else None,
                )
            )

    open_tasks = [t for t in owner.get_all_tasks() if not t.completed]
    if open_tasks:
        view_pet = st.selectbox("Show tasks for", ["All pets"] + [p.name for p in owner.pets])
        shown = Scheduler(owner).sort_by_priority(
            [t for t in open_tasks if view_pet == "All pets" or t.pet_name == view_pet]
        )
        st.table(
            [
                {
                    "Pet": t.pet_name,
                    "Task": t.title,
                    "Minutes": t.duration_minutes,
                    "Priority": t.priority,
                    "Time": t.time or "flexible",
                    "Repeats": t.frequency,
                    "Due": t.due_date.isoformat(),
                }
                for t in shown
            ]
        )

        d1, d2 = st.columns(2)
        with d1:
            labels = [f"{t.pet_name}: {t.title}" for t in open_tasks]
            pick = st.selectbox("Mark complete", labels)
            if st.button("Done ✓"):
                pname, ttitle = pick.split(": ", 1)
                nxt = owner.get_pet(pname).mark_task_complete(ttitle)
                st.success(
                    f"Completed. Next one due {nxt.due_date.isoformat()}." if nxt else "Completed."
                )
                st.rerun()
        with d2:
            rm = st.selectbox("Remove task", labels, key="rm")
            if st.button("Remove"):
                pname, ttitle = rm.split(": ", 1)
                owner.get_pet(pname).remove_task(ttitle)
                st.rerun()
    else:
        st.info("No open tasks yet.")

# --- Schedule ----------------------------------------------------------------
st.divider()
st.subheader("4. Today's plan")
plan_day = st.date_input("Plan for", value=date.today())

if st.button("Generate schedule", type="primary"):
    plan = Scheduler(owner).build_plan(plan_day)
    if not plan.items and not plan.skipped:
        st.info("Nothing due on this day.")
    else:
        st.success(
            f"Scheduled {len(plan.items)} task(s), {plan.total_minutes} of "
            f"{owner.available_minutes} available minutes."
        )
        for w in plan.warnings:
            st.warning(f"⚠️ Time conflict: {w}")
        if plan.items:
            st.table(plan.to_rows())
        for task, why in plan.skipped:
            st.error(f"Skipped **{task.title}** ({task.pet_name}, {task.duration_minutes} min): {why}")
        with st.expander("Why this plan?"):
            st.markdown(
                "Tasks are ordered by **priority** (high → low), then by **requested time**, "
                "then **shortest first**. Tasks with a set time keep it if it's free and inside your "
                "day; otherwise they move to the next open slot. Flexible tasks fill the earliest gap. "
                "Anything that won't fit is skipped and listed above."
            )
            st.code(plan.explain())