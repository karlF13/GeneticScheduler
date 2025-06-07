# main.py
from data.data import create_sample_data
from algorithm.genetic import GeneticScheduler
from utils.display_schedule import print_schedule

if __name__ == "__main__":
    sections, subjects, professors, rooms = create_sample_data()

    scheduler = GeneticScheduler(
        sections=sections,
        subjects=subjects,
        professors=professors,
        rooms=rooms,
        population_size=150,
        mutation_rate=0.03,
        crossover_rate=0.8,
        generations=20000
    )

    print(f"Total sessions to schedule: {scheduler.genome_length}")
    print("Starting evolution with conflict reduction strategies...")

    best_schedule = scheduler.evolve()

    print(f"\nBest schedule found with fitness: {best_schedule.fitness:.4f}")
    print("\nSchedule details:")

    print_schedule(best_schedule, sections, subjects, professors, rooms)