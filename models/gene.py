from dataclasses import dataclass
from typing import Dict, Optional

from models.resources import Day, Subject, SessionType

@dataclass
class Gene:
    # Represents a single scheduled session (a "gene" in the chromosome)
    section_id: str          # ID of the student section (e.g., "COM231")
    subject_id: str          # ID of the subject (e.g., "CCPHYS2L")
    session_number: int      # Which session of the subject this gene represents (e.g., 1 or 2)
    session_type: SessionType
    professor_id: str        # ID of the assigned professor
    room_id: str             # ID of the assigned room
    day: Day                 # Day of the week the session is scheduled
    start_time: float        # Start time of the session in 24-hour format (e.g., 13.5 for 1:30 PM)
    duration: float          # Duration of the session in hours

    @property
    def end_time(self) -> float:
        """
        Returns the end time of the session by adding duration to start time.
        """
        return self.start_time + self.duration

    def overlaps_with(self, other: 'Gene') -> bool:
        """
         Checks if this session overlaps with another session on the same day (e.g., room, section, prof conflicts)
        """
        if self.day != other.day:
            return False
        return (self.start_time < other.end_time and
                other.start_time < self.end_time)

