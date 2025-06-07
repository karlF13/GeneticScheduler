# utils/conflicts.py
from typing import Dict, List, Optional
from models.resources import Day
from models.gene import Gene


class TimeSlot:
    def __init__(self, day: Day, start_time: float, duration: float):
        self.day = day
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration

    def overlaps_with(self, other: 'TimeSlot') -> bool:
        if self.day != other.day:
            return False
        return (self.start_time < other.end_time and
                other.start_time < self.end_time)


class ConflictTracker:
    """Tracks resource usage to prevent conflicts with professor consistency"""

    def __init__(self):
        # Track professor, room, and section schedules
        self.professor_schedule: Dict[str, List[TimeSlot]] = {}
        self.room_schedule: Dict[str, List[TimeSlot]] = {}
        self.section_schedule: Dict[str, List[TimeSlot]] = {}

        # Track professor assignments for subject-section pairs
        self.professor_assignments: Dict[tuple[str, str], str] = {}  # (section_id, subject_id) -> professor_id
        self.genes: List[Gene] = []

    def clear(self):
        self.professor_schedule.clear()
        self.room_schedule.clear()
        self.section_schedule.clear()
        self.professor_assignments.clear()
        self.genes.clear()

    def is_available(self, gene: Gene) -> bool:
        """Check if a gene can be scheduled without conflicts"""
        time_slot = TimeSlot(gene.day, gene.start_time, gene.duration)

        # First check professor consistency
        assignment_key = (gene.section_id, gene.subject_id)
        if assignment_key in self.professor_assignments:
            if gene.professor_id != self.professor_assignments[assignment_key]:
                return False  # Professor doesn't match previous assignment

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
        """Add a gene to the tracker, enforcing professor consistency"""
        assignment_key = (gene.section_id, gene.subject_id)

        # Check/update professor assignment
        if assignment_key in self.professor_assignments:
            if gene.professor_id != self.professor_assignments[assignment_key]:
                raise ValueError(
                    f"Professor conflict for {gene.section_id}-{gene.subject_id}. "
                    f"Assigned: {self.professor_assignments[assignment_key]}, "
                    f"Trying to assign: {gene.professor_id}"
                )
        else:
            self.professor_assignments[assignment_key] = gene.professor_id

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

        self.genes.append(gene)

    def get_assigned_professor(self, section_id: str, subject_id: str) -> Optional[str]:
        """Get the professor assigned to a subject-section pair if one exists"""
        return self.professor_assignments.get((section_id, subject_id), None)

    def remove_gene(self, gene: Gene):
        """Remove a gene from the tracker"""
        try:
            self.genes.remove(gene)
        except ValueError:
            pass

        time_slot = TimeSlot(gene.day, gene.start_time, gene.duration)

        # Remove from professor schedule
        if gene.professor_id in self.professor_schedule:
            try:
                self.professor_schedule[gene.professor_id].remove(time_slot)
                if not self.professor_schedule[gene.professor_id]:  # Clean up empty lists
                    del self.professor_schedule[gene.professor_id]
            except ValueError:
                pass

        # Remove from room schedule
        if gene.room_id and gene.room_id in self.room_schedule:
            try:
                self.room_schedule[gene.room_id].remove(time_slot)
                if not self.room_schedule[gene.room_id]:
                    del self.room_schedule[gene.room_id]
            except ValueError:
                pass

        # Remove from section schedule
        if gene.section_id in self.section_schedule:
            try:
                self.section_schedule[gene.section_id].remove(time_slot)
                if not self.section_schedule[gene.section_id]:
                    del self.section_schedule[gene.section_id]
            except ValueError:
                pass

        # Only remove professor assignment if no more sessions exist for this subject-section
        assignment_key = (gene.section_id, gene.subject_id)
        if assignment_key in self.professor_assignments:
            # Check if any remaining genes have this assignment
            has_remaining = any(
                g.section_id == gene.section_id and
                g.subject_id == gene.subject_id
                for g in self.genes
            )
            if not has_remaining:
                del self.professor_assignments[assignment_key]