from models.resources import Room, Professor, Subject, Section, SessionType, SessionTemplate

def create_sample_data():
    rooms = [
        Room("431", 50, SessionType.LECTURE),
        Room("505", 50, SessionType.LAB),
        Room("432", 50, SessionType.LECTURE),

        # Room("433", "Lecture Room2", 50, SessionType.LECTURE),
        Room("Hardware Lab", 50, SessionType.HARDWARE_LAB)
    ]
    professors = [
        Professor("P001", "John Samuel Rebutoc", ["CCPHYS2L"]),
        Professor("P002", "Jobert D. Bravo", ["CCQUAMET", "CTFDMBSL"]),
        Professor("P003", "Emmanuel A. Ramirez", ["CCALCOMP"]),
        Professor("P004", "Emmanuel P. Zuñiga", ["CTBASNTL"]),
    ]
    subjects = [
        Subject("CCPHYS2L", "COLLEGE PHYSICS 2", [
            SessionTemplate("CCPHYS2L", 1, SessionType.LECTURE, 4.0),
            SessionTemplate("CCPHYS2L", 2, SessionType.LECTURE, 4.0)
        ]),
        Subject("CCQUAMET", "QUANTITATIVE METHODS", [
            SessionTemplate("CCQUAMET", 1, SessionType.LECTURE, 2.0),
            SessionTemplate("CCQUAMET", 2, SessionType.LECTURE, 2.0)
        ]),
        Subject("CTFDMBSL", "DATABASE SYSTEMS", [
            SessionTemplate("CTFDMBSL", 1, SessionType.LECTURE, 2.67),
            SessionTemplate("CTFDMBSL", 2, SessionType.LAB, 3.0)
        ]),
        Subject("CCALCOMP", "ALGORITHMS AND COMPLEXITY", [
            SessionTemplate("CCALCOMP", 1, SessionType.LECTURE, 2.0),
            SessionTemplate("CCALCOMP", 2, SessionType.LECTURE, 2.0)
        ]),
        Subject("CTBASNTL", "BASIC NETWORKING", [
            SessionTemplate("CTBASNTL", 1, SessionType.HARDWARE_LAB, 4.0),
            SessionTemplate("CTBASNTL", 2, SessionType.HARDWARE_LAB, 2.67)
        ])
    ]

    sections = [
        Section("COM231",
                ["CCPHYS2L", "CCQUAMET", "CTFDMBSL", "CCALCOMP", "CTBASNTL"], 45),
        Section("COM232",
                ["CCPHYS2L", "CCQUAMET", "CTFDMBSL", "CCALCOMP", "CTBASNTL"], 45),

    ]
    return sections, subjects, professors, rooms
