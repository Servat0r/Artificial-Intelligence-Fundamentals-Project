from __future__ import annotations
from salvatore.utils import *
from .base import ContoursLineMetric


class AbsErrorLinesMetric(ContoursLineMetric):
    # todo add documentation!
    CHUNKSIZE = 4   # size of chunks to be extracted from individuals

    def __init__(self, image_path: str, canny_low: TReal, canny_high: TReal,
                 bounds_low: TReal = 0.0, bounds_high: TReal = 1.0):
        """
        :param image_path: Path of the target image.
        :param canny_low: Low threshold for cv2.Canny().
        :param canny_high: High threshold for cv2.Canny().
        :param bounds_low: Lower bounds for representing coordinates. Defaults to 0.0.
        :param bounds_high: Higher bounds for representing coordinates. Defaults to 1.0.
        """
        self.target_cv2 = None  # target image in cv2 (array) format
        self.target_pil = None  # target image as PIL.Image object
        super(AbsErrorLinesMetric, self).__init__(image_path, canny_low, canny_high, bounds_low, bounds_high)

    def get_target_image(self) -> Image:
        return self.target_pil

    # noinspection PyUnresolvedReferences
    def standardize_target(self):
        pil_image = Image.open(self.image_path)
        cv2_image = pil_to_cv2(pil_image)
        self.image_width, self.image_height = cv2_image.shape[1], cv2_image.shape[0]

        # find contours
        _, contours, _ = find_contours(cv2_image, self.canny_low, self.canny_high)

        # create and store contour image in memory
        self.target_cv2 = create_monochromatic_image(self.image_width, self.image_height)
        self.target_cv2 = draw_contours(self.target_cv2, contours, copy=False)
        self.target_pil = Image.fromarray(self.target_cv2)

    def standardize_individual(self, individual, check_repr=False):
        """
        Expands this individual into a complete sequence of points of lines.
        """
        individual = super(AbsErrorLinesMetric, self).standardize_individual(individual, check_repr)
        img = create_monochromatic_image(self.image_width, self.image_height)
        for start, end in self.list_to_chunks(individual):
            img = cv2.line(img, start, end, color=0)
        return img

    def get_difference(self, individual):
        # get all individual points as a numpy array
        individual_points = self.standardize_individual(individual)
        result = np.abs(cv2.subtract(self.target_cv2, individual_points))
        result = np.sum(result)
        return result


__all__ = [
    'AbsErrorLinesMetric',
]
