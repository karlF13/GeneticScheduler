# utils/conflicts.py
from typing import Dict, List
from models.resources import Day
from models.gene import Gene

class TimeSlot:
    # class to manage timeslots

    def __init__(self, day: Day, start_time: float, duration: float):
        self.day = day
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration

    # For checking time conflicts
    def overlaps_with(self, other: 'TimeSlot') -> bool:
        if self.day != other.day:
            return False
        return (self.start_time < other.end_time and
                other.start_time < self.end_time)

class ConflictTracker:
    """Tracks resource usage to prevent conflicts"""

    def __init__(self):
        # Track professor, room, and section schedules
        self.professor_schedule: Dict[str, List[TimeSlot]] = {}
        self.room_schedule: Dict[str, List[TimeSlot]] = {}
        self.section_schedule: Dict[str, List[TimeSlot]] = {}

    def clear(self):
        self.professor_schedule.clear()
        self.room_schedule.clear()
        self.section_schedule.clear()

    def is_available(self, gene: Gene) -> bool:
        # stores a gene's timeslot
        time_slot = TimeSlot(gene.day, gene.start_time, gene.duration)

        # Check professor availability
        prof_slots = self.professor_schedule.get(gene.professor_id, [])
        for slot in prof_slots:
            if time_slot.overlaps_with(slot):
                return False

        # Check room availability
        if gene.room_id:
            room_slots = self.room_schedule.get(gene.room_id, [])
            for slot in room_slots:
                if time_slot.overlaps_with(slot):
                    return False

        # Check section availability
        section_slots = self.section_schedule.get(gene.section_id, [])
        for slot in section_slots:
            if time_slot.overlaps_with(slot):
                return False

        return True

    def add_gene(self, gene: Gene):
        time_slot = TimeSlot(gene.day, gene.start_time, gene.duration)

        # Add to professor schedule
        if gene.professor_id not in self.professor_schedule:
            self.professor_schedule[gene.professor_id] = []
        self.professor_schedule[gene.professor_id].append(time_slot)

        # Add to room schedule
        if gene.room_id:
            if gene.room_id not in self.room_schedule:
                self.room_schedule[gene.room_id] = []
            self.room_schedule[gene.room_id].append(time_slot)

        # Add to section schedule
        if gene.section_id not in self.section_schedule:
            self.section_schedule[gene.section_id] = []
        self.section_schedule[gene.section_id].append(time_slot)