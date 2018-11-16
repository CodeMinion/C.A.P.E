import argparse
import imutils
import cv2
import numpy as np
import ntpath
import os
import json

BODER_PADDING = 10 # Additional padding in pixels to add to the page for handling unclosed panels.
MASK_SIZE = 15
MAX_PANELS_IN_PAGE = 15 #9
COMIC_PANEL_FORMAT_VERSION = 1;

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
		
	#print hist
	
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
	resized = imutils.resize(image, width=image.shape[1]/2)
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
		thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV)[1]
		#thresh = cv2.threshold(blurred, maxColorIndex, 255, cv2.THRESH_BINARY_INV)[1]
	else:
		# Use this for standard pages that have white borders. 
		thresh = cv2.threshold(blurred, maxColorIndex-1, 255, cv2.THRESH_BINARY)[1]
	
	
	if debug:
		cv2.imshow("Image", thresh)
		cv2.waitKey(0)
		
	goal = 4 # desired arbitrary panel count 
	comicPanels = findBestPanels(image, resized, thresh, ratio, goal, 0, 4)
	
	print isGoodLayout(comicPanels, image.shape)
	
	# Reverse to get a left to right ordering of the panels
	comicPanles = comicPanels.reverse()
	
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
		
		# Make a bounding box around the panel
		x,y,w,h = cv2.boundingRect(c);
			
		cv2.rectangle(blank_image, (x,y), (x+w, y+h), (0, 255, 0), -1)
		
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
	
		panelShapes.append((rect, c))
	
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
		
		#cv2.imshow("Image", image)
		#cv2.waitKey(0)
		
	outPath = "res_"+ntpath.basename(comicPanelPath)

	filename = os.path.basename(comicPanelPath)
	filenameNotExt = os.path.splitext(filename)[0]
	
	metaDataDest = os.path.splitext(comicPanelPath)[0]+".cpanel"
	
	panelMetadata = generatePanelMetadata(comicPanels)
	
	metaDataFile = open(metaDataDest, "w")
	metaDataFile.write(panelMetadata)
	
	print outPath
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
	
	
	json_data = json.dumps(data)
	
	return json_data
	
	
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
		
		
	'''
	# Size of the border to add to the comic page to handle unclosed panels.
	border_padding = 10
	
	resized = imutils.resize(image, width=300)
	ratio = image.shape[0] / float(resized.shape[0])
	
	isBlackBordered = hasDarkBorders(resized, 50)
	
	print isBlackBordered
	
	borderColor = [255,255,255]
	if isBlackBordered:
		borderColor = [0,0,0] 
	
	# Put back to handle unclosed panels.
	resized = cv2.copyMakeBorder(resized,
		border_padding, border_padding,
		border_padding, border_padding, cv2.BORDER_CONSTANT, value=borderColor)
	
	#ratio = image.shape[0] / float(resized.shape[0])
	
	# convert the resized image to grayscale, blur it slightly,
	# and threshold it
	gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
	blurred = gray
	#blurred = cv2.GaussianBlur(gray, (5, 5), 0)
	
	
	if isBlackBordered:
		# Use this for pages that have black borders.
		thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV)[1]
	else:
		# Use this for standard pages that have white borders. 
		thresh = cv2.threshold(blurred, 240, 255, cv2.THRESH_BINARY)[1]
	
	#comicPanels = findComicPanels(thresh, ratio, 1)
	
	'''
	
	'''	
	# TODO Perform a few retires if the number of produced panels is less than some 
	# average until it reaches the maximum dilation
	# Erode to remove separete mixed panels.
	kernel = np.ones((2,2),np.uint8)
	dilation = cv2.dilate(thresh,kernel,iterations = 1)#4) // Dialation ranges from 1 to 4.
	eroded = dilation
	#eroded = cv2.erode(dilation,kernel,iterations = 1)
	
	cv2.imshow("Eroded", eroded);
	cv2.waitKey(0)
	
	# find contours in the thresholded image and initialize the
	# shape detector
	#cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
	#	cv2.CHAIN_APPROX_SIMPLE)
	#cnts = cnts[0] if imutils.is_cv2() else cnts[1]	
	
	im2, cnts, hierarchy = cv2.findContours(eroded.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE )
	cv2.drawContours(resized, cnts, -1, (0,255,0), 3)
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
		
		# Make a bounding box around the panel
		x,y,w,h = cv2.boundingRect(c);
		
		# If we have a contour large enough to encapsulate over 60% of the image
		# than chance are a master contour of the page so skip it.
		#if(w > 0.66 *blank_image.shape[0] and h > 0.66 * blank_image.shape[1]):
		#	continue
		
		
		cv2.rectangle(blank_image, (x,y), (x+w, y+h), (0, 255, 0), -1)
		
		cv2.imshow("Image", blank_image)
		cv2.waitKey(0)

	#-----
	
	# Use the newley generated image with the boxes to find new contours
	gray = cv2.cvtColor(blank_image, cv2.COLOR_BGR2GRAY)
	thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)[1]
	cv2.imshow("Image", thresh)
	cv2.waitKey(0)
	
	im2, cnts, hierarchy = cv2.findContours(thresh.copy(),cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)#cv2.CHAIN_APPROX_NONE )
	cv2.drawContours(resized, cnts, -1, (0,255,0), 2)
	cv2.imshow("Image", resized)
	cv2.waitKey(0)
	
	hierarchy = hierarchy[0] # get the actual inner list of hierarchy descriptions
	
	panelShapes = []
	
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
		
			
		# compute the center of the contour, then detect the name of the
		# shape using only the contour
		M = cv2.moments(c)
		cX = int((M["m10"] / M["m00"]))
		cY = int((M["m01"] / M["m00"]))
		
		#cX = int((M["m10"] / M["m00"]) * ratio)
		#cY = int((M["m01"] / M["m00"]) * ratio)
		
		# multiply the contour (x, y)-coordinates by the resize ratio,
		# then draw the contours and the name of the shape on the image
		#print c
		#print c
			
		c = c.astype("float")
		c *= ratio
		c = c.astype("int")
		#cv2.drawContours(image, [c], -1, (0, 255, 0), 2)
		
		# Make a bounding box around the panel
		x,y,w,h = cv2.boundingRect(c);
		
		x -= int((border_padding * ratio))
		y -= int((border_padding * ratio))
		
		if x < 0:
			x = 0
			
		if y < 0:
			y = 0
		
		
		# If we have a contour large enough to encapulate over 60% of the image
		# than chance are a master contour of the page so skip it.
		#if(w > 0.66 *image.shape[0] and h > 0.66 * image.shape[1]):
		#	continue
		
		cv2.rectangle(image, (x,y), (x+w, y+h), (0, 255, 0), 2)
		
		#image = cv2.resize(image,None,fx=0.4, fy=0.4, interpolation = cv2.INTER_LINEAR)
		#cv2.namedWindow( "Image", cv2.WINDOW_AUTOSIZE );
		# show the output image
		cv2.imshow("Image", image)
		cv2.waitKey(0)

	cv2.imwrite('result.png',image)	
'''	