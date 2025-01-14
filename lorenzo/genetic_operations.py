#from genetic_from_text import original_image, original_height, original_width
import string
import random
from skimage.metrics import peak_signal_noise_ratio as psnr 
from skimage.metrics import mean_squared_error as mse
from PIL import Image, ImageDraw, ImageFont
import numpy as np



def load_image(image_path):
    global original_image 
    global original_height, original_width 
    original_image = Image.open(image_path).convert("L")
    original_height, original_width  = original_image.size

def set_font(font):
    global font_name
    global font_size 
    font_name = font.get("name")
    font_size = font.get("size")
    

def draw_text(image):
    """Draw random text on image with given size."""
    if font_name == "default":
        font = ImageFont.load_default()
    else:
        font = ImageFont.truetype(f"lorenzo/fonts/{font_name}.ttf", font_size)
    
    text_length = random.randint(1,3)
    text = "".join(random.choice(string.ascii_letters) for i in range(text_length))

    x = random.randint(0,original_width-1)
    y = random.randint(0,original_height-1)

    color = (random.randint(0,255))
    image.text((y,x), text, fill=color, font=font)

def add_random_text_to_image(image, number_of_shapes):
    """Add shape with random proporties to image number_of_shapes times."""
    image_filled = image.copy()
    for _ in range(0, number_of_shapes):
        draw = ImageDraw.Draw(image_filled)
        draw_text(draw)
    return image_filled

def create_random_population(size, mutation_strength):
    """Create first generation with random population."""
    first_population = []
    for _ in range(0, size):
        blank_image = Image.new("L", (original_height, original_width))
        filled_image = add_random_text_to_image(blank_image, mutation_strength)
        first_population.append(filled_image)
    return first_population

def evaluate_fitness(image, distance):
    """Evaluate similarity of image with original."""
    if (distance == "psns"):
        return psnr(np.array(image), np.array(original_image))

    if (distance == "mse"):
        return mse(np.array(image), np.array(original_image))

    return psnr(np.array(image), np.array(original_image))

# Crossover operations with alternatives and helpers

def images_to_arrays(image1, image2):
    """Represent images as arrays."""
    img1_arr = np.array(image1)
    img2_arr = np.array(image2)
    return img1_arr ,img2_arr

def random_horizontal_swap(image1, image2):
    """Swap random rows of two images."""
    img1_arr, img2_arr = images_to_arrays(image1, image2)
    horizontal_random_choice = np.random.choice(original_width,
                                                int(original_width/2),
                                                replace=False)
    img1_arr[horizontal_random_choice] = img2_arr[horizontal_random_choice]
    return Image.fromarray(img1_arr)

def crossover(image1, image2):
    """Make crossover operation on two images."""
    return random_horizontal_swap(image1, image2)

def mutate(image, number_of_times):
    """Mutate image adding random shape number_of_times."""
    mutated = add_random_text_to_image(image, number_of_times)
    return mutated

def get_parents(local_population, local_fitnesses, distance):
    """Connect parents in pairs based on fitnesses as weights using softmax."""

    if(distance == "mse"):
            local_fitnesses = 1 / np.array(local_fitnesses)
    
    fitness_normalized = []
    for f in local_fitnesses:
        newf = (f - min(local_fitnesses)) / (max(local_fitnesses) - min(local_fitnesses))
        fitness_normalized.append(newf)
    
    fitness_sum = sum(np.exp(fitness_normalized))
    fitness_activated = np.exp(fitness_normalized) / fitness_sum
    local_parents_list = []
    for _ in range(0, len(local_population)):
        parents = random.choices(local_population, weights=fitness_activated, k=2)
        local_parents_list.append(parents)
    return local_parents_list
