# models/resources.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


# Enumeration for types of sessions that can be scheduled
class SessionType(Enum):
    LECTURE = "lecture"             # Regular lecture session
    LAB = "lab"                     # Computer lab session
    ONLINE = "ONLINE"               # Online session (no room)
    HARDWARE_LAB = "hardware lab"   # Hardware lab (hands-on classes)
    PHYS_LAB = "phys_lab"

class Day(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5

    #Wednesday skipped (no classes on wednesdays)

@dataclass
class SessionTemplate:
    subject_id: str             # ID of the subject (e.g., CCPHYS2L)
    session_number: int         # Session sequence number (e.g., 1st, 2nd session)
    session_type: SessionType   # Type of session (e.g., LECTURE, LAB)
    duration_hours: float       # Duration of session in hours

@dataclass
class Room:
    id: str                     # Unique room ID (e.g., "431")
    capacity: int               # Maximum number of students the room can accommodate
    room_type: List[SessionType]      # Type of room (must match the session type)
    preferred_courses: Optional[List[str]] = None

@dataclass
class Professor:
    id: str                     # Unique professor ID (e.g., "P001")
    course: List[str]
    subjects: List[str]         # List of subject IDs the professor is qualified to teach

@dataclass
class Subject:
    id: str                     # Unique subject ID (e.g., "CTFDMBSL")
    course: List[str]
    # name: str                   # Full name of the subject
    sessions: List[SessionTemplate] # Session requirements for the subject
    requires_room: bool

@dataclass
class Section:
    id: str             # Unique section ID (e.g., "COM231")
    course: str
    subjects: List[str] # List of subject IDs this section is enrolled in
    max_students: int   # Maximum number of students in this section

