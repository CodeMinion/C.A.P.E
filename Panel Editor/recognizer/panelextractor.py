import argparse
import imutils
import cv2
import numpy as np
import ntpath
import os
import json
from PolygonUtils import *
from operator import itemgetter, attrgetter
from ComicPanel import ComicPanel


BODER_PADDING = 10 # Additional padding in pixels to add to the page for handling unclosed panels.
MASK_SIZE = 15
MAX_PANELS_IN_PAGE = 15 #9
COMIC_PANEL_FORMAT_VERSION = 2;
# Maximun allowed points in contour before it the panel is considered for re-evaluation
MAX_CONTOURS_IN_GOOD_PANEL = 4
# Arbitrary number of desired panels.
GOOD_PANELS_GOAL = 5
'''
Uses the image histogram to evaluate if the
comic page has dark borders or not.

https://docs.opencv.org/3.1.0/d1/db7/tutorial_py_histogram_begins.html

Process: Get the histogram of the image using
		the four corners of the image as input.
		Then we check if the predominant color
		is below the threshold. If so we consider
		the borders dark.

Note: Works best with gray scale images.

'''
def hasDarkBorders(image, threshold):
	mask = np.zeros(image.shape[:2], np.uint8)
	mask[:MASK_SIZE, :MASK_SIZE] = 255
	mask[-MASK_SIZE:, :MASK_SIZE] = 255
	mask[:MASK_SIZE, -MASK_SIZE:] = 255
	mask[-MASK_SIZE:, -MASK_SIZE:] = 255
	hist = cv2.calcHist([image],[0],mask,[256],[0,256])
	#cv2.imshow("Image", mask)
	#cv2.waitKey(0)

	# Find the most common color among all corners
	maxColorIndex = 0
	maxColorValue = -1
	for colorIndex, colorValue in enumerate(hist) :
		if colorValue > maxColorValue:
			maxColorIndex = colorIndex
			maxColorValue = colorValue

	print hist

	print maxColorIndex
	hasDarkBordered = maxColorIndex < threshold

	return hasDarkBordered, maxColorIndex

'''
Use the grays cale image histogram to check if
the image is largely bright.
@param theshImg binary image
@param percent of pixels needed in order to consider image bright. 0-100
'''
def isBrightPanel(theshImg, threshold):
	hist = cv2.calcHist([theshImg],[0],None,[256],[0,256])
	#cv2.imshow("Image", mask)
	#cv2.waitKey(0)

	# Find the most common color among all corners
	maxColorIndex = 0
	maxColorValue = -1
	for colorIndex, colorValue in enumerate(hist) :
		if colorValue > maxColorValue:
			maxColorIndex = colorIndex
			maxColorValue = colorValue

	#print hist

	maxColorPercent = (maxColorValue/(theshImg.shape[0]*theshImg.shape[1]))*100
	isBrightPanel = maxColorIndex > 0 and maxColorPercent > threshold

	print maxColorIndex, isBrightPanel, maxColorPercent

	return isBrightPanel, maxColorIndex

'''
Helper method to evaluate if the layout of panels is valid.
List of tuples of (rect, contour)
'''
def isGoodLayout(panels, pageDimensions):

	# We'll assume that if no comic panels detected overlap
	# then the sum of all the panel areas will be at most the
	# same area as the page. So if we end up with a larger
	# area then the page

	comicPageArea = pageDimensions[0] * pageDimensions[1]

	totalArea = 0
	for panel in panels:
		x,y,w,h = panel[0]
		totalArea += (w*h)


	return comicPageArea > totalArea

