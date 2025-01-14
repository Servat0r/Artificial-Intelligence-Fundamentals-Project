from PIL import Image, ImageDraw
import numpy as np
from skimage.metrics import structural_similarity
import cv2
import matplotlib.pyplot as plt
import sewar as sw
import imageio 

from sewar.full_ref import mse, rmse, psnr, uqi, ssim, ergas, scc, rase, sam, msssim, vifp

MAX_STEPS = 200
FLAG_LOCATION = 0.5

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
        
        #iamge for gif
        self.gif_images = []

    def polygonDataToImage(self, polygonData):
        """
        accepts polygon data and creates an image containing these polygons.
        :param polygonData: a list of polygon parameters. Each item in the list
        represents the vertices locations, color and transparency of the corresponding polygon
        :return: the image containing the polygons (Pillow format)
        """

        # start with a new image:
        #image = Image.new("RGB", (self.width, self.height))
        image = Image.new('RGB', (self.width, self.height), (255, 255, 255)) #gray scale version
        draw = ImageDraw.Draw(image, 'RGBA')

        # divide the polygonData to chunks, each containing the data for a single polygon:
        #chunkSize = self.polygonSize * 2 + 4  # (x,y) per vertex + (RGBA)
        chunkSize = self.polygonSize * 2 + 1  # (x,y) per vertex + (GRAY) only one color
        polygons = self.list2Chunks(polygonData, chunkSize)

        # iterate over all polygons and draw each of them into the image:
        #iter = 0

        #order the generator of polygons by their area, so that the smaller polygons will be drawn last, from biggest to smallest
        
        #if self.polygonSize == 2:
        #    sorted_polygons = sorted(polygons, key=lambda x: self.ellipseArea(x[0], x[1]), reverse=True)
        #print(polygons)

        for poly in polygons:
            #iter += 1
            #print(iter)

            index = 0
            #print(poly)

            # extract the vertices of the current polygon:
            vertices = []
            for vertex in range(self.polygonSize):
                vertices.append((int(poly[index] * self.width), int(poly[index + 1] * self.height)))
                index += 2

            # extract the RGB and alpha values of the current polygon:
            #red = int(poly[index] * 255)
            #green = int(poly[index + 1] * 255)
            #blue = int(poly[index + 2] * 255)
            #alpha = int(poly[index + 3] * 255)
            gray = int(poly[index] * 255)


            # draw the polygon into the image:
            #draw.polygon(vertices, (red, green, blue, alpha))
            #draw polygon grayscale
            #draw.polygon(vertices, (gray, gray, gray, 255))
            #draw circle grayscale
            if (self.polygonSize == 2):
                draw.ellipse(vertices, (gray, gray, gray, 255))
            else:
                draw.polygon(vertices, (gray, gray, gray, 255))
            #draw circle grayscale not filled
            #draw.ellipse(vertices, outline=(gray, gray, gray, 255))
            
            
            
            

        # cleanup:
        del draw

        return image

    def getDifference(self, polygonData, method="MSE"):
        """
        accepts polygon data, creates an image containing these polygons, and calculates the difference
        between this image and the reference image using one of two methods.
        :param polygonData: a list of polygon parameters. Each item in the list
        represents the vertices locations, color and transparency of the corresponding polygon
        :param method: base method of calculating the difference ("MSE" or "SSIM" or others).
        larger return value always means larger difference
        :return: the calculated difference between the image containg the polygons and the reference image
        """

        # create the image containing the polygons:
        image = self.polygonDataToImage(polygonData)

        if method == "MSE":
            return self.getMse(image)
        elif method == "UQI":
            return 1.0 - self.getUqi(image)
        elif method == "SSIM":
            return 1.0 - self.getSsim(image)
        elif method == "MSSIM":
            return 1.0 - self.getMsssim(image)
        elif method == "MSE+SSIM":
            return self.getMse(image) + (1.0 - self.getSsim(image))
        elif method == "SCC":
            return 1.0 - self.getScc(image)
        elif method == "VIFP":
            return 1.0 - self.getVifp(image)
        elif method == "RMSE":
            return self.getRmse(image)
        elif method == "PSNR":
            return 1.0 - self.getPsnr(image)
        else :
            print("Unknown method: " + method)
            return 0

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

        # create an image from the polygon data:
        image = self.polygonDataToImage(polygonData)

        # save image for gif animation 
        self.gif_images.append(self.toCv2(image))

        # plot the image side-by-side with the reference image:
        self.plotImages(image, header)

        # save the plot to file:
        plt.savefig(imageFilePath)

    def saveGif(self, gifFilePath):
        # save gif to file:
        imageio.mimsave(gifFilePath, self.gif_images)

    # utility methods:
    # image is the image made by polygons 

    def toCv2(self, pil_image):
        """converts the given Pillow image to CV2 format"""
        # rgb version
        #return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        #gray scale version
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2GRAY)

    def getMse(self, image):
        """calculates MSE of difference between the given image and the reference image"""
        return np.sum((self.toCv2(image).astype("float") - self.refImageCv2.astype("float")) ** 2)/float(self.numPixels)

    def getRmse(self, image):
        """calculates RMSE of difference between the given image and the reference image"""
        return np.sqrt(self.getMse(image))  

    def getSsim(self, image):
        """calculates mean structural similarity index between the given image and the reference image"""
        #return structural_similarity(self.toCv2(image), self.refImageCv2, multichannel=True)
        #ssim for grayscale images
        return structural_similarity(self.toCv2(image), self.refImageCv2)

    def getUqi(self, image):
        """calculates universal quality index between the given image and the reference image using swear"""
        return uqi(self.toCv2(image), self.refImageCv2)

    def getScc(self, image):
        """calculates structural content correlation between the given image and the reference image"""
        return scc(self.toCv2(image), self.refImageCv2)

    def getVifp(self, image):
        """calculates visual information fidelity between the given image and the reference image"""
        return vifp(self.refImageCv2, self.toCv2(image)) 

    def getPsnr(self, image):
        """calculates peak signal-to-noise ratio between the given image and the reference image"""
        return psnr(self.refImageCv2, self.toCv2(image))

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

    #ellipses area
    def ellipseArea(self, a, b):
        return np.pi * a * b

    