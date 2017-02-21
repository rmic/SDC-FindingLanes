#**Project 1 : Finding Lane Lines on the Road** 

Author: Raphaël Michel
Email : raph.mic@gmail.com

The goals / steps of this project are the following:
* Make a pipeline that finds lane lines on the road
* Reflect on the work in a written report


[//]: # (Image References)
[contrast-before]: ./images/contrast-before.png "Before contrast"
[contrast-after]: ./images/contrast-after.png "After contrast"
[result1]: ./images/white-output.png "Lane lines - provided video"
[result2]: ./images/yellow-output.png "Lane lines - provided video"
[result3]: ./images/challenge-output.png "Lane lines - challenge video"
[result4]: ./images/result-namur-1.png "Lane lines - self-made video"
[result5]: ./images/result-namur-2.png "Lane lines - self-made video"
---

## Pipeline Description

My pipeline consisted of the following steps: 

#### Converting to grayscale and blurring to remove small unwanted artefacts
The grayscale conversion makes it easier to work with the images, reduces the overall memory footprint and evens out / flattens small color differences. 

Blurring was done using a Gaussian blur with a 13x13px kernel. It easily removes small unwanted artefacts on or next to the lane that may show up when detecting edges.

#### Increasing contrast by pushing the highlights 
 
 This step is not absolutely necessary on the videos provided for the project, because they were filmed during a bright sunny day, the image is very well lit, the colors appear very nicely.
  
On test videos I filmed myself during days of bad weather, the distinction between the gray of the road and the white of the road markings is not as sharp, this really helps to make the markings stand out and be better detected during the next step.

![before][contrast-before] ![after][contrast-after]

####  Detecting the edges using a canny edge detector

This step detects the edges of the shapes that we see on the picture.
The challenge here is to find adequate threshold values. I started with the values given during the video lectures (50 and 150), and fiddled around to see if changing them brought any improvement, but, on the provided videos, these seemed to be a good working basis. 

#### Masking the unwanted parts of the image

At this stage, we apply a mask to filter out most of the parts of the image that are not relevant to the detection of lane lines. This basically boils down to creating a polygon around the lane lines. In the code, the polygon is defined by the variable named `vertices`, which is defined as follows

```
# y_cut determines the height under which the lanes are detected 
# in this case, 38% located at the bottom of the image.
y_cut = .62
vertices = np.array([[ (0, imshape[0]),            # bottom left
                           (imshape[1] * .45, imshape[0] * y_cut),  # top left
                           (imshape[1] * .55, imshape[0] * y_cut),  # top right
                           (imshape[1], imshape[0]) ]],  # bottom right
                          dtype=np.int32)
```
![masking][mask]

#### Detecting lines using a hough line detector

This step detects the lines that were drawn by the canny edge detector, and returns the ends of the segments. The lines are detected using different parameters.
* rho and theta were kept at the values which I had set during the lessons (respectively 2 and PI/90), which worked fine.
* threshold : I chose the value 15 by trial and error, it includes the most probable lines and filters out some  unwanted artefacts
* min_line_length : I set this value to 200, to have a sufficiently long line so that it excludes everything that would probably not be a lane line, but still includes the striped lines.
* max_line_gap : I set this value to 150. My initial intuition was that if set sufficiently high, it would help to close the gap between the stripes, but then it created lines that weren't those I searched for, so I reduced it back to 150, so that it allows some imperfection in the lane lines, and still detect them.

#### Filtering and classifying the lines

Despite the precautions taken (masking, etc...) and the choice of the parameters, the hough lines detector still detects unwanted lines (especially in the challenge video, as well as in home-made videos). The main idea in filtering out these unwanted lines is that most of them are not roughly parrallel to the lane lines. I computed the slope of each line found during the hough transform and discarded all those that had a slope (in absolute value)  lower than 0.5. I then classified the remaining lines in either left or right lane line on basis of the position of one point relative to the other. I could have used the slope to do this classification but I was not certain that the algorithm always returned the point closest to the origin before the other one.

#### Fitting and drawing two lines (one for each side of the lane)
 
 The hough lines detector returns the ends of the segments it detects. More over, it can return several segments for each lane line instead of a long line. The goal here was to find single line for each side, that would 1) follow the path formed by the points returned by the hough lines and 2) go all the way from the bottom of the image up to the detection horizon (the `y_cut` variable)

The method I chose to build the line was simply to take all the points for each side, and fit a line using the `polyfit` function of numpy, and then draw them on top of the original video.


### Results

#### Provided videos

![White lines][result1] ![Yellow lines][result2]  ![Challenge][result3] 

#### Self made videos

![Namur 1][result4] ![Namur 2][result5]  
### Reflection

#### Potential shortcomings

* Change of conditions such as the road material or the marking color, gray weather, rain, snow, night conditions driving, etc.), change the specificities of the image, such as the colors and contrast, or may even hide markings or edges.
* The detected lines are shaky under 'difficult' conditions, such as when the contrast is not sufficient, when there is a lot of noise, or when lines aren't straight lines.
* Curvy lines are not detected correctly. By design we fit a straight line across the points provided by the hough transform. When the curve is has a large radius the straight lines may be acceptable, but with a shorter radius, the lines would not follow the road accurately.
* Some roads have no line at all. This pipeline will probably fail at detecting the boundaries of the road accurately.
* This pipeline uses a limited detection horizon. There is more information on the image than what we really use. In this code, we cut and use the lower 38% of the image, but there could be more information above that line that remains unexploited.
* Simiarly to the previous point, the pipeline is impacted by the angle at which the camera is pointed, if it aims too low, much of the lower part of the image may be taken by the front of the car and contain a short part of the road. If it is not aligned correctly, too much to the left or to the right, one of the lines may not be detected.
* It is easily blinded by obstacles, if there is a car close enough in front of the camera, the detection may not be accurate.
* The pipeline makes a series of operations on each frame of the video, and the output rate may be insufficient for annotating a video stream in real time at 25fps or more. This is, in fact debatable. Do we really need 25+ fps (and  detect a change in 0.04s or less) for a car moving within the authorized speed limits ? Maybe.

#### Possible improvements

* Detect conditions based on the image colors, and adapt the pipeline steps and its parameters accordingly.
* Smoothing the lines movements using, for example, a moving average over a short time frame to limit shakiness.
* Use different algorithms to detect and draw curvy lines rather than straight lines. 
* Roads without any line drawn on the ground may require a slightly different approach, or a parameter tuning.
* About the angle problem, that could be detected relatively quickly, and the region of interest could be recomputed if needed.
* Eliminate useless steps, reduce image size, and introduce masking regions earlier may help to speed up the overall operation.