'''
Returns the panels in the given comic page inside image.
@param image - Comic page
@return tuble of rectangles and contours.
'''
def findComicPanels(image):

	# Size of the border to add to the comic page to handle unclosed panels.
	border_padding = BODER_PADDING
	resized = imutils.resize(image, width=image.shape[1]/3) # 2
	ratio = image.shape[0] / float(resized.shape[0])

	gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

	isBlackBordered, maxColorIndex = hasDarkBorders(gray, 50)

	print isBlackBordered, maxColorIndex

	borderColor = [255,255,255]
	if isBlackBordered:
		borderColor = [0,0,0]

	# Put back to handle unclosed panels.
	resized = cv2.copyMakeBorder(resized,
		border_padding, border_padding,
		border_padding, border_padding, cv2.BORDER_CONSTANT, value=borderColor)

	gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
	blurred = gray

	if debug:
		cv2.imshow("Gray", blurred)

	if isBlackBordered:
		# Use this for pages that have black borders.
		#thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV)[1]
		thresh = cv2.threshold(blurred, maxColorIndex+1, 255, cv2.THRESH_BINARY_INV)[1]
		#thresh = cv2.threshold(blurred, maxColorIndex, 255, cv2.THRESH_BINARY_INV)[1]
	else:
		# Use this for standard pages that have white borders.
		thresh = cv2.threshold(blurred, maxColorIndex-1, 255, cv2.THRESH_BINARY)[1]


	if debug:
		cv2.imshow("Image", thresh)
		cv2.waitKey(0)

	goal = GOOD_PANELS_GOAL #4 # desired arbitrary panel count $ Consider 5
	comicPanels = findBestPanels(image, resized, thresh, ratio, goal, 0, 4)

	print isGoodLayout(comicPanels, image.shape)

	# Reverse to get a left to right ordering of the panels
	#comicPanles = comicPanels.reverse()
	# Enhanced for sorting Manga.
	# Sort the panels from left ot right
	comicPanels = sorted(comicPanels, key=attrgetter('y','x'))

	return comicPanels


def findBestPanels(image, resized, thresh, ratio, goal, leftIternations, rightIterations):

	currentPanelCount = 0

	comicPanels = []

	bestIteration = 0

	isBright = isBrightPanel(thresh, 65)[0]

	while leftIternations < rightIterations:
		midIters = leftIternations + (rightIterations - leftIternations) / 2

		comicPanels = extractComicPanels(resized.copy(), thresh, ratio, midIters, isBright)
		print "Pass Completed "+ str(midIters)

		panelsFound = len(comicPanels)

		if panelsFound > bestIteration and panelsFound <= MAX_PANELS_IN_PAGE:
			bestIteration = midIters

		if isBright:
			if panelsFound == goal:
				return comicPanels
			elif not isGoodLayout(comicPanels, image.shape):
				rightIterations = midIters - 1
			elif panelsFound < goal:
				rightIterations = midIters - 1
			else:
				leftIternations = midIters

		else:

			if panelsFound == goal:
				return comicPanels
			elif not isGoodLayout(comicPanels, image.shape):
				leftIternations = midIters + 1
			elif panelsFound < goal:
				leftIternations = midIters + 1
			else:
				rightIterations = midIters

	comicPanels = extractComicPanels(resized.copy(), thresh, ratio, bestIteration, isBright)


	return comicPanels

# Check if a point is inside a rectangle
def rect_contains(rect, point) :
    if point[0] < rect[0] :
        return False
    elif point[1] < rect[1] :
        return False
    elif point[0] > rect[2] :
        return False
    elif point[1] > rect[3] :
        return False
    return True

# Draw delaunay triangles
def draw_delaunay(img, subdiv, delaunay_color ) :

    triangleList = subdiv.getTriangleList();
    size = img.shape
    r = (0, 0, size[1], size[0])

    for t in triangleList :

        pt1 = (t[0], t[1])
        pt2 = (t[2], t[3])
        pt3 = (t[4], t[5])

        if rect_contains(r, pt1) and rect_contains(r, pt2) and rect_contains(r, pt3) :

            cv2.line(img, pt1, pt2, delaunay_color,  3) #1, cv2.CV_AA, 0)
            cv2.line(img, pt2, pt3, delaunay_color,  3) #1, cv2.CV_AA, 0)
            cv2.line(img, pt3, pt1, delaunay_color,  3) #1, cv2.CV_AA, 0)

			#cv2.line(blank_image, (edge.u.x,edge.u.y), (edge.v.x, edge.v.y), (255, 0, 0), 3)

