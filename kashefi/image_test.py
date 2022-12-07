import random

import imageio
from PIL import Image, ImageDraw
import numpy as np
from sewar import msssim
from skimage.metrics import structural_similarity
import cv2
import matplotlib.pyplot as plt

MAX_STEPS = 200
FLAG_LOCATION = 0.5
log_dump = []

class ImageTest:
    def __init__(self, imagePath, polygonSize):
        """
        Initializes an instance of the class
        :param imagePath: the path of the file containing the reference image
        :param polygonSize: the number of vertices on the polygons used to recreate the image
        """
        self.refImage = Image.open(imagePath)
        self.polygonSize = polygonSize


        self.width, self.height = self.refImage.size
        self.numPixels = self.width * self.height
        self.refImageCv2 = self.toCv2(self.refImage)


        self.gif_images = []

    def polygonDataToImage(self, polygonData):
        """
        accepts polygon data and creates an image containing these polygons.
        :param polygonData: a list of polygon parameters. Each item in the list
        represents the vertices locations, color and transparency of the corresponding polygon
        :return: the image containing the polygons (Pillow format)
        """

        # start with a new image:
        image = Image.new('RGB', (self.width, self.height),(127,127,127,127))#TODO
        draw = ImageDraw.Draw(image, 'RGBA')
        # image = Image.new('L', (self.width, self.height), 127)#TODO
        # draw = ImageDraw.Draw(image, 'L')

        # divide the polygonData to chunks, each containing the data for a single polygon:
        chunkSize = self.polygonSize * 2 + 4 # (x,y) per vertex + (RGBA) default
        # chunkSize = self.polygonSize * 2 + 5 # (x,y,r) per vertex + (RGBA)
        polygons = self.list2Chunks(polygonData, c6hunkSize)
        radius = self.width/20 if self.width < self.height else self.height/20
        # max_radius = self.width/20 if self.width < self.height else self.height/20
        # iterate over all polygons and draw each of them into the image:
        for poly in polygons:
            index = 0
            # calc the fixed radius for all vertices of polygon
            # radius = int((poly[self.polygonSize * 2 + 4] * max_radius) % max_radius)
            # extract the vertices of the current polygon:
            vertices = []
            for vertex in range(self.polygonSize):
                vertices.append((int(poly[index] * self.width), int(poly[index + 1] * self.height), radius if radius > 0 else 1)) #default
                index += 2
            # r = (r/2 if r > self.width/2 else r)
            # vertices.append((int(poly[index] * self.width), int(poly[index + 1] * self.height), r))

                # index += 2 #default

            # extract the RGB and alpha values of the current polygon:
            red = int(poly[index] * 255) #default
            green = int(poly[index + 1] * 255) #default
            blue = int(poly[index + 2] * 255) #default
            alpha = int(poly[index + 3] * 255) #default
            # starting_angle = int(poly[index + 4] * 255)
            # ending_angle = int(poly[index + 5] * 255)
            # gray = int(poly[index] * 255)
            # color = int(poly[index] * 255)

            # draw the polygon into the image:
            # draw.polygon(vertices, (red, green, blue, alpha))
            draw.regular_polygon(vertices[0], self.polygonSize, 0, (red, green, blue, alpha))
            # draw.regular_polygon(vertices[0], self.polygonSize, 0, gray)
            # start, end = self.get_random_angles()
            # start, end = 0, 90
            # arc_width = int(poly[index] * self.width) % self.width
            # line_width = 1
            # radios = int(poly[index] * self.width) % self.width
            # draw.arc(vertices, start, end, (red, green, blue, alpha), line_width)
            # draw.pieslice(vertices, starting_angle, ending_angle, (red, green, blue, alpha))
            # draw.rounded_rectangle(vertices, radios, (red, green, blue, alpha), line_width)
            # draw.arc(vertices, start, end, (gray, gray, gray, alpha), line_width)
            # draw.arc(vertices, start, end, 127, line_width)
            # draw.chord(vertices, start, end, (red, green, blue, alpha), line_width)
            # draw.polygon(vertices, (gray, gray, gray, 255))
            # draw.polygon(vertices, 0)

        # cleanup:
        del draw

        return image




    def getDifference(self, polygonData, method="MSE"):
        """
        accepts polygon data, creates an image containing these polygons, and calculates the difference
        between this image and the reference image using one of two methods.
        :param polygonData: a list of polygon parameters. Each item in the list
        represents the vertices locations, color and transparency of the corresponding polygon
        :param method: base method of calculating the difference ("MSE" or "SSIM").
        larger return value always means larger difference
        :return: the calculated difference between the image containg the polygons and the reference image
        """

        # create the image containing the polygons:
        image = self.polygonDataToImage(polygonData)

        if method == "MSE":
            return self.getMse(image)
        elif method == "SSIM":
            return self.getSsim(image)
        else:
            return 1.0 - self.getMsssim(image)

    def plotImages(self, image, header=None):
        """
        creates a 'side-by-side' plot of the given image next to the reference image
        :param image: image to be drawn next to reference image (Pillow format)
        :param header: text used as a header for the plot
        """

        fig = plt.figure("Image Comparison:")
        if header:
            plt.suptitle(header)

        # plot the reference image on the left:
        ax = fig.add_subplot(1, 2, 1)
        plt.imshow(self.refImage)
        self.ticksOff(plt)

        # plot the given image on the right:
        fig.add_subplot(1, 2, 2)
        plt.imshow(image)
        self.ticksOff(plt)

        return plt

    def saveImage(self, polygonData, imageFilePath, header=None):
        """
        accepts polygon data, creates an image containing these polygons,
        creates a 'side-by-side' plot of this image next to the reference image,
        and saves the plot to a file
        :param polygonData: a list of polygon parameters. Each item in the list
        represents the vertices locations, color and transparency of the corresponding polygon
        :param imageFilePath: path of file to be used to save the plot to
        :param header: text used as a header for the plot
        """

        # create an image from th epolygon data:
        image = self.polygonDataToImage(polygonData)


        # save image for gif animation
        self.gif_images.append(image)


        # plot the image side-by-side with the reference image:
        self.plotImages(image, header)

        # save the plot to file:
        plt.savefig(imageFilePath)

    # utility methods:

    def toCv2(self, pil_image):
        """converts the given Pillow image to CV2 format"""
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def getMse(self, image):
        """calculates MSE of difference between the given image and the reference image"""
        return np.sum((self.toCv2(image).astype("float") - self.refImageCv2.astype("float")) ** 2)/float(self.numPixels)

    def getSsim(self, image):
        """calculates mean structural similarity index between the given image and the reference image"""
        # return structural_similarity(self.toCv2(image), self.refImageCv2, multichannel=True)
        # (Kashefi) Changed Multichannel = true to channel_axis = -1 as in https://github.com/pytorch/ignite/pull/2360
        return structural_similarity(self.toCv2(image), self.refImageCv2, channel_axis=-1)

    def getMsssim(self, image):
        """calculates mean structural similarity index between the given image and the reference image"""
        return msssim(self.toCv2(image), self.refImageCv2)
    def list2Chunks(self, list, chunkSize):
        """divides a given list to fixed size chunks, returns a generator iterator"""
        for chunk in range(0, len(list), chunkSize):
            yield(list[chunk:chunk + chunkSize])

    def ticksOff(self, plot):#TODO
        """turns off ticks on both axes"""
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
    # def getMode(self):
    #     return self.refImage.mode

    def saveGif(self, gifFilePath):
        # save gif to file:
        imageio.mimsave(gifFilePath, self.gif_images)