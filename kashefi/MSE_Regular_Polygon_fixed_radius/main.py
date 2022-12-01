# Try Different Selection Options
# # Try Different Crossover (Mate) Options
# # Try Different Mutation (Mutate) Options
# Combine these different options making a table of combinations
# Make implement and test each combination and record the result
# Write a report
from PIL.Image import Image
from deap import base
from deap import creator
from deap import tools

import random
import numpy as np
import os

import image_test
import elitism_callback

import matplotlib.pyplot as plt
import seaborn as sns
import time
from scoop import futures
import multiprocessing
from multiprocessing import freeze_support


start_time = time.time()
C_METHOD = "MSE"

# problem related constants
POLYGON_SIZE = 5
NUM_OF_POLYGONS = 200

# calculate total number of params in chromosome:
# For each polygon we have:
# two coordinates per vertex, 3 color values, one alpha value, starting and ending angles
NUM_OF_PARAMS = NUM_OF_POLYGONS * (POLYGON_SIZE * 2 + 5)

# Genetic Algorithm constants:
# POPULATION_SIZE = 200
# P_CROSSOVER = 0.9  # probability for crossover
# P_MUTATION = 0.008   # probability for mutating an individual
# MAX_GENERATIONS = 500
# HALL_OF_FAME_SIZE = 30
# CROWDING_FACTOR = 10.0  # crowding factor for crossover and mutation
POPULATION_SIZE = 250
P_CROSSOVER = 0.9  # probability for crossover
P_MUTATION = 0.01   # probability for mutating an individual
MAX_GENERATIONS = 1000
HALL_OF_FAME_SIZE = 20
CROWDING_FACTOR = 10.0  # crowding factor for crossover and mutation

# set the random seed:
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# create the image test class instance:
imageTest = image_test.ImageTest("images/monalisa.png", POLYGON_SIZE)
# imageTest = image_test.ImageTest("images/tower.jpg", POLYGON_SIZE)

# calculate total number of params in chromosome:
# For each polygon we have:
# two coordinates per vertex, 3 color values, one alpha value, starting and ending angles
NUM_OF_PARAMS = NUM_OF_POLYGONS * (POLYGON_SIZE * 2 + 5)
# NUM_OF_PARAMS = NUM_OF_POLYGONS * (POLYGON_SIZE * 2 + 4)
# NUM_OF_PARAMS = NUM_OF_POLYGONS * (POLYGON_SIZE * 2 )

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
    if C_METHOD == "MSE":
        return imageTest.getDifference(individual, "MSE"),
    elif C_METHOD == "SSIM":
        return imageTest.getDifference(individual, "SSIM"),

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
        folder = "images/results/run-{}-{}-{}-{}-{}-{}".format(POLYGON_SIZE, NUM_OF_POLYGONS, C_METHOD, POPULATION_SIZE, MAX_GENERATIONS, start_time)
        if not os.path.exists(folder):
            os.makedirs(folder)

        # save the image in the folder:
        imageTest.saveImage(polygonData,
                            "{}/after-{}-gen.png".format(folder, gen),
                            "After {} Generations".format(gen))

# Genetic Algorithm flow:
def main():
    # Concurrent Execution should be enabled
    # toolbox.register("map", futures.map)
    # execute the algorithm in multiple threads simultaneously
    pool = multiprocessing.Pool()
    toolbox.register("map", pool.map)

    # create initial population (generation 0):
    population = toolbox.populationCreator(n=POPULATION_SIZE)

    # prepare the statistics object:
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("min", np.min)
    stats.register("avg", np.mean)

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

    # Show Elapsed Time from the begingin to the end of the Algorithm execution
    print("time elapsed: {:.2f}s".format(time.time() - start_time))

    # draw best image next to reference image:
    imageTest.plotImages(imageTest.polygonDataToImage(best))

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

    # show both plots:
    plt.show()
    folder = "images/results/run-{}-{}-{}-{}-{}-{}".format(POLYGON_SIZE, NUM_OF_POLYGONS, C_METHOD, POPULATION_SIZE, MAX_GENERATIONS, start_time)
    if not os.path.exists(folder):
        os.makedirs(folder)
    # save gif
    imageTest.saveGif(folder + "/result.gif")
    np.savetxt(folder + '/evolution_log.csv', logbook, delimiter=',', fmt='%s')



if __name__ == "__main__":
    # freeze_support()

    main()
