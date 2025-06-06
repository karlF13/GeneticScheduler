import random
from typing import List, Optional

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

        # Valid time slots hahah di ko pa sure kasi kung pano
        # self.valid_time_slots = [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5,
        #                          13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0]

        self.valid_time_slots = [7.0, 8.0, 9.0, 10.0, 11.0 ,12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0]

        self.genome_length = self._calculate_genome_length()

    def _calculate_genome_length(self) -> int:
        total_sessions = 0
        for section in self.sections:
            for subject_id in section.subjects:
                subject = self.subject_dict[subject_id]
                total_sessions += len(subject.sessions)
        return total_sessions

    def create_smart_chromosome(self) -> Chromosome:

        genes = []
        conflict_tracker = ConflictTracker()

        # Collect all sessions that need to be scheduled
        sessions_to_schedule = []
        for section in self.sections:
            for subject_id in section.subjects:
                subject = self.subject_dict[subject_id]
                for session_template in subject.sessions:
                    sessions_to_schedule.append((section, subject_id, session_template))

        # Sort by duration (longer sessions first - harder to place)
        sessions_to_schedule.sort(key=lambda x: x[2].duration_hours, reverse=True)

        for section, subject_id, session_template in sessions_to_schedule:
            gene = self._create_conflict_free_gene(
                section, subject_id, session_template, conflict_tracker
            )
            if gene:
                genes.append(gene)
                conflict_tracker.add_gene(gene)
            else:
                # Fallback to random if no conflict-free slot found
                gene = self._create_random_gene(section, subject_id, session_template)
                genes.append(gene)

        return Chromosome(genes)

    def _create_conflict_free_gene(self, section: Section, subject_id: str,
                                   session_template: SessionTemplate,
                                   conflict_tracker: ConflictTracker) -> Optional[Gene]:
        """Try to create a gene without conflicts"""

        # Get eligible professors
        eligible_professors = [p for p in self.professors if subject_id in p.subjects]
        if not eligible_professors:
            return None

        # Get eligible rooms
        eligible_rooms = [r for r in self.rooms
                          if r.room_type == session_template.session_type]

        # Try different combinations
        attempts = 0
        max_attempts = 100

        while attempts < max_attempts:
            professor = random.choice(eligible_professors)
            room_id = None
            if eligible_rooms:
                room_id = random.choice(eligible_rooms).id

            day = random.choice(list(Day))

            # Find valid start times for this duration
            valid_starts = []
            for start_time in self.valid_time_slots:
                # Only allow start times at 7, 8, 9, 10, or 11
                if start_time not in [7.0, 8.0, 9.0, 10.0, 11.0, 12, 13, 14, 15, 16, 18, 19]:
                    continue

                end_time = start_time + session_template.duration_hours

                if end_time <= 19.0:  # Don't go too late
                    # Check if it crosses lunch break
                    if not (start_time < 13.0 and end_time > 12.0):
                        valid_starts.append(start_time)

            if not valid_starts:
                attempts += 1
                continue

            start_time = random.choice(valid_starts)

            gene = Gene(
                section_id=section.id,
                subject_id=subject_id,
                session_number=session_template.session_number,
                session_type = session_template.session_type,
                professor_id=professor.id,
                room_id=room_id,
                day=day,
                start_time=start_time,
                duration=session_template.duration_hours
            )

            if conflict_tracker.is_available(gene):
                return gene

            attempts += 1

        return None  # No conflict-free slot found

    def _create_random_gene(self, section: Section, subject_id: str,
                            session_template: SessionTemplate) -> Gene:
        """Fallback random gene creation"""
        eligible_professors = [p for p in self.professors if subject_id in p.subjects]
        professor = random.choice(eligible_professors)

        room_id = None

        eligible_rooms = [r for r in self.rooms
                          if r.room_type == session_template.session_type]
        if eligible_rooms:
            room_id = random.choice(eligible_rooms).id

        day = random.choice(list(Day))
        start_time = random.choice([7.0, 8.0, 9.0, 10.0, 11.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0])

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
        for section in self.sections:
            for subject_id in section.subjects:
                subject = self.subject_dict[subject_id]
                for session_template in subject.sessions:
                    gene = self._create_random_gene(section, subject_id, session_template)
                    genes.append(gene)

        return Chromosome(genes)

    def initialize_population(self) -> List[Chromosome]:
        population = []

        # Create 30% smart chromosomes, 70% random
        # too random, harder to evolve; too perfect, might get stuck in local optima
        smart_count = int(0.3 * self.population_size)

        for _ in range(smart_count):
            population.append(self.create_smart_chromosome())

        for _ in range(self.population_size - smart_count):
            population.append(self.create_random_chromosome())

        return population

    def smart_mutate(self, chromosome: Chromosome) -> Chromosome:
        """Enhanced mutation with swap operations"""
        for i, gene in enumerate(chromosome.genes):
            if random.random() < self.mutation_rate:
                mutation_type = random.choice(['professor', 'room', 'time', 'day', 'swap'])

                if mutation_type == 'swap' and len(chromosome.genes) > 1:
                    # Swap time slots with another gene
                    j = random.randint(0, len(chromosome.genes) - 1)
                    if i != j:
                        other_gene = chromosome.genes[j]
                        # Swap timing info
                        gene.day, other_gene.day = other_gene.day, gene.day
                        gene.start_time, other_gene.start_time = other_gene.start_time, gene.start_time

                elif mutation_type == 'professor':
                    eligible_professors = [p for p in self.professors if gene.subject_id in p.subjects]
                    if eligible_professors:
                        gene.professor_id = random.choice(eligible_professors).id

                elif mutation_type == 'room' and gene.room_id:
                    subject = self.subject_dict[gene.subject_id]
                    session = subject.sessions[gene.session_number - 1]
                    eligible_rooms = [r for r in self.rooms if r.room_type == session.session_type]
                    if eligible_rooms:
                        gene.room_id = random.choice(eligible_rooms).id

                elif mutation_type == 'time':
                    valid_times = [t for t in self.valid_time_slots
                                   if t + gene.duration <= 19.0 and
                                   not (t < 13.0 and t + gene.duration > 12.0)]
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

        # Repair conflicts in children
        child1 = self._repair_chromosome(Chromosome(child1_genes))
        child2 = self._repair_chromosome(Chromosome(child2_genes))

        return child1, child2

    def mutate(self, chromosome: Chromosome) -> Chromosome:
        return self.smart_mutate(chromosome)

    def tournament_selection(self, population: List[Chromosome]) -> Chromosome:
        tournament_size = max(3, len(population) // 5)
        tournament = random.sample(population, tournament_size)
        return max(tournament, key=lambda x: x.fitness)

    def _repair_chromosome(self, chromosome: Chromosome) -> Chromosome:
        """Repair conflicts in a chromosome by reassigning conflicting genes"""
        conflict_tracker = ConflictTracker()
        repaired_genes = []

        # Sort genes by priority (longer duration first, then by original fitness contribution)
        sorted_genes = sorted(chromosome.genes, key=lambda g: g.duration, reverse=True)

        for gene in sorted_genes:
            if conflict_tracker.is_available(gene):
                # No conflict, keep as is
                repaired_genes.append(gene)
                conflict_tracker.add_gene(gene)
            else:
                # Conflict detected, find new assignment
                repaired_gene = self._find_alternative_assignment(gene, conflict_tracker)
                if repaired_gene:
                    repaired_genes.append(repaired_gene)
                    conflict_tracker.add_gene(repaired_gene)
                else:
                    # Fallback: use original gene (will be penalized in fitness)
                    repaired_genes.append(gene)

        return Chromosome(repaired_genes)

    def _find_alternative_assignment(self, gene: Gene, conflict_tracker: ConflictTracker) -> Optional[Gene]:
        """Find an alternative assignment for a conflicting gene"""
        # Get subject info for constraints
        subject = self.subject_dict[gene.subject_id]
        session_template = subject.sessions[gene.session_number - 1]

        # Get eligible professors and rooms
        eligible_professors = [p.id for p in self.professors if gene.subject_id in p.subjects]
        eligible_rooms = [r.id for r in self.rooms if r.room_type == session_template.session_type]

        # Try different combinations (limited attempts to avoid infinite loops)
        for attempt in range(50):
            # Try different professor
            new_professor = random.choice(eligible_professors)
            new_room = random.choice(eligible_rooms) if eligible_rooms else None
            new_day = random.choice(list(Day))

            # Find valid time slots
            valid_times = []
            for start_time in self.valid_time_slots:
                end_time = start_time + gene.duration
                if (end_time <= 19.0 and
                        not (start_time < 13.0 and end_time > 12.0)):
                    valid_times.append(start_time)

            if not valid_times:
                continue

            new_start_time = random.choice(valid_times)

            # Create candidate gene
            candidate_gene = Gene(
                section_id=gene.section_id,
                subject_id=gene.subject_id,
                session_number=gene.session_number,
                session_type=gene.session_type,
                professor_id=new_professor,
                room_id=new_room,
                day=new_day,
                start_time=new_start_time,
                duration=gene.duration
            )

            # Check if this assignment works
            if conflict_tracker.is_available(candidate_gene):
                return candidate_gene

        return None  # No alternative found

    def evolve(self) -> Chromosome:
        """Main evolution loop with improved termination"""
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

            # Check for early termination (perfect solution)
            if best_fitness >= 0.99:  # Very high fitness
                print(f"Perfect solution found at generation {generation}!")
                break

            # Check for stagnation
            if len(best_fitness_history) > 50:
                recent_improvement = max(best_fitness_history[-50:]) - min(best_fitness_history[-50:])
                if recent_improvement < 0.001:
                    stagnation_counter += 1
                else:
                    stagnation_counter = 0

                if stagnation_counter > 100:
                    print(f"Stopping due to stagnation at generation {generation}")
                    break

            # Print progress
            if generation % 100 == 0:
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