from models.resources import Room, Professor, Subject, Section, SessionType, SessionTemplate

def create_sample_data():
    rooms = [
        # LECTURE ROOM
        Room("431", 50, SessionType.LECTURE),
        Room("410", 50, SessionType.LECTURE),
        Room("407", 50, SessionType.LECTURE),
        Room("409", 50, SessionType.LECTURE),
        Room("433", 50, SessionType.LECTURE),
        Room("435", 50, SessionType.LECTURE),
        Room("401", 50, SessionType.LECTURE),
        Room("402", 50, SessionType.LECTURE),
        Room("403", 50, SessionType.LECTURE),
        Room("404", 50, SessionType.LECTURE),
        Room("405", 50, SessionType.LECTURE),
        Room("406", 50, SessionType.LECTURE),
        Room("407", 50, SessionType.LECTURE),
        #
        # #COMLAB ROOM
        Room("501", 50, SessionType.LAB),
        Room("502", 50, SessionType.LAB),
        Room("503", 50, SessionType.LAB),
        Room("504", 50, SessionType.LAB),
        Room("505", 50, SessionType.LAB),
        Room("537", 50, SessionType.LAB),
        #
        # #HARDWARE LAB ROOM
        # Room("534", 50, SessionType.HARDWARE_LAB),
        #
        # #extra
        # Room("423", 50, SessionType.LECTURE),

        # Room("431", 50, SessionType.LECTURE),
        # Room("505", 50, SessionType.LAB),
        # Room("506", 50, SessionType.LAB),
        # Room("432", 50, SessionType.LECTURE),

        Room("Hardware Lab1", 50, SessionType.HARDWARE_LAB),
        Room("Hardware Lab2", 50, SessionType.HARDWARE_LAB),
        Room("Hardware Lab3", 50, SessionType.HARDWARE_LAB),
        Room("Hardware Lab4", 50, SessionType.HARDWARE_LAB),

        Room("Hardware Lab5", 50, SessionType.HARDWARE_LAB),
        Room("Hardware Lab6", 50, SessionType.HARDWARE_LAB),

        Room("PE ROOM1", 50, SessionType.PHYS_LAB),
        Room("PE ROOM2", 50, SessionType.PHYS_LAB),
        Room("PE ROOM3", 50, SessionType.PHYS_LAB),
        Room("PE ROOM4", 50, SessionType.PHYS_LAB),
        Room("PE ROOM5", 50, SessionType.PHYS_LAB),
        Room("PE ROOM6", 50, SessionType.PHYS_LAB),
        Room("PE ROOM7", 50, SessionType.PHYS_LAB),
        Room("PE ROOM8", 50, SessionType.PHYS_LAB),
    ]
    professors = [
        Professor("J. BRAVO", ["CS"], ["CCDISTR1", "CTFDMBSL", "CCQUAMET"]),
        Professor("E. RAMIREZ", ["CS"], ["CCOBJPGL", "CCALCOMP", "CCINTHCI"]),
        Professor("S. REBUTOC", ["CS"], ["CCPHYS2L"]),
        Professor("M. ZUNIGA", ["CS", "IT"], ["CTBASNTL"]),
        Professor("J. SACDALAN", ["IT"], ["CCOBJPGL", "CTAPROJ1"]),
        Professor("M. GALO", ["IT"], ["CCOBJPGL"]),
        Professor("A. VICENTE", ["IT"], ["CCDISTR1"]),
        Professor("M. REYES", ["IT"], ["CCQUAMET"]),
        Professor("R. GALAPON", ["IT"], ["CTBASNTL", "CCINTHCI"]),
        Professor("A. CAMACHO", ["IT"], ["CTBASNTL", "CCINTHCI"]),
        Professor("S. LUMBOG", ["IT"], ["CTFDMBSL"]),
        Professor("F. ATIENZA", ["IT"], ["CTFDMBSL"]),
        Professor("R. VIADO", ["IT"], ["CTWBDEVL", "CTADWEBL"]),
        Professor("E. ALINO", ["IT"], ["CTWBDEVL", "CTAPROJ1"]),
        Professor("L. TAVU", ["CS"], ["CTAPDEVL"]),
        Professor("BUHAIN", ["IT"], ["CTAINASL"]),
        Professor("C. TORRES", ["IT"], ["CTAINASL"]),
        Professor("J. ABAO", ["IT"], ["CTAINASL"]),
        Professor("M.J QUILITAN", ["CS", "IT"], ["GEETH01X"]),
        Professor("JA LIBUNAO", ["CS", "IT"], ["GEETH01X"]),
        Professor("N. UMPAR", ["CS", "IT"], ["GEETH01X"]),
        Professor("D. URGELLES", ["CS", "IT"], ["GEETH01X"]),
        Professor("E. LAGOS", ["CS", "IT"], ["GEETH01X", "GENAT01R"]),
        Professor("E. NOLASCO", ["CS", "IT"], ["GEETH01X"]),
        Professor("A. CABRERA", ["CS", "IT"], ["GEETH01X"]),
        Professor("EJ LAYUG", ["CS", "IT"], ["GENAT01R"]),
        Professor("D. CONDEZ", ["CS", "IT"], ["GENAT01R"]),
        Professor("C. SANTIAGO", ["CS", "IT"], ["GENAT01R"]),
        Professor("G. BAYRAN", ["CS", "IT"], ["GENAT01R"]),
        Professor("C. LEGASPI", ["CS", "IT"], ["GENAT01R"]),
        Professor("T. MAGSINO", ["CS", "IT"], ["GENAT01R"]),
        Professor("BA ESTRADA", ["CS", "IT"], ["GENAT01R"]),
        Professor("Z. PENUS", ["CS", "IT"], ["GENAT01R"]),
        Professor("K. NOGA", ["CS", "IT"], ["GENAT01R"]),
        Professor("D. ABUTON", ["CS", "IT"], ["GENAT01R"]),
        Professor("E. PUNZALAN", ["CS", "IT"], ["GENAT01R"]),


        Professor("N. UZUMAKI", ["CS", "IT"], ["MNSTP02X"]),
        Professor("U. SASUKE", ["CS", "IT"], ["MNSTP02X"]),
        Professor("S. TONY", ["CS", "IT"], ["MNSTP02X"]),
        Professor("U. ", ["CS", "IT"], ["MNSTP02X"]),
        Professor("H. KAKASHI", ["CS", "IT"], ["MCFIT03X"]),
        Professor("H. SAKURA", ["CS", "IT"], ["MCFIT03X"]),
        Professor("H. asdas", ["CS", "IT"], ["MCFIT03X"]),
        Professor("H. erger", ["CS", "IT"], ["MCFIT03X"]),
    ]
    subjects = [
        Subject("GEETH01X", ["CS", "IT"], [
            SessionTemplate("GEETH01X", 1, SessionType.ONLINE, 2),
            SessionTemplate("GEETH01X", 2, SessionType.ONLINE, 2),
        ], False),
        Subject("GENAT01R", ["CS", "IT"], [
            SessionTemplate("GENAT01R", 1, SessionType.ONLINE, 2),
            SessionTemplate("GENAT01R", 2, SessionType.ONLINE, 2),
        ], False),
        Subject("MNSTP02X", ["CS", "IT"],[
            SessionTemplate("MNSTP02X", 1, SessionType.ONLINE, 2),
            SessionTemplate("MNSTP02X", 2, SessionType.ONLINE, 2),
        ], False),
        Subject("MCFIT03X", ["CS", "IT"],[
            SessionTemplate("MCFIT03X", 1, SessionType.PHYS_LAB, 2.67),
        ], True),
        Subject("CCDISTR1", ["CS", "IT"],[
            SessionTemplate("CCDISTR1", 1, SessionType.LECTURE, 2),
            SessionTemplate("CCDISTR1", 2, SessionType.LECTURE, 2),
        ], True),
        Subject("CCOBJPGL", ["CS", "IT"],[
            SessionTemplate("CCOBJPGL", 1, SessionType.LAB, 4),
            SessionTemplate("CCOBJPGL", 2, SessionType.LECTURE, 2.67),
        ], True),
        Subject("CCPHYS2L", ["CS", "IT"],[
            SessionTemplate("CCPHYS2L", 1, SessionType.LECTURE, 4),
            SessionTemplate("CCPHYS2L", 2, SessionType.LECTURE, 4),
        ], True),
        Subject("CTBASNTL", ["CS", "IT"],[
            SessionTemplate("CTBASNTL", 1, SessionType.HARDWARE_LAB, 4),
            SessionTemplate("CTBASNTL", 2, SessionType.HARDWARE_LAB, 2.67),
        ], True),
        Subject("CCALCOMP", ["CS"],[
            SessionTemplate("CCALCOMP", 1, SessionType.LECTURE, 1),
            SessionTemplate("CCALCOMP", 2, SessionType.LECTURE, 1),
        ], True),
        Subject("CTFDMBSL", ["CS", "IT"],[
            SessionTemplate("CTFDMBSL", 1, SessionType.LAB, 4),
            SessionTemplate("CTFDMBSL", 2, SessionType.LECTURE, 2.67),
        ], True),
        Subject("CCQUAMET", ["CS", "IT"],[
            SessionTemplate("CCQUAMET", 1, SessionType.LECTURE, 2),
            SessionTemplate("CCQUAMET", 2, SessionType.LECTURE, 2),
        ], True),
        Subject("CCINTHCI", ["CS", "IT"],[
            SessionTemplate("CCINTHCI", 1, SessionType.LAB, 4),
        ], True),
        Subject("CTAPDEVL", ["CS"],[
            SessionTemplate("CTAPDEVL", 1, SessionType.LAB, 4),
            SessionTemplate("CTAPDEVL", 2, SessionType.LECTURE, 2.67),
        ], True),
        Subject("CTWBDEVL", ["IT"], [
            SessionTemplate("CTWBDEVL", 1, SessionType.LAB, 4),
            SessionTemplate("CTWBDEVL", 2, SessionType.LECTURE, 2.67),
        ], True),
        Subject("CTAPROJ1", ["IT"], [
            SessionTemplate("CTAPROJ1", 1, SessionType.ONLINE, 2),
            SessionTemplate("CTAPROJ1", 2, SessionType.ONLINE, 2),
        ], False),
        Subject("CTAINASL", ["IT"],[
            SessionTemplate("CTAINASL", 1, SessionType.LECTURE, 2.67),
            SessionTemplate("CTAINASL", 2, SessionType.LAB, 4),
        ], True),
        Subject("CTADWEBL",["IT"], [
            SessionTemplate("CTADWEBL", 1, SessionType.LECTURE, 2.67),
            SessionTemplate("CTADWEBL", 2, SessionType.LAB, 4),
        ], True),
    ]

    sections = [
        # CS
        #
        # 1st year
        Section("COM241","CS",
                ["GEETH01X", "GENAT01R", "MNSTP02X", "MCFIT03X", "CCDISTR1", "CCOBJPGL"], 45),
        Section("COM242","CS",
                ["GEETH01X", "GENAT01R", "MNSTP02X", "MCFIT03X", "CCDISTR1", "CCOBJPGL"], 45),

        #2nd year
        Section("COM231" , "CS",
                ["CCPHYS2L", "CCQUAMET", "CTFDMBSL", "CCALCOMP", "CTBASNTL"], 45),
        Section("COM232","CS",
                ["CCPHYS2L", "CCQUAMET", "CTFDMBSL", "CCALCOMP", "CTBASNTL"], 45),

        #3rd year
        Section("COM221", "CS",
                ["CCINTHCI", "CTAPDEVL"], 45),

        #IT

        # 1st year
        Section("INF241",  "IT",
                ["CCOBJPGL", "CCDISTR1", "GEETH01X", "MNSTP02X", "GENAT01R", "MCFIT03X"], 45),
        Section("INF242",  "IT",
                ["CCOBJPGL", "CCDISTR1", "GEETH01X", "MNSTP02X", "GENAT01R", "MCFIT03X"], 45),
        Section("INF243", "IT",
                ["CCOBJPGL", "CCDISTR1", "GEETH01X", "MNSTP02X", "GENAT01R", "MCFIT03X"], 45),

        #2nd year
        Section("INF231",  "IT",
                ["CCQUAMET", "CTBASNTL", "CTFDMBSL", "CTWBDEVL"], 45),
        Section("INF232", "IT",
                ["CCQUAMET", "CTBASNTL", "CTFDMBSL", "CTWBDEVL"], 45),
        Section("INF233", "IT",
                ["CCQUAMET", "CTBASNTL", "CTFDMBSL", "CTWBDEVL"], 45),
        Section("INF234", "IT",
                ["CCQUAMET", "CTBASNTL", "CTFDMBSL", "CTWBDEVL"], 45),
        Section("INF235", "IT",
                ["CCQUAMET", "CTBASNTL", "CTFDMBSL", "CTWBDEVL"], 45),

        # 3rd year
        Section("INF221", "IT",
                ["CTAPROJ1", "CCINTHCI", "CTAINASL", "CTADWEBL"], 45),
        Section("INF222", "IT",
                ["CTAPROJ1", "CCINTHCI", "CTAINASL", "CTADWEBL"], 45),
        Section("INF223", "IT",
                ["CTAPROJ1", "CCINTHCI", "CTAINASL", "CTADWEBL"], 45),
        Section("INF224", "IT",
                ["CTAPROJ1", "CCINTHCI", "CTAINASL", "CTADWEBL"], 45)

    ]
    return sections, subjects, professors, rooms