'''
A questionable panels is any panel
consider larger than expected. While there could be
panels that occupy a large part of the screen
most panels will not. So we are interested
in those large panels for extra processing
in case the large size is a result a failure in the
recognizer
'''
def isQuestinablePanel(x,y,w,h, image):
	panelArea = w * h
	imageArea = image.shape[0] * image.shape[1]

	return panelArea >= imageArea * 0.5

'''
Helper function to extract comic panels from a given comic page.
'''
def extractComicPanels(resized, thresh, ratio, iter, isBright):
	# TODO Perform a few retires if the number of produced panels is less than some
	# average until it reaches the maximum dilation
	# Erode to remove separete mixed panels.
	kernel = np.ones((2,2),np.uint8)

	if isBright:
		dilation = cv2.dilate(thresh,kernel,iterations = 1)
		eroded = cv2.erode(dilation,kernel,iterations = iter)

	else:
		dilation = cv2.dilate(thresh,kernel,iterations = iter) # // Dialation ranges from 1 to 4.
		eroded = dilation #thresh #dilation

	#dilation = cv2.dilate(thresh,kernel,iterations = 1)#4) // Dialation ranges from 1 to 4.
	#eroded = cv2.erode(dilation,kernel,iterations = iter) #thresh #dilation
	#eroded = cv2.erode(dilation,kernel,iterations = 1)

	if debug:
		cv2.imshow("Eroded", eroded);
		cv2.waitKey(0)

	im2, cnts, hierarchy = cv2.findContours(eroded.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE )

	cv2.drawContours(resized, cnts, -1, (0,255,0), 3)

	if debug:
		cv2.imshow("Image", resized)
		cv2.waitKey(0)

	hierarchy = hierarchy[0] # get the actual inner list of hierarchy descriptions

	width = resized.shape[0]
	blank_image = np.zeros((width, resized.shape[1], 3), np.uint8)
	blank_image[:,0:width] = (255,255,255)      # (B, G, R)

	# Use the initial contours to create an image of only bonding boxes
	# loop over the contours
	for component in zip(cnts, hierarchy):
		c = component[0]
		currentHeirarchy = component[1]

		# Skip top contour, this is the contour of the entire page
		# Hierarchy arr ->  [Next, Previous, First_Child, Parent]
		if currentHeirarchy[3] < 0:
			continue;

		# Skip the content of the panels, we only want the contour of the panels themselves.
		if currentHeirarchy[3] > 0:
			continue;

		#print approx;
		#c= approx;

		# Make a bounding box around the panel
		x,y,w,h = cv2.boundingRect(c);

		questinable = isQuestinablePanel(x,y,w,h, blank_image)

		print 'Image size'
		print blank_image.shape
		# Calculate the size of the smallest edge size to discard
		# We assume this to be left over edges connecting disconnected shapes.
		MIN_DISCARD_EDGE_LENGTH = blank_image.shape[1] * 0.07
		if questinable:
			# Perform extra processing
			epsilon = 0.001*cv2.arcLength(c,True);
			approx = cv2.approxPolyDP(c,epsilon,True);
			if len(approx) <= MAX_CONTOURS_IN_GOOD_PANEL:
				# Good panel, if it had subpanels the approximation would yeild more points
				# Draw the panel for the next phase
				cv2.rectangle(blank_image, (x,y), (x+w, y+h), (0, 255, 0), -1)
			else:
				gridSize = 5
				edges, nodes = getEdgesFromContour(approx, gridSize, gridSize, MIN_DISCARD_EDGE_LENGTH) # TODO Replace cut off point by fraction of the image
				graphs = findDisconnectedSubgraphs(nodes)
				for graphInfo in graphs:
					box = graphInfo[1]
					cv2.rectangle(blank_image, (box[0]+gridSize,box[1]+gridSize),
					(box[0]+box[2]-gridSize, box[1]+box[3]-gridSize), (255, 0, 255), -1)

				'''
				for edge in edges:
					cv2.line(blank_image, (edge.u.x,edge.u.y), (edge.v.x, edge.v.y), (255, 0, 0), 3)
					cv2.imshow("Image", blank_image)
					cv2.waitKey(0)
				'''
		else:

			# Draw the panel for the next phase
			cv2.rectangle(blank_image, (x,y), (x+w, y+h), (0, 255, 0), -1)

		#cv2.drawContours(blank_image, [approx], -1, (255,255,0), 3)


		#nodes = getNodesFromContour(approx)

		'''
			w = 4
			h = 4
			x = (n.x / 15) * 15
			y = (n.y / 15) * 15
			cv2.rectangle(blank_image, (x,y), (x+w, y+h), (255, 0, 0), -1)
			#cv2.imshow("Image", blank_image)
			#cv2.waitKey(0)
		'''

		'''
		# Subdivision
		points = []
		size = blank_image.shape
		rect = (0, 0, size[1], size[0])
		subdiv  = cv2.Subdiv2D(rect);
		for n in nodes:
			subdiv.insert((int(n.x), int(n.y)))

		draw_delaunay( blank_image, subdiv, (0, 255, 255) );
		'''
		if debug:
			cv2.imshow("Image", blank_image)
			cv2.waitKey(0)

		#cv2.imshow("Image", blank_image)
		#cv2.waitKey(0)

	if debug:
		cv2.imshow("Image", blank_image)
		cv2.waitKey(0)

	#-----


	# Use the newley generated image with the boxes to find new contours
	gray = cv2.cvtColor(blank_image, cv2.COLOR_BGR2GRAY)
	thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)[1]

	if debug:
		cv2.imshow("Image", thresh)
		cv2.waitKey(0)

	im2, cnts, hierarchy = cv2.findContours(thresh.copy(),cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)#cv2.CHAIN_APPROX_NONE )
	cv2.drawContours(resized, cnts, -1, (0,255,0), 2)

	if debug:
		cv2.imshow("Image", resized)
		cv2.waitKey(0)

	hierarchy = hierarchy[0] # get the actual inner list of hierarchy descriptions

	panelShapes = []

	border_padding = BODER_PADDING;

	originalW = int((resized.shape[1]-(border_padding*2))* ratio);
	originalH = int((resized.shape[0]-(border_padding*2))* ratio);

	# Assuming we can have very thin panels, this seems to be the best
	# amount that would allow for comfortable read.

	minAllowedPanelSize = (originalH * originalW) / MAX_PANELS_IN_PAGE

	# loop over the contours
	for component in zip(cnts, hierarchy):
		c = component[0]
		currentHeirarchy = component[1]

		# Skip top contour, this is the contour of the entire page
		# Hierarchy arr ->  [Next, Previous, First_Child, Parent]
		if currentHeirarchy[3] < 0:
			continue;

		# Skip the content of the panels, we only want the contour of the panels themselves.
		if currentHeirarchy[3] != 0:
			continue;

		c = c.astype("float")
		c *= ratio
		c = c.astype("int")

		# Make a bounding box around the panel
		x,y,w,h = cv2.boundingRect(c);


		x -= int((border_padding * ratio))
		y -= int((border_padding * ratio))

		#w -= int((border_padding * ratio))
		#h -= int((border_padding * ratio))

		deltaX = 0
		deltaY = 0
		if x < 0:
			x = 0

		if y < 0:
			y = 0

		# If the box would extend past the right and bottom of the image update width.
		if x + w > originalW:
			w = originalW - x

		if y + h > originalH:
			h = originalH  - y

		# Remove frames that are too small since they are probably not frames
		frameArea = w * h;
		if frameArea < minAllowedPanelSize:
			continue

		rect = (x,y, w, h)

		panelShapes.append(ComicPanel(rect, c))

	print len(panelShapes)

	return panelShapes

