from collections import defaultdict
from typing import List

from models.gene import Gene
from models.resources import Day, Subject

class Chromosome:

    def __init__(self, genes: List[Gene]):
        # A chromosome represents a full schedule (list of scheduled sessions/genes)
        self.genes = genes
        self.fitness = 0.0  # Fitness score (higher = better)

    def calculate_fitness(self, constraints) -> float:
        """
        Calculates the fitness of the chromosome based on several constraints
        """

        penalty = 0

        """ Hard constraints """
        # An instructor must not be scheduled to teach more than one class at the same time
        penalty += 100 * self._check_professor_conflicts()

        # No two classes may be scheduled in the same room at the same time.
        penalty += 100 * self._check_room_conflicts()

        # # A section must not have more than one class scheduled at the same time
        # penalty += 100 * self._check_section_conflicts()

        # Classes must be scheduled within the time window of 7:00 AM to 9:00 PM.
        penalty += 100 * self._check_time_window()

        # Sessions of the same subject should not be scheduled more than once on the same day.
        penalty += 100 * self._check_same_subject_same_day()

        """ Soft constraints """
        # A lunch break should be included in the daily schedule, typically between classes
        penalty += 50 * self._check_break_constraints()

        # Sessions of the same subject should preferably be scheduled on non-consecutive days.
        penalty += 50 * self.check_subject_spacing_violations()

        # Sessions of the same subject should preferably be scheduled in the same rooms.
        penalty += 20 * self._check_subject_room()

        # Subjects should be evenly distributed throughout the week.
        penalty += 30 * self.check_subject_distribution()

        # Professor teaching schedules should be arranged to prevent consecutive lessons without breaks.
        # penalty += 50 * self._check_professor_breaks()

        # Perfect fitness is 1.0
        self.fitness = 1000.0 / (1000.0 + penalty)
        return self.fitness

    def _check_professor_conflicts(self) -> int:
        """
        Counts number of sessions where a professor has overlapping sessions
        """
        conflicts = 0
        for i, gene1 in enumerate(self.genes):
            for j, gene2 in enumerate(self.genes):
                if i >= j:
                    continue
                if (gene1.professor_id == gene2.professor_id
                        and gene1.day == gene2.day):
                    if gene1.overlaps_with(gene2):
                        conflicts += 1
        return conflicts

    def _check_room_conflicts(self) -> int:
        """
        Counts number of overlapping sessions in the same room
        """
        conflicts = 0
        for i, gene1 in enumerate(self.genes):
            for j, gene2 in enumerate(self.genes):
                if i >= j:
                    continue
                if (gene1.room_id == gene2.room_id
                        and gene1.day == gene2.day
                        and gene1.room_id is not None):
                    if gene1.overlaps_with(gene2):
                        conflicts += 1
        return conflicts

    def _check_section_conflicts(self) -> int:
        """
        Counts number of overlapping sessions for the same student section
        """
        conflicts = 0
        for i, gene1 in enumerate(self.genes):
            for j, gene2 in enumerate(self.genes):
                if i >= j:
                    continue
                if (gene1.section_id == gene2.section_id
                        and gene1.day == gene2.day):
                    if gene1.overlaps_with(gene2):
                        conflicts += 1
        return conflicts

    def _check_time_window(self) -> int:
        """
        Penalizes classes that start too early or too late
        """
        violations = 0
        for gene in self.genes:
            if gene.start_time < 7.0 or gene.start_time > 21.0:
                violations += 1
        return violations

    def _check_break_constraints(self) -> int:
        """
        Penalizes classes that start during lunch break (12:00-13:00)
        """
        violations = 0
        for gene in self.genes:
            if 12.0 < gene.start_time < 13.0 or 12.0 < gene.end_time <= 13.0:
                violations += 1
        return violations

    def _check_same_subject_same_day(self) -> int:
        """
        Penalizes having multiple sessions of the same subject on the same day for a section
        """
        violations = 0
        section_day_subject = {}
        for gene in self.genes:
            key = (gene.section_id, gene.day)
            if key not in section_day_subject:
                section_day_subject[key] = set()
            if gene.subject_id in section_day_subject[key]:
                violations += 1
            else:
                section_day_subject[key].add(gene.subject_id)
        return violations

    def check_subject_distribution(self) -> int:
        """
        Checks if subject load per section is well-distributed across days.
        """
        #counts section subjects per day
        section_day_count = {}
        for gene in self.genes:
            key = (gene.section_id, gene.day)
            section_day_count[key] = section_day_count.get(key, 0) + 1

        # checks if the number of subjects are well distributed
        conflicts = 0
        for section_id in set(gene.section_id for gene in self.genes):
            day_counts = [section_day_count.get((section_id, day), 0) for day in Day]
            if max(day_counts) - min(day_counts) > 2:
                conflicts+=1

        return conflicts

    def check_subject_spacing_violations(self) -> int:
        """
        Checks if a subject's sessions for a section are scheduled too close together (e.g., back-to-back days)
        """
        conflicts = 0

        # Group genes by section and subject
        section_subject_genes = {}
        for gene in self.genes:
            key = (gene.section_id, gene.subject_id)
            if key not in section_subject_genes:
                section_subject_genes[key] = []
            section_subject_genes[key].append(gene)

        # Check each section-subject combination
        for (section_id, subject_id), genes in section_subject_genes.items():
            if len(genes) < 2:
                continue  # Need at least 2 sessions to have spacing violations

            # Get all days for this section-subject combination
            days = [gene.day for gene in genes]
            days_values = sorted([day.value for day in days])

            # Check for consecutive day violations
            for i in range(len(days_values) - 1):
                if days_values[i + 1] - days_values[i] == 1:
                    conflicts += 1

        return conflicts

    def _check_subject_room(self) -> int:
        """
        Penalizes if the same subject for the same section is held in different rooms
        for sessions of the same session_type.
        """
        conflicts = 0
        # Group genes by (section_id, subject_id, session_type)
        grouped = defaultdict(list)
        for gene in self.genes:
            key = (gene.section_id, gene.subject_id, gene.session_type)
            grouped[key].append(gene)

        # For each group, check if genes with different session_number have different rooms
        for key, genes in grouped.items():
            rooms_by_session = {}
            for gene in genes:
                # Store the room for this session_number
                if gene.session_number in rooms_by_session:
                    if rooms_by_session[gene.session_number] != gene.room_id:
                        # Same session number assigned different rooms? Possibly data error, count as conflict
                        conflicts += 1
                else:
                    rooms_by_session[gene.session_number] = gene.room_id

            # Now check if rooms differ across different session_numbers
            unique_rooms = set(rooms_by_session.values())
            if len(unique_rooms) > 1:
                # Number of conflicts is number of differing room pairs:
                # e.g., if 3 rooms, conflicts = combinations(3,2) = 3
                n = len(unique_rooms)
                conflicts += n * (n - 1) // 2

        return conflicts

    def _check_professor_breaks(self) -> int:
        """Check if professors have breaks between sessions"""
        violations = 0

        # Group genes by professor and day
        prof_day_sessions = {}
        for gene in self.genes:
            key = (gene.professor_id, gene.day)
            if key not in prof_day_sessions:
                prof_day_sessions[key] = []
            prof_day_sessions[key].append(gene)

        # Check each professor's daily schedule
        for (prof_id, day), sessions in prof_day_sessions.items():
            if len(sessions) <= 1:
                continue  # No need to check breaks for single session

            # Sort sessions by start time
            sessions.sort(key=lambda x: x.start_time)

            # Check gaps between consecutive sessions
            for i in range(len(sessions) - 1):
                current_session = sessions[i]
                next_session = sessions[i + 1]

                gap = next_session.start_time - current_session.end_time

                # # Violation if gap is less than 15 minutes
                # if gap < 0.25:
                #     violations += 1

                # Additional violation for back-to-back sessions (gap = 0)
                if gap == 0:
                    violations += 1

        return violations