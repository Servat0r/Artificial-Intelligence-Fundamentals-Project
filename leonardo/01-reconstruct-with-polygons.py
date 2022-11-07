from deap import base
from deap import creator
from deap import tools

import random
import numpy
import os

import image_test as image_test
import elitism_callback as elitism_callback

import matplotlib.pyplot as plt
import seaborn as sns

# problem related constants
POLYGON_SIZE = 2
NUM_OF_POLYGONS = 1000

# calculate total number of params in chromosome:
# For each polygon we have:
# two coordinates per vertex, 3 color values, one alpha value
#NUM_OF_PARAMS = NUM_OF_POLYGONS * (POLYGON_SIZE * 2 + 4)
#grayscale version:
NUM_OF_PARAMS = NUM_OF_POLYGONS * (POLYGON_SIZE * 2 + 1)

# Genetic Algorithm constants:
POPULATION_SIZE = 400
P_CROSSOVER = 0.9  # probability for crossover
P_MUTATION = 0.5   # probability for mutating an individual
MAX_GENERATIONS = 1000
HALL_OF_FAME_SIZE = 100
CROWDING_FACTOR = 20.0  # crowding factor for crossover and mutation

# set the random seed:
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# create the image test class instance:
imageTest = image_test.ImageTest("/Users/lilf4p/Developer/aif/aif-project/images/monalisabw.jpeg", POLYGON_SIZE)

# calculate total number of params in chromosome:
# For each polygon we have:
# two coordinates per vertex, 3 color values, one alpha value
#NUM_OF_PARAMS = NUM_OF_POLYGONS * (POLYGON_SIZE * 2 + 4)
#garayscale version:
NUM_OF_PARAMS = NUM_OF_POLYGONS * (POLYGON_SIZE * 2 + 1)

# all parameter values are bound between 0 and 1, later to be expanded:
BOUNDS_LOW, BOUNDS_HIGH = 0.0, 1.0  # boundaries for all dimensions

toolbox = base.Toolbox()

# define a single objective, minimizing fitness strategy:
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

# create the Individual class based on list:
creator.create("Individual", list, fitness=creator.FitnessMin)

# helper function for creating random real numbers uniformly distributed within a given range [low, up]
# it assumes that the range is the same for every dimension
def randomFloat(low, up):
    return [random.uniform(l, u) for l, u in zip([low] * NUM_OF_PARAMS, [up] * NUM_OF_PARAMS)]

# create an operator that randomly returns a float in the desired range:
toolbox.register("attrFloat", randomFloat, BOUNDS_LOW, BOUNDS_HIGH)

# create an operator that fills up an Individual instance:
toolbox.register("individualCreator",
                 tools.initIterate,
                 creator.Individual,
                 toolbox.attrFloat)

# create an operator that generates a list of individuals:
toolbox.register("populationCreator",
                 tools.initRepeat,
                 list,
                 toolbox.individualCreator)


# fitness calculation using MSE as difference metric:
def getDiff(individual):
    return imageTest.getDifference(individual, "MSE"),
    #return imageTest.getDifference(individual, "SSIM"),

toolbox.register("evaluate", getDiff)


# genetic operators:
toolbox.register("select", tools.selTournament, tournsize=2)

toolbox.register("mate",
                 tools.cxSimulatedBinaryBounded,
                 low=BOUNDS_LOW,
                 up=BOUNDS_HIGH,
                 eta=CROWDING_FACTOR)

toolbox.register("mutate",
                 tools.mutPolynomialBounded,
                 low=BOUNDS_LOW,
                 up=BOUNDS_HIGH,
                 eta=CROWDING_FACTOR,
                 indpb=1.0/NUM_OF_PARAMS)


# save the best current drawing every 100 generations (used as a callback):
def saveImage(gen, polygonData):

    # only every 100 generations:
    if gen % 100 == 0:

        # create folder if does not exist:
        folder = "result/grayscale/run-mse-ellipse-{}-{}/ga-{}-{}-{}-{}-{}-{}".format(POLYGON_SIZE, NUM_OF_POLYGONS, POPULATION_SIZE, P_CROSSOVER, P_MUTATION, MAX_GENERATIONS, HALL_OF_FAME_SIZE, CROWDING_FACTOR)
        if not os.path.exists(folder):
            os.makedirs(folder)

        # save the image in the folder:
        imageTest.saveImage(polygonData,
                            "{}/after-{}-gen.png".format(folder, gen),
                            "After {} Generations".format(gen))
        

# Genetic Algorithm flow:
def main():

    # create initial population (generation 0):
    population = toolbox.populationCreator(n=POPULATION_SIZE)

    # prepare the statistics object:
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("min", numpy.min)
    stats.register("avg", numpy.mean)

    # define the hall-of-fame object:
    hof = tools.HallOfFame(HALL_OF_FAME_SIZE)


    # perform the Genetic Algorithm flow with elitism and 'saveImage' callback:
    population, logbook = elitism_callback.eaSimpleWithElitismAndCallback(population,
                                                      toolbox,
                                                      cxpb=P_CROSSOVER,
                                                      mutpb=P_MUTATION,
                                                      ngen=MAX_GENERATIONS,
                                                      callback=saveImage,
                                                      stats=stats,
                                                      halloffame=hof,
                                                      verbose=True)

    # print best solution found:
    best = hof.items[0]
    print()
    print("Best Solution = ", best)
    print("Best Score = ", best.fitness.values[0])
    print()


    # draw best image next to reference image:
    folder = "result/grayscale/run-mse-ellipse-{}-{}/ga-{}-{}-{}-{}-{}-{}".format(POLYGON_SIZE, NUM_OF_POLYGONS, POPULATION_SIZE, P_CROSSOVER, P_MUTATION, MAX_GENERATIONS, HALL_OF_FAME_SIZE, CROWDING_FACTOR)
    imageTest.saveImage(best,"{}/best.png".format(folder),
                            "Best Solution\nBest Score = {}".format(best.fitness.values[0]))

    # extract statistics:
    minFitnessValues, meanFitnessValues = logbook.select("min", "avg")

    # plot statistics:
    sns.set_style("whitegrid")
    plt.figure("Stats:")
    plt.plot(minFitnessValues, color='red')
    plt.plot(meanFitnessValues, color='green')
    plt.xlabel('Generation')
    plt.ylabel('Min / Average Fitness')
    plt.title('Min and Average fitness over Generations')

    # save both plots:
    plt.savefig("result/grayscale/run-mse-ellipse-{}-{}/ga-{}-{}-{}-{}-{}-{}/stats.png".format(POLYGON_SIZE, NUM_OF_POLYGONS, POPULATION_SIZE, P_CROSSOVER, P_MUTATION, MAX_GENERATIONS, HALL_OF_FAME_SIZE, CROWDING_FACTOR))

if __name__ == "__main__":
    main()