'''
Processes a single comic panel and places
the processed panels information in dest folder.
@param path to the comic panel file
@param dest dir where to store the panel resource.
'''
def processComicPanel(comicPanelPath, dest):

	image = cv2.imread(comicPanelPath)

	comicPanels = findComicPanels(image)

	for panelInfo in comicPanels:
		x,y, w, h = panelInfo[0]
		cv2.rectangle(image, (x,y), (x+w, y+h), (0, 255, 0), 5)

		#cv2.imshow("Output", image)
		#cv2.waitKey(0)

	outPath = "res_"+ntpath.basename(comicPanelPath)

	filename = os.path.basename(comicPanelPath)
	filenameNotExt = os.path.splitext(filename)[0]

	metaDataDest = os.path.splitext(comicPanelPath)[0]+".cpanel"

	panelMetadata = generatePanelMetadata(comicPanels)

	# Add image file name to improve linkage to the source image
	panelMetadata['imagePath'] = filename

	panelMetadata = json.dumps(panelMetadata)
	metaDataFile = open(metaDataDest, "w")
	metaDataFile.write(panelMetadata)

	print outPath

	if debug:
		cv2.imwrite(outPath,image)

'''
Given a comic panel data this function
generates the metadata file for the
comic page.
'''
def generatePanelMetadata(comicPanels):
	key_version = "version"
	key_shape = "shape"
	key_box = "box"
	key_x = "x"
	key_y = "y"
	key_width = "w"
	key_height = "h"
	key_panels = "panels"

	data = {}
	data['version'] = COMIC_PANEL_FORMAT_VERSION

	panels = []
	data[key_panels] = panels

	for panelInfo in comicPanels:
		x,y, w, h = panelInfo[0]
		box = { key_x:x,
				key_y: y,
				key_width:w,
				key_height:h
				}
		'''
		box[key_x] = x
		box[key_y] = y
		box[key_width] = w
		box[key_height] = h
		'''
		panel = {key_box: box}
		#panel[key_box] = box

		shape = []
		panel[key_shape] = shape

		# For every point in the contour make a new shape entry.
		contours = panelInfo[1]

		for cnt in contours:
			shapeEntry = { key_x: cnt[0][0], key_y: cnt[0][1]}
			shape.append(shapeEntry)

		panels.append(panel)


	#json_data = json.dumps(data)

	return data #json_data


