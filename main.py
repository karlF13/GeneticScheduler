# main.py
from data.data import create_sample_data
from algorithm.genetic import GeneticAlgorithm
from sched_to_txt_file import print_schedule_to_file, print_schedule_by_professor_to_file, print_schedule_by_room_to_file

if __name__ == "__main__":
    sections, subjects, professors, rooms = create_sample_data()

    scheduler = GeneticAlgorithm(
        sections=sections,
        subjects=subjects,
        professors=professors,
        rooms=rooms,
        population_size=150,
        mutation_rate=0.03,
        crossover_rate=0.8,
        generations=20000
    )



    best_schedule, fitness_History = scheduler.evolve()

    scheduler.print_schedule(best_schedule)
    print_schedule_to_file(best_schedule)
    print_schedule_by_room_to_file(best_schedule)
    print_schedule_by_professor_to_file(best_schedule)