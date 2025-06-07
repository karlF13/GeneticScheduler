# utils/display.py
from typing import List
from models.chromosome import Chromosome
from models.resources import Section, Subject, Professor, Room

def print_schedule(chromosome: Chromosome,
                   sections: List[Section],
                   subjects: List[Subject],
                   professors: List[Professor],
                   rooms: List[Room]) -> None:
    section_dict = {s.id: s for s in sections}
    subject_dict = {s.id: s for s in subjects}
    professor_dict = {p.id: p for p in professors}
    room_dict = {r.id: r for r in rooms}

    schedule = {}
    for gene in chromosome.genes:
        schedule.setdefault(gene.section_id, {}).setdefault(gene.day, []).append(gene)

    # Print conflicts summary
    conflicts = (chromosome._check_professor_conflicts() +
                 chromosome._check_room_conflicts() +
                 chromosome._check_section_conflicts())
    print(f"\n=== SCHEDULE SUMMARY ===")
    print(f"Total Conflicts: {conflicts}")
    print(f"Fitness Score: {chromosome.fitness:.4f}")

    for section_id, days in schedule.items():
        print(f"\n=== Schedule for Section: {section_id} ===")
        for day in sorted(days.keys(), key=lambda d: d.value):
            print(f"\n  {day.name}:")
            sessions = sorted(days[day], key=lambda g: g.start_time)
            for gene in sessions:
                subject = subject_dict[gene.subject_id]
                professor = professor_dict[gene.professor_id]
                room_name = room_dict[gene.room_id].id if gene.room_id and gene.room_id in room_dict else "Online"

                def format_time(time_float):
                    hour = int(time_float)
                    minute = int((time_float - hour) * 60)
                    suffix = "AM"
                    if hour >= 12:
                        suffix = "PM"
                        if hour > 12:
                            hour -= 12
                    if hour == 0:
                        hour = 12
                    return f"{hour}:{minute:02d} {suffix}"

                start_str = format_time(gene.start_time)
                end_str = format_time(gene.end_time)

                print(f"    {start_str} - {end_str} | {subject.id} (Session {gene.session_number}) | "
                      f"Prof: {professor.id} | Room: {room_name}")
