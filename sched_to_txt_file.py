import os
from typing import List, Dict
from collections import defaultdict
from datetime import datetime


def print_schedule_to_file(chromosome, output_filename="schedule_output.txt"):
    if not chromosome:
        with open(output_filename, 'w') as f:
            f.write("No valid schedule found\n")
        return

    # Calculate penalty breakdown
    penalty_breakdown = {
        'professor_conflicts': 100 * chromosome._check_professor_conflicts(),
        'room_conflicts': 100 * chromosome._check_room_conflicts(),
        'time_window': 100 * chromosome._check_time_window(),
        'same_subject_same_day': 100 * chromosome._check_same_subject_same_day(),
        'break_constraints': 50 * chromosome._check_break_constraints(),
        'subject_spacing': 50 * chromosome.check_subject_spacing_violations(),
        'subject_room': 20 * chromosome._check_subject_room(),
        'professor_breaks': 50 * chromosome._check_professor_breaks(),
        'wed_sat_constraints': 40 * chromosome._check_wednesday_saturday_constraints()
    }
    total_penalty = sum(penalty_breakdown.values())

    # Track TBA assignments
    tba_subjects = set()

    # Group genes by section
    schedule_by_section = defaultdict(list)
    for gene in chromosome.genes:
        schedule_by_section[gene.section_id].append(gene)
        if gene.professor_id == "TBA":
            tba_subjects.add(gene.subject_id)

    # Write to file
    with open(output_filename, 'w') as f:
        # Write header with timestamp
        f.write("=" * 60 + "\n")
        f.write("AUTOMATED SCHEDULE REPORT\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")

        # Write schedule summary
        f.write("SCHEDULE SUMMARY\n")
        f.write("-" * 20 + "\n")
        f.write(f"Fitness Score: {chromosome.fitness:.4f}\n")
        f.write(f"Total Penalty: {total_penalty}\n\n")

        # Write penalty breakdown
        f.write("PENALTY BREAKDOWN\n")
        f.write("-" * 20 + "\n")
        for constraint, value in penalty_breakdown.items():
            constraint_name = constraint.replace('_', ' ').title()
            f.write(f"{constraint_name:<25}: {value}\n")
        f.write("\n")

        # Write detailed schedule by section
        f.write("DETAILED SCHEDULE BY SECTION\n")
        f.write("=" * 40 + "\n\n")

        for section_id in sorted(schedule_by_section.keys()):
            f.write(f"Section {section_id}\n")
            f.write("-" * (len(section_id) + 8) + "\n")

            # Sort by day and then by time
            section_genes = sorted(schedule_by_section[section_id],
                                   key=lambda g: (g.day.value, g.start_time))

            if not section_genes:
                f.write("  No classes scheduled\n\n")
                continue

            for gene in section_genes:
                start_time = f"{int(gene.start_time):02d}:{int((gene.start_time % 1) * 60):02d}"
                end_time = f"{int(gene.end_time):02d}:{int((gene.end_time % 1) * 60):02d}"
                room_info = f"Room: {gene.room_id}" if gene.room_id else "Online"

                prof_display = gene.professor_id if gene.professor_id != "TBA" else "TBA (No qualified professor)"

                f.write(f"  {gene.day.name:<9} | {start_time}-{end_time} | {gene.subject_id:<12} "
                        f"({gene.session_number}) | Prof: {prof_display:<20} | {room_info}\n")

            f.write("\n")

        # Write TBA assignments summary
        if tba_subjects:
            f.write("SUBJECTS REQUIRING PROFESSOR ASSIGNMENT\n")
            f.write("=" * 40 + "\n")
            f.write("The following subjects have been scheduled but need professors to be assigned:\n\n")
            for subject_id in sorted(tba_subjects):
                f.write(f"  - {subject_id}\n")
            f.write(f"\nTotal subjects needing professors: {len(tba_subjects)}\n\n")

        # Write additional statistics
        f.write("SCHEDULE STATISTICS\n")
        f.write("-" * 20 + "\n")
        total_classes = len(chromosome.genes)
        total_sections = len(schedule_by_section)
        classes_per_section = total_classes / total_sections if total_sections > 0 else 0

        f.write(f"Total Classes Scheduled: {total_classes}\n")
        f.write(f"Total Sections: {total_sections}\n")
        f.write(f"Average Classes per Section: {classes_per_section:.1f}\n")

        # Count classes by day
        classes_by_day = defaultdict(int)
        for gene in chromosome.genes:
            classes_by_day[gene.day.name] += 1

        f.write("\nClasses by Day:\n")
        for day, count in sorted(classes_by_day.items()):
            f.write(f"  {day}: {count} classes\n")

    print(f"Schedule has been written to: {output_filename}")
    print(f"File location: {os.path.abspath(output_filename)}")


