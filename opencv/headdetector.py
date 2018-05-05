from __future__ import print_function
from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2

MAXSIZE=(320,240)

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--images", required=True, help="path to images directory")
args = vars(ap.parse_args())

# initialize the HOG descriptor/person detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
#hog.setSVMDetector("cascadeH5.xml")

cas1 = cv2.CascadeClassifier('HS.xml')
cas2 = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
cas3 = cv2.CascadeClassifier('haarcascade_profileface.xml')
cas4 = cv2.CascadeClassifier('haarcascade_upperbody.xml')
cas5 = cv2.CascadeClassifier('cascadeH5.xml')

cas = [cas1,cas2,cas3,cas4,cas5]

# loop over the image paths
i=0
for imagePath in paths.list_images(args["images"]):
	image = cv2.imread(imagePath)
	if image.shape[1]>MAXSIZE[0]:
		image = cv2.resize(image,MAXSIZE)
	orig = image.copy()
	image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	i+=1
	cn = 0
	for c in cas:
		print ("---- cascade number %i" % (cn))
		cn+=1
		rects = c.detectMultiScale(image, 1.3,3)
		rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
		pick = non_max_suppression(rects, probs=None, overlapThresh=0.65)
		for (xA, yA, xB, yB) in pick:
			cv2.rectangle(orig, (xA, yA), (xB, yB), (0, 255, 0), 2)

		filename = imagePath[imagePath.rfind("/") + 1:]
		print("[INFO] {}: {} original boxes".format(filename, len(rects)))
		if len(rects)>0:
			print( " +++++++++ saving")
			cv2.imwrite("result"+str(i)+".jpg",orig)
