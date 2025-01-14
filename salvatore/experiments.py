# Base classes for experiments
from __future__ import annotations

import os
import pickle
from salvatore.utils import *
from datetime import datetime


class Experiment:

    @property
    def base_save_dir(self):
        return os.path.join(type(self).__name__, f"Experiment_{datetime.today().strftime('%Y_%m_%d_%H_%M_%S')}")

    @property
    def dir_exp_info(self):
        return f'_{self.population_size}pop_{self.max_generations}max_gen_{self.hof_size}hof_size'

    @classmethod
    @abstractmethod
    def experiment_schema(cls):
        return {
            # Experiment-proper parameters
            'image_path': str,
            sch.Optional('population_size', default=250): int,
            sch.Optional('p_crossover', default=0.9): float,
            sch.Optional('p_mutation', default=0.5): float,
            sch.Optional('max_generations', default=1000): int,
            sch.Optional('hof_size', default=25): int,
            sch.Optional('random_seed', default=10): int,
            sch.Optional('save_image_dir', default=None): str,
            sch.Optional('bounds_low', default=0.0): float,
            sch.Optional('bounds_high', default=1.0): float,
        }

    @classmethod
    def from_config(cls, config: dict) -> Experiment:
        schema = sch.Schema(cls.experiment_schema())
        config = schema.validate(config)
        return cls(**config)

    def __init__(self, image_path: str, population_size: int = 250, p_crossover=0.9,
                 p_mutation=0.5, max_generations: int = 1000, hof_size: int = 25,
                 random_seed: int = None, save_image_dir: str = None, device='cpu',
                 algorithm: EAlgorithm = EASimpleForArrays(), bounds_low: float = None,
                 bounds_high: float = None):
        self.metric = None  # subclasses must initialize
        self.population_size = population_size
        self.p_crossover = p_crossover
        self.p_mutation = p_mutation
        self.max_generations = max_generations
        self.hof_size = hof_size
        self.bounds_low = bounds_low
        self.bounds_high = bounds_high
        self.crowding_factor = None
        self.num_params = None

        self.seed = random_seed
        if self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)
        self.toolbox = dp_base.Toolbox()

        # Where to save experiment results
        dr = self.base_save_dir + self.dir_exp_info
        save_image_dir = dr if save_image_dir is None else os.path.join(save_image_dir, dr)
        self.save_image_dir = os.path.join('salvatore', 'results', save_image_dir)
        os.makedirs(self.save_image_dir, exist_ok=True)

        self._show_results = False
        self.device = device
        self.algorithm = algorithm

    def save_image(self, algorithm: EAlgorithm, gen_step: int = 20):
        gen, best = algorithm.gen, algorithm.best
        # only after gen_step generations
        if gen % gen_step == 0 or algorithm.stop:
            self.__ticks_off()
            os.makedirs(self.save_image_dir, exist_ok=True)
            image = self.metric.get_individual_image(best)
            self.plot_image_comparison(image, f"After {gen} generations", difference=False)
            self.__ticks_off()
            image_file_path = os.path.join(self.save_image_dir, f'After {gen} generations.png')
            plt.savefig(image_file_path)

    def save_stats(self, algorithm: EAlgorithm, show: bool = False):
        """
        Saves statistics of min and average fitness value.
        """
        logbook, gen = algorithm.logbook, algorithm.gen
        if algorithm.stop:
            min_fitness_val, avg_fitness_val = logbook.select('min', 'avg')
            # plot statistics:
            sns.set_style("whitegrid")
            plt.figure("Stats:")
            plt.plot(min_fitness_val, color='red')
            plt.plot(avg_fitness_val, color='green')
            plt.xlabel('Generation')
            plt.ylabel('Min / Average Fitness')
            plt.title('Min and Average fitness over Generations')
            plt.savefig(os.path.join(self.save_image_dir, f'Stats.png'))
            if show:
                plt.show()

    # noinspection PyUnresolvedReferences
    def plot_individual_sample(self, difference=False, eval_fitness=True):
        """
        A random individual sample.
        """
        individual = self.toolbox.individualCreator()
        print(individual)
        if eval_fitness:
            fitness = self.metric.get_difference(individual)
            print(fitness)
        image = self.metric.get_individual_image(individual)
        image.show()
        self.plot_image_comparison(image, difference=difference, show=True)
        self.__ticks_off()

    def show_target_image(self):
        if self.metric is None:
            raise RuntimeError('Metric not defined for the experiment. This is probably because of an incorrect' +
                               ' use of super() call in experiment constructor. Remember that base constructor of' +
                               ' Experiment does NOT initialize the metric.')
        self.metric.get_target_image().show()

    # noinspection PyUnresolvedReferences
    def plot_image_comparison(self, image, header=None, difference=False, show=False):
        """
        Plots an image showing a comparison of the target image and the current one.
        """
        fig = plt.figure("Image Comparison:")
        if header:
            plt.suptitle(header)

        if difference:
            # plot the reference image on the left:
            ax = fig.add_subplot(2, 2, 1)
            target_image = self.metric.get_target_image()
            plt.imshow(target_image)
            self.__ticks_off()

            # plot the given image on the right:
            fig.add_subplot(2, 2, 2)
            plt.imshow(image)
            self.__ticks_off()

            target_cv = pil_to_cv2(self.metric.get_target_image(), start_mode=None, end_mode=None)
            image_cv = pil_to_cv2(image, start_mode=None, end_mode=None)
            diff_cv = np.abs(cv2.subtract(target_cv, image_cv))
            diff_image = cv2_to_pil(diff_cv, start_mode=None, end_mode=None)
            fig.add_subplot(2, 2, 3)
            plt.imshow(diff_image)
            self.__ticks_off()
        else:
            # plot the reference image on the left:
            ax = fig.add_subplot(1, 2, 1)
            target_image = self.metric.get_target_image()
            plt.imshow(target_image)
            self.__ticks_off()

            # plot the given image on the right:
            fig.add_subplot(1, 2, 2)
            plt.imshow(image)
            self.__ticks_off()

        if show:
            plt.show()
        return plt

    @staticmethod
    def __ticks_off():
        """
        Turns off ticks on both axes.
        """
        plt.tick_params(
            axis='both',
            which='both',
            bottom=False,
            left=False,
            top=False,
            right=False,
            labelbottom=False,
            labelleft=False,
        )

    # noinspection PyMethodMayBeStatic
    def set_fitness(self):  # fitness function
        # define a single objective, minimizing fitness strategy:
        dp_creator.create("FitnessMin", dp_base.Fitness, weights=(-1.0,))

    def set_individual(self):  # individual class and individualCreator
        # create the Individual class based on list:
        # noinspection PyUnresolvedReferences
        dp_creator.create("Individual", np.ndarray, fitness=dp_creator.FitnessMin)

        # register an operator that randomly returns a float in the given range
        self.toolbox.register(
            "attrFloat",
            lambda low, high: [random.uniform(l, u) for l, u in zip([low] * self.num_params, [high] * self.num_params)],
            self.bounds_low, self.bounds_high)

        # create an operator that fills up an Individual instance:
        # noinspection PyUnresolvedReferences
        self.toolbox.register("individualCreator", dp_tools.initIterate, dp_creator.Individual, self.toolbox.attrFloat)

    def set_pop_creator(self):
        # create an operator that generates a list of individuals:
        # noinspection PyUnresolvedReferences
        self.toolbox.register("populationCreator", dp_tools.initRepeat, list, self.toolbox.individualCreator)

    def set_evaluate(self):
        # register evaluation
        self.toolbox.register("evaluate", lambda individual: (self.metric.get_difference(individual),))

    def set_select(self):
        # genetic operators
        # self.toolbox.register('select', dp_tools.selTournament, tournsize=2)
        self.toolbox.register('select', selection_tournament, tournsize=2)

    def set_mate(self):
        self.toolbox.register(
            'mate', np_cx_simulated_binary_bounded, low=self.bounds_low,
            up=self.bounds_high, eta=self.crowding_factor,
        )

    def set_mutate(self):
        self.toolbox.register(
            "mutate", np_mut_polynomial_bounded, low=self.bounds_low, up=self.bounds_high,
            eta=self.crowding_factor, indpb=1.0 / self.num_params
        )

    def setup(self):
        self.set_fitness()
        self.set_individual()
        self.set_pop_creator()
        self.set_evaluate()
        self.set_select()
        self.set_mate()
        self.set_mutate()

    def standard_hall_of_fame(self):
        return ArrayHallOfFame(self.hof_size, similar=np.array_equal)

    # noinspection PyUnresolvedReferences
    def run(self, show: bool = False, callbacks: TCallback = None, verbose: bool = True):
        if show:
            self._show_results = True
            self.show_target_image()
        # create initial population (generation 0):
        population = self.toolbox.populationCreator(n=self.population_size)

        # prepare the statistics object:
        stats = dp_tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("min", np.min)
        stats.register("avg", np.mean)

        # define the hall-of-fame object:
        hof = self.standard_hall_of_fame()

        # perform the Genetic Algorithm flow with elitism and 'save_image' callback:
        # noinspection PyUnusedLocal
        population, logbook = self.algorithm(
            population, self.toolbox, cxpb=self.p_crossover, mutpb=self.p_mutation,
            ngen=self.max_generations, callbacks=callbacks,
            stats=stats, halloffame=hof, verbose=verbose)

        # print time stats
        tot_time = self.algorithm.end_time - self.algorithm.start_time
        min_time, sec_time = tot_time // 60, tot_time % 60
        hour_time, min_time = min_time // 60, min_time % 60
        print(f'Total elapsed time: {hour_time} hours, {min_time} minutes, {sec_time} seconds')

        # print best solution found:
        best = self.algorithm.best
        print()
        print("Best Solution = ", best)
        print("Best Score = ", best.fitness.values[0])
        print()

        # draw best image next to reference image
        self.save_image(self.algorithm, gen_step=1)

        # save statistics at the end of the experiment
        self.save_stats(self.algorithm, show=True)

        # save best image
        best_image_file_name = os.path.join(self.save_image_dir, 'best.png')
        best_image = self.metric.get_individual_image(best).convert('L')
        best_image.save(best_image_file_name)

        # save the best individual as NumPy array
        best_ind_file_name = os.path.join(self.save_image_dir, 'best.pkl')
        with open(best_ind_file_name, 'wb') as fp:
            pickle.dump(best, fp)


