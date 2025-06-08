import random
import copy
from typing import List, Tuple, Dict, Set, Optional
from collections import defaultdict
import math

from models.gene import Gene
from models.chromosome import Chromosome
from models.resources import Day, SessionType, Room, Professor, Subject, Section, SessionTemplate


class GeneticAlgorithm:
    def __init__(self,
                 sections: List[Section],
                 subjects: List[Subject],
                 professors: List[Professor],
                 rooms: List[Room],
                 population_size: int = 200,
                 generations: int = 2000,
                 mutation_rate: float = 0.15,
                 crossover_rate: float = 0.8,
                 elite_size: int = 20,
                 diversity_threshold: float = 0.01,
                 stagnation_limit: int = 500):  # Reduced stagnation limit

        self.sections = sections
        self.subjects = subjects
        self.professors = professors
        self.rooms = rooms
        self.population_size = population_size
        self.generations = generations
        self.initial_mutation_rate = mutation_rate
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size
        self.diversity_threshold = diversity_threshold
        self.stagnation_limit = stagnation_limit

        # Anti-stagnation parameters
        self.stagnation_counter = 0
        self.last_best_fitness = 0.0
        self.restart_count = 0
        self.max_restarts = 3  # Maximum number of restarts
        self.diversity_injection_threshold = 25  # Inject diversity after this many stagnant generations


        # Population diversity tracking
        self.diversity_history = []
        self.fitness_plateau_count = 0

        # Multi-objective tracking
        self.pareto_front = []

        # Create lookup dictionaries
        self.subject_dict = {s.id: s for s in subjects}
        self.professor_dict = {p.id: p for p in professors}
        self.room_dict = {r.id: r for r in rooms}
        self.section_dict = {s.id: s for s in sections}

        # Available time slots
        self.time_slots = self._generate_time_slots()

        # Analyze scheduling constraints
        self._analyze_constraints()

    def _generate_time_slots(self) -> List[float]:
        """Generate available time slots"""
        slots = []
        # Morning slots: 7:00 AM to 12:00 PM
        for hour in range(7, 12):
            slots.extend([hour + 0.0, hour + 0.5])

        # Afternoon slots: 1:00 PM to 9:00 PM
        for hour in range(13, 21):
            slots.extend([hour + 0.0, hour + 0.5])

        return slots

    def _analyze_constraints(self):
        """Analyze scheduling constraints and bottlenecks"""
        print("\n=== CONSTRAINT ANALYSIS ===")

        # Analyze professor workload
        subject_professor_map = defaultdict(list)
        professor_subjects = defaultdict(set)

        for prof in self.professors:
            for subject_id in prof.subjects:
                subject_professor_map[subject_id].append(prof.id)
                professor_subjects[prof.id].add(subject_id)

        # Find bottleneck subjects (subjects with few qualified professors)
        bottlenecks = []
        unassigned_subjects = []  # Track subjects with no qualified professors

        for subject_id in [s.id for s in self.subjects]:
            professors = subject_professor_map[subject_id]
            if len(professors) == 0:
                unassigned_subjects.append(subject_id)
            elif len(professors) <= 2:  # Critical bottleneck
                bottlenecks.append((subject_id, len(professors), professors))

        print("UNASSIGNED SUBJECTS (no qualified professors):")
        for subject_id in unassigned_subjects:
            print(f"  {subject_id}: Will be assigned TBA")

        print("BOTTLENECK SUBJECTS (≤2 qualified professors):")
        for subject_id, count, profs in sorted(bottlenecks, key=lambda x: x[1]):
            print(f"  {subject_id}: {count} professors -> {profs}")

        # Calculate required vs available professor hours
        total_required_hours = 0
        professor_required_hours = defaultdict(float)

        for section in self.sections:
            for subject_id in section.subjects:
                subject = self.subject_dict[subject_id]
                total_subject_hours = sum(session.duration_hours for session in subject.sessions)
                total_required_hours += total_subject_hours

                # Assign to qualified professors
                qualified_profs = subject_professor_map[subject_id]
                if qualified_profs:
                    hours_per_prof = total_subject_hours / len(qualified_profs)
                    for prof_id in qualified_profs:
                        professor_required_hours[prof_id] += hours_per_prof

        print(f"\nTOTAL REQUIRED TEACHING HOURS: {total_required_hours:.1f}")
        print("PROFESSOR WORKLOAD ANALYSIS:")

        overloaded_profs = []
        for prof_id, hours in professor_required_hours.items():
            status = "OVERLOADED" if hours > 40 else "OK"
            if hours > 40:
                overloaded_profs.append((prof_id, hours))
            print(f"  {prof_id}: {hours:.1f} hours/week - {status}")

        if overloaded_profs:
            print("\nWARNING: Overloaded professors detected!")
            for prof_id, hours in sorted(overloaded_profs, key=lambda x: x[1], reverse=True):
                print(f"  {prof_id}: {hours:.1f} hours (exceeded by {hours - 40:.1f})")

        # Store analysis results
        self.bottleneck_subjects = [b[0] for b in bottlenecks]
        self.unassigned_subjects = unassigned_subjects
        self.subject_professor_map = subject_professor_map
        self.professor_workload = professor_required_hours

    def _calculate_population_diversity(self, population: List[Chromosome]) -> float:
        """Calculate population diversity using hamming distance"""
        if len(population) < 2:
            return 0.0

        total_distance = 0
        comparisons = 0

        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                distance = self._chromosome_distance(population[i], population[j])
                total_distance += distance
                comparisons += 1

        return total_distance / comparisons if comparisons > 0 else 0.0

    def _chromosome_distance(self, chrom1: Chromosome, chrom2: Chromosome) -> float:
        """Calculate normalized hamming distance between two chromosomes"""
        if len(chrom1.genes) != len(chrom2.genes):
            return 1.0

        differences = 0
        total_genes = len(chrom1.genes)

        for g1, g2 in zip(chrom1.genes, chrom2.genes):
            if (g1.professor_id != g2.professor_id or
                    g1.room_id != g2.room_id or
                    g1.day != g2.day or
                    abs(g1.start_time - g2.start_time) > 0.5):
                differences += 1

        return differences / total_genes if total_genes > 0 else 0.0

    def _inject_diversity(self, population: List[Chromosome]) -> List[Chromosome]:
        """Inject diversity by replacing worst performing chromosomes with new random ones"""
        print("  -> Injecting diversity to combat stagnation")

        # Sort population by fitness
        population.sort(key=lambda x: x.fitness, reverse=True)

        # Replace bottom 30% with new chromosomes
        replace_count = int(0.3 * len(population))

        # Keep top performers
        new_population = population[:-replace_count] if replace_count > 0 else population[:]

        # Add new random chromosomes
        for _ in range(replace_count):
            if random.random() < 0.5:
                new_chromosome = self.create_intelligent_chromosome()
            else:
                new_chromosome = self.create_random_chromosome()
            new_population.append(new_chromosome)

        # Add some heavily mutated versions of good chromosomes
        for i in range(min(5, len(population) // 4)):
            mutated = copy.deepcopy(population[i])
            # Apply heavy mutation
            old_mutation_rate = self.mutation_rate
            self.mutation_rate = 0.8  # High mutation rate
            for _ in range(3):  # Multiple mutations
                mutated = self.mutate(mutated)
            self.mutation_rate = old_mutation_rate
            new_population[-(i + 1)] = mutated

        return new_population

    def _adaptive_parameters(self, generation: int, population: List[Chromosome]):
        """Adapt parameters based on generation and population state"""
        # Adaptive mutation rate
        diversity = self._calculate_population_diversity(population)
        self.diversity_history.append(diversity)

        # Increase mutation rate if diversity is low
        if diversity < self.diversity_threshold:
            self.mutation_rate = min(0.5, self.initial_mutation_rate * 2)
        else:
            self.mutation_rate = max(0.05, self.initial_mutation_rate * 0.8)

    def _get_qualified_professors(self, subject_id: str, section_id: str) -> List[Professor]:
        """Get professors qualified to teach a specific subject"""

        return [p for p in self.professors if subject_id in p.subjects and self.section_dict[section_id].course in p.course]

    def _get_suitable_rooms(self, session_type: SessionType, course: str) -> List[Room]:
        """Get rooms suitable for a specific session type and course"""
        suitable_rooms = []

        for room in self.rooms:
            if room.room_type == session_type:
                if room.preferred_courses is None or course in room.preferred_courses:

                    suitable_rooms.append(room)
        return suitable_rooms

    def _find_valid_start_time(self, duration: float, exclude_times: Set[Tuple[Day, float]] = None) -> float:
        """Find a valid start time avoiding conflicts"""
        valid_times = []

        for start_time in self.time_slots:
            end_time = start_time + duration
            # Check lunch break conflict
            if start_time < 13.0 and end_time > 12.0:
                continue
            if end_time > 21.0:
                continue

            # Check excluded times if provided
            if exclude_times:
                conflict = False
                for day, excluded_time in exclude_times:
                    if abs(start_time - excluded_time) < duration:
                        conflict = True
                        break
                if conflict:
                    continue

            valid_times.append(start_time)

        return random.choice(valid_times) if valid_times else 7.0

    def _check_professor_conflicts(self, genes: List[Gene]) -> Dict[str, List[Tuple[Gene, Gene]]]:
        """Check for professor time conflicts (skip genes with None/TBA professors)"""
        conflicts = defaultdict(list)
        prof_schedule = defaultdict(list)

        # Group genes by professor (skip None/TBA professors)
        for gene in genes:
            if gene.professor_id and gene.professor_id != "TBA":
                prof_schedule[gene.professor_id].append(gene)

        # Check for overlapping times
        for prof_id, prof_genes in prof_schedule.items():
            for i, gene1 in enumerate(prof_genes):
                for gene2 in prof_genes[i + 1:]:
                    if gene1.day == gene2.day:
                        # Check time overlap
                        if (gene1.start_time < gene2.end_time and
                                gene2.start_time < gene1.end_time):
                            conflicts[prof_id].append((gene1, gene2))

        return conflicts

    def _resolve_professor_conflicts(self, chromosome: Chromosome) -> Chromosome:
        """Resolve professor scheduling conflicts"""
        conflicts = self._check_professor_conflicts(chromosome.genes)

        if not conflicts:
            return chromosome

        # Resolve conflicts by adjusting times or reassigning professors
        for prof_id, conflict_pairs in conflicts.items():
            for gene1, gene2 in conflict_pairs:
                # Try to reschedule one of the conflicting genes
                if random.random() < 0.5:
                    target_gene = gene1
                else:
                    target_gene = gene2

                # Get other genes for this professor on same day
                same_day_genes = [g for g in chromosome.genes
                                  if g.professor_id == prof_id and g.day == target_gene.day]

                occupied_times = {(g.day, g.start_time) for g in same_day_genes if g != target_gene}

                # Try to find new time
                new_start_time = self._find_valid_start_time(target_gene.duration, occupied_times)
                target_gene.start_time = new_start_time

        return chromosome

    def create_intelligent_chromosome(self) -> Chromosome:
        """Create chromosome with conflict-aware scheduling"""
        genes = []
        professor_schedule = defaultdict(list)  # Track professor assignments
        room_schedule = defaultdict(list)  # Track room assignments

        # Group required sessions by section
        section_sessions = defaultdict(list)
        for section in self.sections:
            for subject_id in section.subjects:
                subject = self.subject_dict[subject_id]
                for session_template in subject.sessions:
                    section_sessions[section.id].append((subject_id, session_template))

        # Schedule sessions with conflict awareness
        for section in self.sections:
            sessions = section_sessions[section.id]

            # Prioritize bottleneck subjects first
            bottleneck_sessions = []
            regular_sessions = []

            for subject_id, session_template in sessions:
                if subject_id in self.bottleneck_subjects:
                    bottleneck_sessions.append((subject_id, session_template))
                else:
                    regular_sessions.append((subject_id, session_template))

            # Schedule bottleneck subjects first
            all_sessions = bottleneck_sessions + regular_sessions

            for subject_id, session_template in all_sessions:
                # Get qualified professors
                qualified_profs = self._get_qualified_professors(subject_id, section.id)

                # Select professor (or TBA if none available)
                if qualified_profs:
                    best_prof = self._select_best_professor(qualified_profs, professor_schedule)
                    professor_id = best_prof.id
                else:
                    professor_id = "TBA"  # No qualified professor found

                # Select room if needed
                room_id = None
                if self.subject_dict[subject_id].requires_room:
                    suitable_rooms = self._get_suitable_rooms(
                        session_template.session_type, section.course)
                    if suitable_rooms:
                        room_id = self._select_best_room(suitable_rooms, room_schedule)

                # Select best time slot
                if professor_id != "TBA":
                    day, start_time = self._select_best_time_slot(
                        professor_id, room_id, session_template.duration_hours,
                        professor_schedule, room_schedule
                    )
                else:
                    # For TBA professors, just find any valid time slot
                    day, start_time = self._select_any_valid_time_slot(
                        room_id, session_template.duration_hours, room_schedule
                    )

                gene = Gene(
                    section_id=section.id,
                    subject_id=subject_id,
                    session_number=session_template.session_number,
                    session_type=session_template.session_type,
                    professor_id=professor_id,
                    room_id=room_id,
                    day=day,
                    start_time=start_time,
                    duration=session_template.duration_hours
                )

                genes.append(gene)

                # Update schedules (only track actual professors, not TBA)
                if professor_id != "TBA":
                    professor_schedule[professor_id].append(
                        (day, start_time, start_time + session_template.duration_hours))
                if room_id:
                    room_schedule[room_id].append((day, start_time, start_time + session_template.duration_hours))

        return Chromosome(genes)

    def _select_any_valid_time_slot(self, room_id: Optional[str], duration: float,
                                    room_schedule: Dict) -> Tuple[Day, float]:
        """Select any valid time slot (used for TBA professors)"""
        room_occupied = set()

        if room_id:
            for day, start, end in room_schedule.get(room_id, []):
                for t in self.time_slots:
                    if start <= t < end:
                        room_occupied.add((day, t))

        # Find free slots
        free_slots = []
        for day in Day:
            for start_time in self.time_slots:
                end_time = start_time + duration

                # Check basic validity
                if start_time < 13.0 and end_time > 12.0:  # Lunch conflict
                    continue
                if end_time > 21.0:  # Too late
                    continue

                # Check room conflicts only
                conflict = False
                if room_id:
                    for t in self.time_slots:
                        if start_time <= t < end_time:
                            if (day, t) in room_occupied:
                                conflict = True
                                break

                if not conflict:
                    free_slots.append((day, start_time))

        if free_slots:
            return random.choice(free_slots)
        else:
            # Fallback to any valid time
            return random.choice(list(Day)), self._find_valid_start_time(duration)

    def _select_best_professor(self, qualified_profs: List[Professor], professor_schedule: Dict) -> Professor:
        """Select professor with least scheduling conflicts"""
        prof_loads = []
        for prof in qualified_profs:
            current_load = len(professor_schedule.get(prof.id, []))
            prof_loads.append((current_load, prof))

        # Select professor with lightest load (with some randomness)
        prof_loads.sort(key=lambda x: x[0])

        # Choose from top 50% least loaded professors
        top_half = prof_loads[:max(1, len(prof_loads) // 2)]
        return random.choice(top_half)[1]

    def _select_best_room(self, suitable_rooms: List[Room], room_schedule: Dict) -> str:
        """Select room with least conflicts"""
        room_loads = []
        for room in suitable_rooms:
            current_load = len(room_schedule.get(room.id, []))
            room_loads.append((current_load, room.id))

        room_loads.sort(key=lambda x: x[0])
        top_half = room_loads[:max(1, len(room_loads) // 2)]
        return random.choice(top_half)[1]

    def _select_best_time_slot(self, prof_id: str, room_id: str, duration: float,
                               professor_schedule: Dict, room_schedule: Dict) -> Tuple[Day, float]:
        """Select best time slot avoiding conflicts"""
        prof_occupied = set()
        room_occupied = set()

        # Get occupied times
        for day, start, end in professor_schedule.get(prof_id, []):
            for t in self.time_slots:
                if start <= t < end:
                    prof_occupied.add((day, t))

        if room_id:
            for day, start, end in room_schedule.get(room_id, []):
                for t in self.time_slots:
                    if start <= t < end:
                        room_occupied.add((day, t))

        # Find free slots
        free_slots = []
        for day in Day:
            for start_time in self.time_slots:
                end_time = start_time + duration

                # Check basic validity
                if start_time < 13.0 and end_time > 12.0:  # Lunch conflict
                    continue
                if end_time > 21.0:  # Too late
                    continue

                # Check conflicts
                conflict = False
                for t in self.time_slots:
                    if start_time <= t < end_time:
                        if (day, t) in prof_occupied or (day, t) in room_occupied:
                            conflict = True
                            break

                if not conflict:
                    free_slots.append((day, start_time))

        if free_slots:
            return random.choice(free_slots)
        else:
            # Fallback to any valid time
            return random.choice(list(Day)), self._find_valid_start_time(duration)

    def create_random_chromosome(self) -> Chromosome:
        """Create a random chromosome (fallback method)"""
        genes = []

        for section in self.sections:
            for subject_id in section.subjects:
                subject = self.subject_dict[subject_id]

                for session_template in subject.sessions:
                    qualified_profs = self._get_qualified_professors(subject_id, section.id)

                    # Use TBA if no qualified professors found
                    if qualified_profs:
                        professor_id = random.choice(qualified_profs).id
                    else:
                        professor_id = "TBA"

                    room_id = None
                    if subject.requires_room:
                        suitable_rooms = self._get_suitable_rooms(
                            session_template.session_type, section.course)
                        if suitable_rooms:
                            room_id = random.choice(suitable_rooms).id

                    day = random.choice(list(Day))
                    start_time = self._find_valid_start_time(session_template.duration_hours)

                    gene = Gene(
                        section_id=section.id,
                        subject_id=subject_id,
                        session_number=session_template.session_number,
                        session_type=session_template.session_type,
                        professor_id=professor_id,
                        room_id=room_id,
                        day=day,
                        start_time=start_time,
                        duration=session_template.duration_hours
                    )
                    genes.append(gene)

        return Chromosome(genes)

    def initialize_population(self) -> List[Chromosome]:
        """Initialize population with mix of intelligent and random chromosomes"""
        population = []

        # 70% intelligent chromosomes, 30% random for diversity
        intelligent_count = int(0.7 * self.population_size)

        print(f"Creating {intelligent_count} intelligent chromosomes...")
        for i in range(intelligent_count):
            try:
                chromosome = self.create_intelligent_chromosome()
                chromosome = self._repair_chromosome(chromosome)
                population.append(chromosome)
            except Exception as e:
                print(f"Failed to create intelligent chromosome {i}: {e}")
                population.append(self.create_random_chromosome())

        print(f"Creating {self.population_size - intelligent_count} random chromosomes...")
        for _ in range(self.population_size - intelligent_count):
            population.append(self.create_random_chromosome())

        return population

    def tournament_selection(self, population: List[Chromosome], tournament_size: int = 7) -> Chromosome:
        """Standard tournament selection without temperature-based pressure"""
        tournament = random.sample(population, min(tournament_size, len(population)))
        return max(tournament, key=lambda x: x.fitness)

    def crossover(self, parent1: Chromosome, parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """Multi-point crossover with conflict resolution"""
        if random.random() > self.crossover_rate:
            return copy.deepcopy(parent1), copy.deepcopy(parent2)

        # Use multiple crossover points for better mixing
        gene_count = min(len(parent1.genes), len(parent2.genes))
        num_points = random.randint(2, min(5, gene_count // 10 + 1))
        crossover_points = sorted(random.sample(range(1, gene_count), num_points))

        child1_genes = []
        child2_genes = []

        start_idx = 0
        for i, point in enumerate(crossover_points + [gene_count]):
            if i % 2 == 0:
                child1_genes.extend(parent1.genes[start_idx:point])
                child2_genes.extend(parent2.genes[start_idx:point])
            else:
                child1_genes.extend(parent2.genes[start_idx:point])
                child2_genes.extend(parent1.genes[start_idx:point])
            start_idx = point

        child1 = self._repair_chromosome(Chromosome(child1_genes))
        child2 = self._repair_chromosome(Chromosome(child2_genes))

        # Resolve conflicts
        child1 = self._resolve_professor_conflicts(child1)
        child2 = self._resolve_professor_conflicts(child2)

        return child1, child2

    def _repair_chromosome(self, chromosome: Chromosome) -> Chromosome:
        """Comprehensive chromosome repair ensuring all hard constraints are met"""
        # Make a copy to work on
        repaired = copy.deepcopy(chromosome)

        # Repair in multiple passes with increasingly aggressive repairs
        for attempt in range(3):  # Try up to 3 times
            # First ensure all required sessions exist
            repaired = self._ensure_all_sessions_exist(repaired)

            # Repair hard constraints in order of importance
            repaired = self._repair_professor_conflicts(repaired)
            repaired = self._repair_room_conflicts(repaired)
            repaired = self._repair_section_conflicts(repaired)
            repaired = self._repair_time_window_violations(repaired)
            repaired = self._repair_same_subject_same_day(repaired)

            # Early exit if we have a valid chromosome
            if self._is_valid_chromosome(repaired):
                break

        return repaired

    def _is_valid_chromosome(self, chromosome: Chromosome) -> bool:
        """Check if chromosome meets all hard constraints"""
        temp_chrom = Chromosome(chromosome.genes)
        penalty = 0
        penalty += 100 * temp_chrom._check_professor_conflicts()
        penalty += 100 * temp_chrom._check_room_conflicts()
        penalty += 100 * temp_chrom._check_section_conflicts()
        penalty += 100 * temp_chrom._check_time_window()
        penalty += 100 * temp_chrom._check_same_subject_same_day()
        return penalty == 0

    def _create_gene_for_session(self, section_id: str, subject_id: str, session_template: SessionTemplate) -> Gene:
        """Create a gene for a specific session"""
        section = next(s for s in self.sections if s.id == section_id)

        qualified_profs = self._get_qualified_professors(subject_id, section.id)

        # Use TBA if no qualified professors found
        if qualified_profs:
            professor_id = random.choice(qualified_profs).id
        else:
            professor_id = "TBA"

        room_id = None
        if self.subject_dict[subject_id].requires_room:
            suitable_rooms = self._get_suitable_rooms(session_template.session_type, section.course)
            if suitable_rooms:
                room_id = random.choice(suitable_rooms).id

        day = random.choice(list(Day))
        start_time = self._find_valid_start_time(session_template.duration_hours)

        return Gene(
            section_id=section_id,
            subject_id=subject_id,
            session_number=session_template.session_number,
            session_type=session_template.session_type,
            professor_id=professor_id,
            room_id=room_id,
            day=day,
            start_time=start_time,
            duration=session_template.duration_hours
        )
    def mutate(self, chromosome: Chromosome) -> Chromosome:
        """Enhanced mutation with conflict resolution"""
        if random.random() > self.mutation_rate:
            return chromosome

        mutated_chromosome = copy.deepcopy(chromosome)

        if mutated_chromosome.genes:
            gene_idx = random.randint(0, len(mutated_chromosome.genes) - 1)
            gene = mutated_chromosome.genes[gene_idx]

            mutation_type = random.choice(['professor', 'room', 'time', 'day'])

            if mutation_type == 'professor' and gene.professor_id != "TBA":
                qualified_profs = self._get_qualified_professors(gene.subject_id, gene.section_id)
                if len(qualified_profs) > 1:  # Only mutate if alternatives exist
                    current_prof = gene.professor_id
                    alternatives = [p for p in qualified_profs if p.id != current_prof]
                    if alternatives:
                        gene.professor_id = random.choice(alternatives).id

            elif mutation_type == 'room' and gene.room_id:
                section = next(s for s in self.sections if s.id == gene.section_id)
                suitable_rooms = self._get_suitable_rooms(gene.session_type, section.course)
                if len(suitable_rooms) > 1:
                    alternatives = [r for r in suitable_rooms if r.id != gene.room_id]
                    if alternatives:
                        gene.room_id = random.choice(alternatives).id

            elif mutation_type == 'time':
                gene.start_time = self._find_valid_start_time(gene.duration)

            elif mutation_type == 'day':
                gene.day = random.choice(list(Day))

        # Resolve conflicts after mutation
        mutated_chromosome = self._resolve_professor_conflicts(mutated_chromosome)
        return self._repair_chromosome(mutated_chromosome)

    def evaluate_population(self, population: List[Chromosome]) -> None:
        """Evaluate fitness for all chromosomes"""
        for chromosome in population:
            chromosome.calculate_fitness(None)

    def get_elite(self, population: List[Chromosome]) -> List[Chromosome]:
        """Get elite chromosomes"""
        sorted_population = sorted(population, key=lambda x: x.fitness, reverse=True)
        return sorted_population[:self.elite_size]

    def evolve(self) -> Tuple[Chromosome, List[float]]:
        """Main evolution loop with 5000 generation termination only"""
        print("Initializing conflict-aware population...")
        population = self.initialize_population()

        print("Starting evolution...")
        fitness_history = []
        best_chromosome = None
        best_fitness = 0.0
        generation_of_last_improvement = 0

        # New variables for fitness improvement tracking
        fitness_improvement_window = 100  # Check improvement over last 100 generations
        min_improvement_threshold = 0.002  # Minimum improvement required

        # Set generations to 5000
        max_generations = 10000

        for generation in range(max_generations):
            self.evaluate_population(population)

            current_best = max(population, key=lambda x: x.fitness)
            current_best_fitness = current_best.fitness

            # Update best if we found a better solution
            if current_best_fitness > best_fitness:
                best_fitness = current_best_fitness
                best_chromosome = copy.deepcopy(current_best)
                generation_of_last_improvement = generation
                self.stagnation_counter = 0
                print(f"  -> New best fitness: {best_fitness:.4f} at generation {generation}")
            else:
                self.stagnation_counter += 1

            fitness_history.append(best_fitness)

            if best_fitness > 0.9:
                print(f"Evolution terminated: Maximum generations ({max_generations}) reached")
                print(f"Final fitness: {best_fitness:.4f} at generation {generation}")
                break

            if generation % 50 == 0:
                avg_fitness = sum(c.fitness for c in population) / len(population)
                print(f"Gen {generation}: Best={best_fitness:.4f}, Avg={avg_fitness:.4f}, "
                      f"Current={current_best_fitness:.4f}")

            # Check for fitness improvement termination condition
            if generation >= fitness_improvement_window:
                fitness_100_gens_ago = fitness_history[generation - fitness_improvement_window]
                fitness_improvement = best_fitness - fitness_100_gens_ago

                if fitness_improvement < min_improvement_threshold:
                    print(f"Evolution terminated: Fitness improved by only {fitness_improvement:.6f} "
                          f"in the last {fitness_improvement_window} generations "
                          f"(threshold: {min_improvement_threshold})")
                    print(f"Final fitness: {best_fitness:.4f} at generation {generation}")
                    break

            # ONLY other termination condition: Maximum generations reached
            if generation >= max_generations - 1:
                print(f"Evolution terminated: Maximum generations ({max_generations}) reached")
                print(f"Final fitness: {best_fitness:.4f} at generation {generation}")
                break

            # Handle stagnation with restart limits (keeping this as it doesn't terminate evolution)
            if self.stagnation_counter >= self.stagnation_limit and best_fitness < 0.7:
                self.restart_count += 1

                if self.restart_count >= self.max_restarts:
                    print(
                        f"  -> Maximum restarts ({self.max_restarts}) reached. Continuing evolution without restarts.")
                    # Continue evolution instead of breaking
                    self.stagnation_counter = 0  # Reset to avoid constant restart attempts

                else:
                    print(f"  -> Restart {self.restart_count}/{self.max_restarts} due to stagnation")

                    # Create new population but keep some elite from the best ever found
                    new_population = []

                    # Keep the absolute best chromosome
                    if best_chromosome:
                        new_population.append(copy.deepcopy(best_chromosome))

                        # Add some mutated versions of the best chromosome
                        for _ in range(min(5, self.elite_size)):
                            mutated_best = copy.deepcopy(best_chromosome)
                            old_mutation_rate = self.mutation_rate
                            self.mutation_rate = 0.3  # Higher mutation for diversity
                            for _ in range(2):  # Multiple mutations
                                mutated_best = self.mutate(mutated_best)
                            self.mutation_rate = old_mutation_rate
                            new_population.append(mutated_best)

                    # Fill the rest with new chromosomes
                    while len(new_population) < self.population_size:
                        if random.random() < 0.7:
                            new_population.append(self.create_intelligent_chromosome())
                        else:
                            new_population.append(self.create_random_chromosome())

                    population = new_population
                    self.stagnation_counter = 0

                    # Reset adaptive parameters
                    self.mutation_rate = self.initial_mutation_rate

                    continue

            # Inject diversity if stagnating but not ready for full restart
            if self.stagnation_counter > 0 and self.stagnation_counter % self.diversity_injection_threshold == 0:
                population = self._inject_diversity(population)

            # Adaptive parameters
            self._adaptive_parameters(generation, population)

            # Create new population
            new_population = []
            elite = self.get_elite(population)
            new_population.extend(copy.deepcopy(elite))

            # Generate offspring
            while len(new_population) < self.population_size:
                parent1 = self.tournament_selection(population)
                parent2 = self.tournament_selection(population)
                child1, child2 = self.crossover(parent1, parent2)
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)
                new_population.extend([child1, child2])

            population = new_population[:self.population_size]

        print(f"Evolution completed. Best fitness: {best_fitness:.4f}")
        print(f"Best solution found at generation: {generation_of_last_improvement}")
        print(f"Total restarts used: {self.restart_count}/{self.max_restarts}")

        return best_chromosome, fitness_history

    def _repair_chromosome(self, chromosome: Chromosome) -> Chromosome:
        """Repair chromosome ensuring all hard constraints are met"""
        # Make a copy to work on
        repaired = copy.deepcopy(chromosome)

        # First ensure all required sessions exist
        repaired = self._ensure_all_sessions_exist(repaired)

        # Repair hard constraints in order of importance
        repaired = self._repair_professor_conflicts(repaired)
        repaired = self._repair_room_conflicts(repaired)
        repaired = self._repair_section_conflicts(repaired)
        repaired = self._repair_time_window_violations(repaired)
        repaired = self._repair_same_subject_same_day(repaired)

        return repaired

    def _ensure_all_sessions_exist(self, chromosome: Chromosome) -> Chromosome:
        """Ensure all required sessions exist in the chromosome"""
        # Group by section-subject
        section_subject_genes = defaultdict(list)
        for gene in chromosome.genes:
            key = (gene.section_id, gene.subject_id)
            section_subject_genes[key].append(gene)

        repaired_genes = []

        # Ensure all required sessions exist
        for section in self.sections:
            for subject_id in section.subjects:
                subject = self.subject_dict[subject_id]
                key = (section.id, subject_id)
                existing_genes = section_subject_genes.get(key, [])

                for session_template in subject.sessions:
                    matching_genes = [g for g in existing_genes
                                      if g.session_number == session_template.session_number]

                    if matching_genes:
                        repaired_genes.append(matching_genes[0])
                    else:
                        # Create missing gene
                        new_gene = self._create_gene_for_session(
                            section.id, subject_id, session_template)
                        repaired_genes.append(new_gene)

        return Chromosome(repaired_genes)

    def _repair_professor_conflicts(self, chromosome: Chromosome) -> Chromosome:
        """Resolve professor scheduling conflicts while handling None/TBA cases"""
        # Create a copy to modify
        repaired = copy.deepcopy(chromosome)

        # First filter out genes we shouldn't process
        processable_genes = [
            gene for gene in repaired.genes
            if gene.professor_id and gene.professor_id != "TBA"
        ]

        # Track professor schedules only for processable genes
        prof_schedule = defaultdict(list)
        for gene in processable_genes:
            prof_schedule[gene.professor_id].append(gene)

        # Find all conflicts among processable genes
        conflicts = defaultdict(list)
        for i, gene1 in enumerate(processable_genes):
            for gene2 in processable_genes[i + 1:]:
                if (gene1.professor_id == gene2.professor_id and
                        gene1.day == gene2.day and
                        gene1.overlaps_with(gene2)):
                    conflicts[gene1.professor_id].append((gene1, gene2))

        # Resolve each conflict
        for prof_id, conflict_pairs in conflicts.items():
            for gene1, gene2 in conflict_pairs:
                # Skip if genes were already modified
                if gene1 not in repaired.genes or gene2 not in repaired.genes:
                    continue

                # We'll modify gene2 (arbitrary choice)
                idx = repaired.genes.index(gene2)

                # Find occupied times for this professor (excluding gene2)
                occupied_times = {
                    (g.day, g.start_time)
                    for g in prof_schedule[prof_id]
                    if g != gene2 and g in repaired.genes
                }

                # Try to find a new time
                try:
                    new_day = random.choice(list(Day))
                    new_start = self._find_valid_start_time(
                        gene2.duration, occupied_times)

                    # Update the gene
                    repaired.genes[idx].day = new_day
                    repaired.genes[idx].start_time = new_start

                    # Update the professor's schedule tracking
                    if gene2 in prof_schedule[prof_id]:
                        prof_schedule[prof_id].remove(gene2)
                    gene_copy = copy.copy(repaired.genes[idx])
                    prof_schedule[prof_id].append(gene_copy)

                except (ValueError, IndexError):
                    # Fallback 1: Try assigning a different professor
                    qualified_profs = self._get_qualified_professors(gene2.subject_id, gene2.section_id)
                    if qualified_profs and len(qualified_profs) > 1:
                        alternatives = [
                            p for p in qualified_profs
                            if p.id != gene2.professor_id
                        ]
                        if alternatives:
                            repaired.genes[idx].professor_id = random.choice(alternatives).id
                            continue

                    # Fallback 2: Mark as TBA if no alternatives
                    repaired.genes[idx].professor_id = "TBA"

        return repaired

    def _repair_room_conflicts(self, chromosome: Chromosome) -> Chromosome:
        """Resolve room scheduling conflicts"""
        # Group genes by room and day
        room_day_genes = defaultdict(list)
        for gene in chromosome.genes:
            if gene.room_id:
                key = (gene.room_id, gene.day)
                room_day_genes[key].append(gene)

        # Check for conflicts
        repaired = copy.deepcopy(chromosome)
        for (room_id, day), genes in room_day_genes.items():
            # Sort by start time
            genes_sorted = sorted(genes, key=lambda g: g.start_time)

            for i in range(len(genes_sorted) - 1):
                gene1 = genes_sorted[i]
                gene2 = genes_sorted[i + 1]

                if gene1.overlaps_with(gene2):
                    # Conflict found - try to move gene2
                    idx = repaired.genes.index(gene2)

                    # Find alternative room if possible
                    section = next(s for s in self.sections if s.id == gene2.section_id)
                    suitable_rooms = self._get_suitable_rooms(
                        gene2.session_type, section.course)

                    if suitable_rooms:
                        # Try to find a room without conflict at this time
                        for room in suitable_rooms:
                            if room.id == room_id:
                                continue

                            # Check if room is available
                            conflicting = False
                            for other_gene in repaired.genes:
                                if (other_gene.room_id == room.id and
                                        other_gene.day == day and
                                        other_gene.overlaps_with(gene2)):
                                    conflicting = True
                                    break

                            if not conflicting:
                                repaired.genes[idx].room_id = room.id
                                break

                    # If couldn't find alternative room, move the time
                    if repaired.genes[idx].room_id == room_id:
                        occupied_times = {(g.day, g.start_time)
                                          for g in repaired.genes
                                          if g.room_id == room_id and g != gene2}
                        new_start = self._find_valid_start_time(
                            gene2.duration, occupied_times)
                        repaired.genes[idx].start_time = new_start

        return repaired

    def _repair_section_conflicts(self, chromosome: Chromosome) -> Chromosome:
        """Resolve section scheduling conflicts (same section having overlapping classes)"""
        # Group genes by section and day
        section_day_genes = defaultdict(list)
        for gene in chromosome.genes:
            key = (gene.section_id, gene.day)
            section_day_genes[key].append(gene)

        repaired = copy.deepcopy(chromosome)

        for (section_id, day), genes in section_day_genes.items():
            # Sort by start time
            genes_sorted = sorted(genes, key=lambda g: g.start_time)

            for i in range(len(genes_sorted) - 1):
                gene1 = genes_sorted[i]
                gene2 = genes_sorted[i + 1]

                if gene1.overlaps_with(gene2):
                    # Conflict found - try to move gene2 to a different time
                    idx = repaired.genes.index(gene2)

                    # Find all times already taken by this section on this day
                    occupied_times = {(g.day, g.start_time)
                                      for g in section_day_genes[(section_id, day)]
                                      if g != gene2}

                    new_start = self._find_valid_start_time(
                        gene2.duration, occupied_times)
                    repaired.genes[idx].start_time = new_start

        return repaired

    def _repair_time_window_violations(self, chromosome: Chromosome) -> Chromosome:
        """Ensure all classes are within allowed time window (7:00-21:00)"""
        repaired = copy.deepcopy(chromosome)

        for i, gene in enumerate(repaired.genes):
            if gene.start_time < 7.0 or gene.start_time > 21.0:
                # Find a valid time
                occupied_times = {(g.day, g.start_time)
                                  for g in repaired.genes
                                  if g != gene and g.professor_id == gene.professor_id}
                new_start = self._find_valid_start_time(gene.duration, occupied_times)
                repaired.genes[i].start_time = new_start

        return repaired

    def _repair_same_subject_same_day(self, chromosome: Chromosome) -> Chromosome:
        """Ensure same subject isn't scheduled multiple times on same day for a section"""
        repaired = copy.deepcopy(chromosome)

        # Track subjects per section per day
        section_day_subjects = defaultdict(set)
        to_reschedule = []

        # First pass: identify conflicts
        for i, gene in enumerate(repaired.genes):
            key = (gene.section_id, gene.day)
            if gene.subject_id in section_day_subjects[key]:
                to_reschedule.append(i)
            else:
                section_day_subjects[key].add(gene.subject_id)

        # Second pass: reschedule conflicting genes
        for idx in to_reschedule:
            gene = repaired.genes[idx]

            # Find a different day that doesn't have this subject for this section
            possible_days = []
            for day in Day:
                if day == gene.day:
                    continue
                if gene.subject_id not in section_day_subjects[(gene.section_id, day)]:
                    possible_days.append(day)

            if possible_days:
                # Choose a random valid day
                new_day = random.choice(possible_days)

                # Find a valid time on the new day
                occupied_times = {(g.day, g.start_time)
                                  for g in repaired.genes
                                  if g.day == new_day and
                                  (g.professor_id == gene.professor_id or
                                   g.room_id == gene.room_id)}

                new_start = self._find_valid_start_time(
                    gene.duration, occupied_times)

                # Update the gene
                repaired.genes[idx].day = new_day
                repaired.genes[idx].start_time = new_start

                # Update our tracking
                section_day_subjects[(gene.section_id, new_day)].add(gene.subject_id)

        return repaired

    def print_schedule(self, chromosome: Chromosome) -> None:
        """Print the schedule organized by section in a readable format, including penalty breakdown"""
        if not chromosome:
            print("No valid schedule found")
            return

        # Calculate penalty breakdown
        penalty = 0
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

        print(f"\n=== SCHEDULE SUMMARY ===")
        print(f"Fitness: {chromosome.fitness:.4f}")
        print(f"Total Penalty: {total_penalty}")
        print("\n=== PENALTY BREAKDOWN ===")
        for constraint, value in penalty_breakdown.items():
            print(f"{constraint.replace('_', ' ').title():<25}: {value}")

        print("\n=== DETAILED SCHEDULE BY SECTION ===")

        # Track TBA assignments
        tba_subjects = set()

        # Group genes by section
        schedule_by_section = defaultdict(list)
        for gene in chromosome.genes:
            schedule_by_section[gene.section_id].append(gene)
            if gene.professor_id == "TBA":
                tba_subjects.add(gene.subject_id)

        # Sort and print by section
        for section_id in sorted(schedule_by_section.keys()):
            print(f"\n--- Section {section_id} ---")

            # Sort by day and then by time
            section_genes = sorted(schedule_by_section[section_id],
                                   key=lambda g: (g.day.value, g.start_time))

            for gene in section_genes:
                start_time = f"{int(gene.start_time):02d}:{int((gene.start_time % 1) * 60):02d}"
                end_time = f"{int(gene.end_time):02d}:{int((gene.end_time % 1) * 60):02d}"
                room_info = f"Room: {gene.room_id}" if gene.room_id else "Online"

                prof_display = gene.professor_id if gene.professor_id != "TBA" else "TBA (No qualified professor)"

                print(f"  {gene.day.name} | {start_time}-{end_time} | {gene.subject_id} "
                      f"({gene.session_number}) | Prof: {prof_display} | {room_info}")

        # Summary of TBA assignments
        if tba_subjects:
            print(f"\n=== SUBJECTS REQUIRING PROFESSOR ASSIGNMENT ===")
            print("The following subjects have been scheduled but need professors to be assigned:")
            for subject_id in sorted(tba_subjects):
                print(f"  - {subject_id}")
            print(f"Total subjects needing professors: {len(tba_subjects)}")