# Do relevant imports
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import cv2
from moviepy.editor import VideoFileClip



def grayscale(img):
    """Applies the Grayscale transform
    This will return an image with only one color channel
    but NOTE: to see the returned image as grayscale
    (assuming your grayscaled image is called 'gray')
    you should call plt.imshow(gray, cmap='gray')"""
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # Or use BGR2GRAY if you read an image with cv2.imread()
    # return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def grayToColor(img):
    return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

def canny(img, low_threshold, high_threshold):
    """Applies the Canny transform"""
    return cv2.Canny(img, low_threshold, high_threshold)


def gaussian_blur(img, kernel_size):
    """Applies a Gaussian Noise kernel"""
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)


def region_of_interest(img, vertices):
    """
    Applies an image mask.

    Only keeps the region of the image defined by the polygon
    formed from `vertices`. The rest of the image is set to black.
    """
    # defining a blank mask to start with
    mask = np.zeros_like(img)

    # defining a 3 channel or 1 channel color to fill the mask with depending on the input image
    if len(img.shape) > 2:
        channel_count = img.shape[2]  # i.e. 3 or 4 depending on your image
        ignore_mask_color = (255,) * channel_count
    else:
        ignore_mask_color = 255

    # filling pixels inside the polygon defined by "vertices" with the fill color
    cv2.fillPoly(mask, vertices, ignore_mask_color)

    # returning the image only where mask pixels are nonzero
    masked_image = cv2.bitwise_and(img, mask)
    return masked_image


def draw_lines(img, lines, color=[255, 0, 0], thickness=2):
    """
    NOTE: this is the function you might want to use as a starting point once you want to
    average/extrapolate the line segments you detect to map out the full
    extent of the lane (going from the result shown in raw-lines-example.mp4
    to that shown in P1_example.mp4).

    Think about things like separating line segments by their
    slope ((y2-y1)/(x2-x1)) to decide which segments are part of the left
    line vs. the right line.  Then, you can average the position of each of
    the lines and extrapolate to the top and bottom of the lane.

    This function draws `lines` with `color` and `thickness`.
    Lines are drawn on the image inplace (mutates the image).
    If you want to make the lines semi-transparent, think about combining
    this function with the weighted_img() function below
    """
    for line in lines:
        for x1, y1, x2, y2 in line:
            cv2.line(img, (x1, y1), (x2, y2), color, thickness)


def hough_lines(img, rho, theta, threshold, min_line_len, max_line_gap):
    """
    `img` should be the output of a Canny transform.

    Returns an image with hough lines drawn.
    """
    lines = cv2.HoughLinesP(img, rho, theta, threshold, np.array([]), minLineLength=min_line_len,
                            maxLineGap=max_line_gap)
    line_img = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
    draw_lines(line_img, lines)
    return line_img


# Python 3 has support for cool math symbols.

def weighted_img(img, initial_img, α=0.8, β=1., λ=0.):
    """
    `img` is the output of the hough_lines(), An image with lines drawn on it.
    Should be a blank image (all black) with lines drawn on it.

    `initial_img` should be the image before any processing.

    The result image is computed as follows:

    initial_img * α + img * β + λ
    NOTE: initial_img and img must be the same shape!
    """
    return cv2.addWeighted(initial_img, α, img, β, λ)



# Define the Hough transform parameters
rho = 2
theta = np.pi/90
threshold = 15
min_line_length = 200
max_line_gap = 150

# Define the canny edge detection parameters
blur_kernel = 13
canny_low_threshold = 50
canny_high_threshold = 150

# Define the detection horizon
y_cut = .62

# The coordinates of the lines
global prev_bottom_left_x
global prev_bottom_right_x
global prev_top_left_x
global prev_top_right_x

prev_bottom_left_x = 0
prev_bottom_right_x = 0
prev_top_left_x = 0
prev_top_right_x = 0

# This function processes each frame from the video individually
def process_image(image):
    global prev_bottom_left_x
    global prev_bottom_right_x
    global prev_top_left_x
    global prev_top_right_x

    imshape = image.shape

    vertices = np.array([[ (0, imshape[0]),
                           (imshape[1] * .45, imshape[0] * y_cut),
                           (imshape[1] * .55, imshape[0] * y_cut),
                           (imshape[1], imshape[0]) ]], dtype=np.int32)

    ## Conversion to grayscale and blurring
    gray = gaussian_blur(grayscale(image),blur_kernel)

    ## Increase contrast
    highlights = (gray[:,:] > 180)
    gray[highlights] = 255


    edges = canny(gray,canny_low_threshold,canny_high_threshold)
    masked = region_of_interest(edges, vertices)

    lines = cv2.HoughLinesP(masked, rho, theta, threshold, np.array([]),
                                    min_line_length, max_line_gap)

    line_image = np.copy(image)*0
    # Iterate over the output "lines" and draw lines on the blank

    left_x = []
    left_y = []
    right_x = []
    right_y = []
    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                slope = np.abs((y2 - y1) / (x2 - x1))
                if(slope > .5):
                    if (x1 < x2 and y1 > y2) or (x2 < x1 and y2 > y1) :
                        # left line
                        left_x.append(x1)
                        left_x.append(x2)
                        left_y.append(y1)
                        left_y.append(y2)
                    else:
                        # right line
                        right_x.append(x1)
                        right_x.append(x2)
                        right_y.append(y1)
                        right_y.append(y2)

    top_left_y = int(imshape[0] * y_cut)
    if(len(left_x) and len(left_y)):
        left_slope, left_intersect = np.polyfit(left_x, left_y, 1)
        bottom_left_x = int((imshape[0] - left_intersect) / left_slope)
        top_left_x = int((top_left_y - left_intersect) / left_slope)
        prev_bottom_left_x = bottom_left_x
        prev_top_left_x = top_left_x
    else:
        bottom_left_x = prev_bottom_left_x
        top_left_x = prev_top_left_x


    top_right_y = int(imshape[0] * y_cut)
    if (len(right_x) and len(right_y)):
        right_slope, right_intersect = np.poly1d(np.polyfit(right_x, right_y, 1))
        bottom_right_x = int((imshape[0] - right_intersect) / right_slope)
        top_right_x = int((top_right_y - right_intersect) / right_slope)
        prev_bottom_right_x = bottom_right_x
        prev_top_right_x = top_right_x
    else:
        bottom_right_x = prev_bottom_right_x
        top_right_x = prev_top_right_x


    draw_lines(line_image, [[[bottom_left_x, imshape[0], top_left_x, top_left_y],
                            [bottom_right_x, imshape[0], top_right_x, top_right_y]]], thickness=10)



    # Create a "color" binary image to combine with line image
    ##color_edges = np.dstack((masked, masked, masked))


    # Draw the lines on the edge image
    full_image = cv2.addWeighted(image, 0.7 , line_image, 1, 0)
    return full_image


white_output = 'solidYellowLeft-output.mp4'
clip1 = VideoFileClip("solidYellowLeft.mp4")
white_clip = clip1.fl_image(process_image) #NOTE: this function expects color images!!
white_clip.write_videofile(white_output, audio=False,fps=25,codec='mpeg4')