def generic_experiment_from_config(experiment_class: Type[Experiment], data: dict):
    # logger and stopping_criterions are already checked using schema in parse_experiment_data
    logger = data.pop('logger', None)
    stopping_criterions = data.pop('stopping_criterions', None)

    save_image_gen_step = data.pop('save_image_gen_step', 100)
    other_callback_args = data.pop('other_callback_args', None)

    # Now validate also save_image_gen_step and other_callback_args
    if save_image_gen_step is not None:
        save_image_gen_step = sch.Schema(int).validate(save_image_gen_step)
    if other_callback_args is not None:
        other_callback_args = sch.Schema({str: object}).validate(other_callback_args)

    dir_path = data.pop('dir_path', '.')
    os.chdir(dir_path)

    experiment = experiment_class.from_config(data)
    common_test_part(experiment, save_image_gen_step, other_callback_args, logger, stopping_criterions)


def generic_experiment_test(
    experiment_class: Type[Experiment], dir_path: str, image_path: str,
    p_crossover=0.9, p_mutation=0.5, population_size=250, max_generations=1000,
    random_seed=10, hof_size=25, save_image_dir: str = None, bounds_low=0.0,
    bounds_high=1.0, save_image_gen_step=100, other_callback_args=None,
    logger=None, stopping_criterions=None, *args, **kwargs
):
    os.chdir(dir_path)

    experiment = experiment_class(
        image_path, population_size=population_size, p_crossover=p_crossover, p_mutation=p_mutation,
        max_generations=max_generations, hof_size=hof_size, random_seed=random_seed, save_image_dir=save_image_dir,
        bounds_low=bounds_low, bounds_high=bounds_high, *args, **kwargs
    )
    common_test_part(experiment, save_image_gen_step, other_callback_args, logger, stopping_criterions)


__all__ = [
    'Experiment',
    'generic_experiment_test',
    'generic_experiment_from_config',
]
