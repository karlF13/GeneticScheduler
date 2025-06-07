import random
from collections import defaultdict
from typing import List, Optional, Tuple, Dict

from models.resources import Room, Professor, Subject, Section, SessionTemplate, Day
from models.gene import Gene
from models.chromosome import Chromosome
from utils.conflicts import ConflictTracker


class GeneticScheduler:
    def __init__(self,
                 sections: List[Section],
                 subjects: List[Subject],
                 professors: List[Professor],
                 rooms: List[Room],
                 population_size: int = 100,
                 mutation_rate: float = 0.01,
                 crossover_rate: float = 0.8,
                 generations: int = 5000):

        self.sections = sections
        self.subjects = subjects
        self.professors = professors
        self.rooms = rooms
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.generations = generations

        self.subject_dict = {s.id: s for s in subjects}
        self.professor_dict = {p.id: p for p in professors}
        self.room_dict = {r.id: r for r in rooms}
        self.section_dict = {sc.id: sc for sc in sections}

        self.valid_time_slots = [7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0]

        # Pre-compute valid start times for each duration
        self.valid_start_times = {}
        for duration in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
            valid_starts = []
            for start_time in self.valid_time_slots:
                end_time = start_time + duration
                if end_time <= 19.0 and not (start_time < 13.0 and end_time > 12.0):
                    valid_starts.append(start_time)
            self.valid_start_times[duration] = valid_starts

        # Pre-compute professor-subject mappings
        self.professor_subjects = {}
        for prof in professors:
            for subject_id in prof.subjects:
                if subject_id not in self.professor_subjects:
                    self.professor_subjects[subject_id] = []
                self.professor_subjects[subject_id].append(prof)

        # Pre-compute room-type mappings
        self.room_types = {}
        for room in rooms:
            if room.room_type not in self.room_types:
                self.room_types[room.room_type] = []
            self.room_types[room.room_type].append(room)

        # Pre-compute sessions to schedule
        self.sessions_to_schedule = []
        for section in sections:
            for subject_id in section.subjects:
                subject = self.subject_dict[subject_id]
                for session_template in subject.sessions:
                    self.sessions_to_schedule.append((section, subject_id, session_template))

        self.genome_length = len(self.sessions_to_schedule)

    def _get_eligible_professors_fast(self, subject_id: str, course: str) -> List[Professor]:
        """Fast professor lookup using pre-computed mappings"""
        if subject_id not in self.professor_subjects:
            return []
        return [p for p in self.professor_subjects[subject_id] if course in p.course]

    def _get_eligible_rooms_fast(self, session_type: str) -> List[Room]:
        """Fast room lookup using pre-computed mappings"""
        return self.room_types.get(session_type, [])

    def create_smart_chromosome(self) -> Chromosome:
        genes = []
        conflict_tracker = ConflictTracker()
        professor_assignments = {}
        room_usage = {r.id: 0 for r in self.rooms}

        # Sort sessions by priority once
        sessions_sorted = sorted(
            self.sessions_to_schedule,
            key=lambda x: (
                    x[2].duration_hours * 10 +
                    (2 if self.subject_dict[x[1]].requires_room else 1)
            ),
            reverse=True
        )

        for section, subject_id, session_template in sessions_sorted:
            # Get eligible rooms sorted by usage
            eligible_rooms = []
            if self.subject_dict[subject_id].requires_room:
                eligible_rooms = sorted(
                    self._get_eligible_rooms_fast(session_template.session_type),
                    key=lambda r: room_usage[r.id]
                )

            # Try conflict-free creation with top rooms
            gene = None
            for room in eligible_rooms[:3]:
                gene = self._create_conflict_free_gene_fast(
                    section, subject_id, session_template,
                    conflict_tracker, room
                )
                if gene:
                    room_usage[room.id] += 1
                    break

            if not gene:
                gene = self._create_conflict_free_gene_fast(
                    section, subject_id, session_template, conflict_tracker
                )
                if gene and gene.room_id:
                    room_usage[gene.room_id] += 1

            if not gene:
                gene = self._create_random_gene_fast(
                    section, subject_id, session_template, professor_assignments
                )
                if gene and gene.room_id:
                    room_usage[gene.room_id] += 1

            if gene:
                genes.append(gene)
                conflict_tracker.add_gene(gene)
                professor_assignments[(section.id, subject_id)] = gene.professor_id

        return Chromosome(genes)

    def _create_conflict_free_gene_fast(self, section: Section, subject_id: str,
                                        session_template: SessionTemplate,
                                        conflict_tracker: ConflictTracker,
                                        preferred_room: Room = None) -> Optional[Gene]:
        """Optimized conflict-free gene creation"""
        existing_prof = conflict_tracker.get_assigned_professor(section.id, subject_id)

        if existing_prof:
            eligible_professors = [p for p in self.professors if p.id == existing_prof]
        else:
            eligible_professors = self._get_eligible_professors_fast(subject_id, section.course)

        if not eligible_professors:
            return None

        # Room selection
        if self.subject_dict[subject_id].requires_room:
            eligible_rooms = [preferred_room] if preferred_room else self._get_eligible_rooms_fast(
                session_template.session_type)
        else:
            eligible_rooms = []

        # Use pre-computed valid start times
        valid_starts = self.valid_start_times.get(session_template.duration_hours, [])
        if not valid_starts:
            return None

        # Limit attempts for speed
        for _ in range(50):  # Reduced from 100
            professor = random.choice(eligible_professors)
            room_id = random.choice(eligible_rooms).id if eligible_rooms else None
            day = random.choice(list(Day))
            start_time = random.choice(valid_starts)

            gene = Gene(
                section_id=section.id,
                subject_id=subject_id,
                session_number=session_template.session_number,
                session_type=session_template.session_type,
                professor_id=professor.id,
                room_id=room_id,
                day=day,
                start_time=start_time,
                duration=session_template.duration_hours
            )

            if conflict_tracker.is_available(gene):
                return gene

        return None

    def _create_random_gene_fast(self, section: Section, subject_id: str,
                                 session_template: SessionTemplate,
                                 existing_assignments: Dict[Tuple[str, str], str] = None) -> Gene:
        """Optimized random gene creation"""
        if existing_assignments is None:
            existing_assignments = {}

        key = (section.id, subject_id)
        if key in existing_assignments:
            professor = self.professor_dict[existing_assignments[key]]
        else:
            eligible_professors = self._get_eligible_professors_fast(subject_id, section.course)
            professor = random.choice(eligible_professors)
            existing_assignments[key] = professor.id

        room_id = None
        if self.subject_dict[subject_id].requires_room:
            eligible_rooms = self._get_eligible_rooms_fast(session_template.session_type)
            if eligible_rooms:
                room_id = random.choice(eligible_rooms).id

        day = random.choice(list(Day))
        start_time = random.choice(self.valid_time_slots)

        return Gene(
            section_id=section.id,
            subject_id=subject_id,
            session_number=session_template.session_number,
            session_type=session_template.session_type,
            professor_id=professor.id,
            room_id=room_id,
            day=day,
            start_time=start_time,
            duration=session_template.duration_hours
        )

    def create_random_chromosome(self) -> Chromosome:
        if random.random() < 0.5:
            return self.create_smart_chromosome()

        genes = []
        for section, subject_id, session_template in self.sessions_to_schedule:
            gene = self._create_random_gene_fast(section, subject_id, session_template)
            genes.append(gene)

        return Chromosome(genes)

    def initialize_population(self) -> List[Chromosome]:
        population = []
        smart_count = int(0.3 * self.population_size)

        for _ in range(smart_count):
            population.append(self.create_smart_chromosome())

        for _ in range(self.population_size - smart_count):
            population.append(self.create_random_chromosome())

        return population

    def smart_mutate(self, chromosome: Chromosome) -> Chromosome:
        """Optimized mutation"""
        for i, gene in enumerate(chromosome.genes):
            if random.random() < self.mutation_rate:
                mutation_type = random.choice(['professor', 'room', 'time', 'day', 'swap'])

                if mutation_type == 'swap' and len(chromosome.genes) > 1:
                    j = random.randint(0, len(chromosome.genes) - 1)
                    if i != j:
                        other_gene = chromosome.genes[j]
                        gene.day, other_gene.day = other_gene.day, gene.day
                        gene.start_time, other_gene.start_time = other_gene.start_time, gene.start_time

                elif mutation_type == 'professor':
                    eligible_professors = self._get_eligible_professors_fast(gene.subject_id,
                                                                             self.section_dict[gene.section_id].course)
                    if eligible_professors:
                        gene.professor_id = random.choice(eligible_professors).id

                elif mutation_type == 'room' and gene.room_id:
                    eligible_rooms = self._get_eligible_rooms_fast(gene.session_type)
                    if eligible_rooms:
                        gene.room_id = random.choice(eligible_rooms).id

                elif mutation_type == 'time':
                    valid_times = self.valid_start_times.get(gene.duration, [])
                    if valid_times:
                        gene.start_time = random.choice(valid_times)

                elif mutation_type == 'day':
                    gene.day = random.choice(list(Day))

        return chromosome

    def crossover(self, parent1: Chromosome, parent2: Chromosome) -> tuple[Chromosome, Chromosome]:
        if random.random() > self.crossover_rate:
            return parent1, parent2

        crossover_point = random.randint(1, len(parent1.genes) - 1)

        child1_genes = parent1.genes[:crossover_point] + parent2.genes[crossover_point:]
        child2_genes = parent2.genes[:crossover_point] + parent1.genes[crossover_point:]

        # Use faster repair
        child1 = self._repair_chromosome_fast(Chromosome(child1_genes))
        child2 = self._repair_chromosome_fast(Chromosome(child2_genes))

        return child1, child2

    def mutate(self, chromosome: Chromosome) -> Chromosome:
        return self.smart_mutate(chromosome)

    def tournament_selection(self, population: List[Chromosome]) -> Chromosome:
        tournament_size = max(3, len(population) // 5)
        tournament = random.sample(population, tournament_size)
        return max(tournament, key=lambda x: x.fitness)

    def _repair_chromosome_fast(self, chromosome: Chromosome) -> Chromosome:
        """Faster chromosome repair with limited attempts"""
        conflict_tracker = ConflictTracker()
        repaired_genes = []

        # Sort once by priority
        sorted_genes = sorted(chromosome.genes,
                              key=lambda g: (g.duration, self._get_gene_priority(g)),
                              reverse=True)

        for gene in sorted_genes:
            if conflict_tracker.is_available(gene):
                repaired_genes.append(gene)
                conflict_tracker.add_gene(gene)
            else:
                # Try quick repair with limited attempts
                repaired_gene = self._quick_repair(gene, conflict_tracker)
                if repaired_gene:
                    repaired_genes.append(repaired_gene)
                    conflict_tracker.add_gene(repaired_gene)

        # Create temporary chromosome for further repairs
        temp_chromosome = Chromosome(repaired_genes)

        # Apply additional repairs
        temp_chromosome = self.repair_subject_room(temp_chromosome)
        temp_chromosome = self.repair_professor_breaks(temp_chromosome)

        return temp_chromosome

    def _quick_repair(self, gene: Gene, conflict_tracker: ConflictTracker) -> Optional[Gene]:
        """Fast repair with limited attempts"""
        eligible_professors = self._get_eligible_professors_fast(gene.subject_id,
                                                                 self.section_dict[gene.section_id].course)
        eligible_rooms = self._get_eligible_rooms_fast(gene.session_type) if self.subject_dict[
            gene.subject_id].requires_room else []
        valid_times = self.valid_start_times.get(gene.duration, [])

        # Try only 20 combinations for speed
        for _ in range(20):
            professor = random.choice(eligible_professors) if eligible_professors else None
            if not professor:
                continue

            room_id = random.choice(eligible_rooms).id if eligible_rooms else None
            day = random.choice(list(Day))
            start_time = random.choice(valid_times) if valid_times else random.choice(self.valid_time_slots)

            candidate = Gene(
                section_id=gene.section_id,
                subject_id=gene.subject_id,
                session_number=gene.session_number,
                session_type=gene.session_type,
                professor_id=professor.id,
                room_id=room_id,
                day=day,
                start_time=start_time,
                duration=gene.duration
            )

            if conflict_tracker.is_available(candidate):
                return candidate

        return None

    def repair_subject_room(self, chromosome: Chromosome) -> Chromosome:
        """
        Ensures sessions of the same subject (for same section/session_type)
        are scheduled in the same room when possible.
        """
        # Group genes by (section_id, subject_id, session_type)
        subject_groups = defaultdict(list)
        for gene in chromosome.genes:
            key = (gene.section_id, gene.subject_id, gene.session_type)
            subject_groups[key].append(gene)

        # Process each subject group
        for key, genes in subject_groups.items():
            if len(genes) < 2:
                continue  # Need at least 2 sessions to have room conflicts

            # Find the most commonly used valid room in this group
            room_counter = defaultdict(int)
            for gene in genes:
                if gene.room_id:
                    room_counter[gene.room_id] += 1

            if not room_counter:
                continue  # No rooms assigned to any session

            most_common_room = max(room_counter.items(), key=lambda x: x[1])[0]

            # Get all eligible rooms for this session type
            session_type = genes[0].session_type
            eligible_rooms = [r.id for r in self._get_eligible_rooms_fast(session_type)]

            # Only proceed if most common room is actually eligible
            if most_common_room not in eligible_rooms:
                continue

            # Assign all sessions to the most common room
            for gene in genes:
                if gene.room_id != most_common_room:
                    gene.room_id = most_common_room

        return chromosome

    def repair_professor_breaks(self, chromosome: Chromosome) -> Chromosome:
        """
        Ensures professors have reasonable breaks between consecutive classes
        by adjusting session times when possible.
        """
        # Group genes by professor and day
        prof_schedules = defaultdict(lambda: defaultdict(list))
        for gene in chromosome.genes:
            prof_schedules[gene.professor_id][gene.day].append(gene)

        min_break = 0.5  # Minimum 30-minute break between classes

        for prof_id, days_schedule in prof_schedules.items():
            for day, sessions in days_schedule.items():
                if len(sessions) < 2:
                    continue

                # Sort sessions by start time
                sessions.sort(key=lambda x: x.start_time)

                # Check consecutive sessions
                for i in range(len(sessions) - 1):
                    current = sessions[i]
                    next_session = sessions[i + 1]

                    gap = next_session.start_time - current.end_time

                    if gap < min_break:
                        # Try to fix by moving next session later
                        required_start = current.end_time + min_break
                        max_start = 21.0 - next_session.duration

                        if required_start <= max_start:
                            next_session.start_time = required_start
                        else:
                            # If can't move later, try moving current earlier
                            required_start = next_session.start_time - current.duration - min_break
                            if required_start >= 7.0:
                                current.start_time = required_start
                            else:
                                # If neither works, swap days with a random gene
                                other_genes = [g for g in chromosome.genes
                                               if g.day != day and g.professor_id != prof_id]
                                if other_genes:
                                    swap_gene = random.choice(other_genes)
                                    current.day, swap_gene.day = swap_gene.day, current.day

        return chromosome

    def evolve(self) -> Chromosome:
        """Optimized evolution loop"""
        population = self.initialize_population()
        best_fitness_history = []
        stagnation_counter = 0

        for generation in range(self.generations):
            # Calculate fitness for all chromosomes
            for chromosome in population:
                chromosome.calculate_fitness(None)

            # Sort by fitness (best first)
            population.sort(key=lambda x: x.fitness, reverse=True)

            best_fitness = population[0].fitness
            best_fitness_history.append(best_fitness)

            # Early termination for perfect solution
            if best_fitness >= 0.99:
                print(f"Perfect solution found at generation {generation}!")
                break

            # Check stagnation with smaller window for faster detection
            if len(best_fitness_history) > 30:  # Reduced from 50
                recent_improvement = max(best_fitness_history[-30:]) - min(best_fitness_history[-30:])
                if recent_improvement < 0.001:
                    stagnation_counter += 1
                else:
                    stagnation_counter = 0

                if stagnation_counter > 50:  # Reduced from 100
                    print(f"Stopping due to stagnation at generation {generation}")
                    break

            # Print progress less frequently
            if generation % 200 == 0:  # Reduced from 100
                conflicts = (population[0]._check_professor_conflicts() +
                             population[0]._check_room_conflicts() +
                             population[0]._check_section_conflicts())
                print(f"Generation {generation}: Best fitness = {best_fitness:.4f}, Conflicts = {conflicts}")

            # Create new population
            new_population = []

            # Keep best individuals (elitism)
            elite_count = int(0.2 * self.population_size)
            new_population.extend(population[:elite_count])

            # Generate rest through crossover and mutation
            while len(new_population) < self.population_size:
                parent1 = self.tournament_selection(population)
                parent2 = self.tournament_selection(population)

                child1, child2 = self.crossover(parent1, parent2)
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)

                new_population.extend([child1, child2])

            population = new_population[:self.population_size]

        # Return best solution
        for chromosome in population:
            chromosome.calculate_fitness(None)

        return max(population, key=lambda x: x.fitness)

    def _get_gene_priority(self, gene: Gene) -> int:
        """Fast priority calculation"""
        priority = gene.duration * 10
        if self.subject_dict[gene.subject_id].requires_room:
            priority += 5
        if gene.session_type == "lab":
            priority += 3
        return priority