'''
Processes every single comic page in the given directory.
@param comicDirPath - path of the source directory
@param dest - destination where to store the results
'''
def processComicPanelsFromDir(comicDirPath, dest):

	for filename in os.listdir(comicDirPath):
		if filename.endswith(".png") or filename.endswith(".jpg"):
			print filename
			processComicPanel(os.path.join(comicDirPath, filename), dest)

if __name__ == '__main__':

	# construct the argument parse and parse the arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--image", required=False,
		help="path to the input image")

	ap.add_argument("-d", "--image_dir", required=False,
		help="path to the input image directory")

	ap.add_argument("-v", "--verbose", required=False, action='store_true',
		help="Show debug images")


	args = vars(ap.parse_args())

	debug = args["verbose"]

	if args["image"] is not None:

		processComicPanel(args["image"], "")
		'''
		image = cv2.imread(args["image"])

		comicPanels = findComicPanels(image)

		for panelInfo in comicPanels:
			x,y, w, h = panelInfo[0]
			cv2.rectangle(image, (x,y), (x+w, y+h), (0, 255, 0), 2)

			#cv2.imshow("Image", image)
			#cv2.waitKey(0)

		outPath = "res_"+ntpath.basename(args["image"])

		print outPath
		cv2.imwrite(outPath,image)
		'''

	if args["image_dir"] is not None:
		processComicPanelsFromDir(args["image_dir"], "")