def print_schedule_by_professor_to_file(chromosome, output_filename="professor_schedule.txt"):

    if not chromosome:
        with open(output_filename, 'w') as f:
            f.write("No valid schedule found\n")
        return

    # Group genes by professor
    schedule_by_professor = defaultdict(list)
    for gene in chromosome.genes:
        if gene.professor_id and gene.professor_id != "TBA":
            schedule_by_professor[gene.professor_id].append(gene)

    # Separate TBA assignments
    tba_assignments = [gene for gene in chromosome.genes if gene.professor_id == "TBA"]

    with open(output_filename, 'w') as f:
        # Write header
        f.write("=" * 60 + "\n")
        f.write("PROFESSOR SCHEDULE REPORT\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")

        # Write schedule by professor
        for professor_id in sorted(schedule_by_professor.keys()):
            f.write(f"Professor: {professor_id}\n")
            f.write("-" * (len(professor_id) + 11) + "\n")

            # Sort by day and then by time
            professor_genes = sorted(schedule_by_professor[professor_id],
                                     key=lambda g: (g.day.value, g.start_time))

            # Calculate total hours for this professor
            total_hours = sum(gene.duration for gene in professor_genes)
            f.write(f"Total Weekly Hours: {total_hours:.1f}\n\n")

            for gene in professor_genes:
                start_time = f"{int(gene.start_time):02d}:{int((gene.start_time % 1) * 60):02d}"
                end_time = f"{int(gene.end_time):02d}:{int((gene.end_time % 1) * 60):02d}"
                room_info = f"Room: {gene.room_id}" if gene.room_id else "Online"

                f.write(f"  {gene.day.name:<9} | {start_time}-{end_time} | {gene.subject_id:<12} "
                        f"| Section: {gene.section_id:<8} | {room_info}\n")

            f.write("\n")

        # Write TBA assignments
        if tba_assignments:
            f.write("UNASSIGNED CLASSES (TBA)\n")
            f.write("=" * 25 + "\n")
            f.write("The following classes need professor assignment:\n\n")

            for gene in sorted(tba_assignments, key=lambda g: (g.section_id, g.subject_id)):
                start_time = f"{int(gene.start_time):02d}:{int((gene.start_time % 1) * 60):02d}"
                end_time = f"{int(gene.end_time):02d}:{int((gene.end_time % 1) * 60):02d}"
                room_info = f"Room: {gene.room_id}" if gene.room_id else "Online"

                f.write(f"  {gene.day.name:<9} | {start_time}-{end_time} | {gene.subject_id:<12} "
                        f"| Section: {gene.section_id:<8} | {room_info}\n")

    print(f"Professor schedule has been written to: {output_filename}")
    print(f"File location: {os.path.abspath(output_filename)}")


def print_schedule_by_room_to_file(chromosome, output_filename="room_schedule.txt"):

    if not chromosome:
        with open(output_filename, 'w') as f:
            f.write("No valid schedule found\n")
        return

    # Group genes by room
    schedule_by_room = defaultdict(list)
    online_classes = []

    for gene in chromosome.genes:
        if gene.room_id:
            schedule_by_room[gene.room_id].append(gene)
        else:
            online_classes.append(gene)

    with open(output_filename, 'w') as f:
        # Write header
        f.write("=" * 60 + "\n")
        f.write("ROOM UTILIZATION REPORT\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")

        # Write schedule by room
        for room_id in sorted(schedule_by_room.keys()):
            f.write(f"Room: {room_id}\n")
            f.write("-" * (len(room_id) + 6) + "\n")

            # Sort by day and then by time
            room_genes = sorted(schedule_by_room[room_id],
                                key=lambda g: (g.day.value, g.start_time))

            # Calculate utilization
            total_hours = sum(gene.duration for gene in room_genes)
            f.write(f"Total Weekly Hours: {total_hours:.1f}\n")
            f.write(f"Number of Classes: {len(room_genes)}\n\n")

            for gene in room_genes:
                start_time = f"{int(gene.start_time):02d}:{int((gene.start_time % 1) * 60):02d}"
                end_time = f"{int(gene.end_time):02d}:{int((gene.end_time % 1) * 60):02d}"
                prof_display = gene.professor_id if gene.professor_id != "TBA" else "TBA"

                f.write(f"  {gene.day.name:<9} | {start_time}-{end_time} | {gene.subject_id:<12} "
                        f"| Section: {gene.section_id:<8} | Prof: {prof_display}\n")

            f.write("\n")

        # Write online classes
        if online_classes:
            f.write("ONLINE CLASSES\n")
            f.write("=" * 15 + "\n")
            f.write("Classes that don't require a physical room:\n\n")

            for gene in sorted(online_classes, key=lambda g: (g.day.value, g.start_time)):
                start_time = f"{int(gene.start_time):02d}:{int((gene.start_time % 1) * 60):02d}"
                end_time = f"{int(gene.end_time):02d}:{int((gene.end_time % 1) * 60):02d}"
                prof_display = gene.professor_id if gene.professor_id != "TBA" else "TBA"

                f.write(f"  {gene.day.name:<9} | {start_time}-{end_time} | {gene.subject_id:<12} "
                        f"| Section: {gene.section_id:<8} | Prof: {prof_display}\n")

    print(f"Room schedule has been written to: {output_filename}")
    print(f"File location: {os.path.abspath(output_filename)}")


def generate_all_schedule_reports(chromosome, base_filename="schedule"):

    print_schedule_to_file(chromosome, f"{base_filename}_by_section.txt")
    print_schedule_by_professor_to_file(chromosome, f"{base_filename}_by_professor.txt")
    print_schedule_by_room_to_file(chromosome, f"{base_filename}_by_room.txt")

    print("\nAll schedule reports have been generated:")
    print(f"  - {base_filename}_by_section.txt")
    print(f"  - {base_filename}_by_professor.txt")
    print(f"  - {base_filename}_by_room.txt")
