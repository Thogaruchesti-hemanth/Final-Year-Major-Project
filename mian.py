# import the necessary packages
import numpy as np
import argparse
import imutils
import time
import cv2
import os
import winsound
import time


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
##ap.add_argument("-i", "--input", required=True,
##	help="path to input video")
ap.add_argument("-c", "--confidence", type=float, default=0.5,
        help="minimum probability to filter weak detections")
ap.add_argument("-t", "--threshold", type=float, default=0.3,
        help="threshold when applyong non-maxima suppression")
args = vars(ap.parse_args())

# load the COCO class labels our YOLO model was trained on
labelsPath = os.path.sep.join(["obj.names"])
LABELS = open(labelsPath).read().strip().split("\n")

# initialize a list of colors to represent each possible class label
np.random.seed(42)
COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
        dtype="uint8")

# derive the paths to the YOLO weights and model configuration
weightsPath = os.path.sep.join(["yolov3.weights"])
configPath = os.path.sep.join(["yolov3.cfg"])

# load our YOLO object detector trained on COCO dataset (80 classes)
# and determine only the *output* layer names that we need from YOLO
print("[INFO] loading YOLO from disk...")
net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)
ln = net.getLayerNames()
ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]
def beep1():
                
        frequency = 400  
        duration = 600  
        winsound.Beep(frequency, duration)
# initialize the video stream, pointer to output video file, and
# frame dimensions

fgbg = cv2.createBackgroundSubtractorMOG2()
vs= cv2.VideoCapture(0)
count=0
j=0

writer = None
(W, H) = (None, None)

# try to determine the total number of frames in the video file
try:
        prop = cv2.cv.CV_CAP_PROP_FRAME_COUNT if imutils.is_cv2() \
                else cv2.CAP_PROP_FRAME_COUNT
        total = int(vs.get(prop))
        print("[INFO] {} total frames in video".format(total))

# an error occurred while trying to determine the total
# number of frames in the video file
except:
        print("[INFO] could not determine # of frames in video")
        print("[INFO] no approx. completion time can be provided")
        total = -1

# loop over frames from the video file stream
while True:
        # read the next frame from the file
        (grabbed, frame) = vs.read()
        img=frame.copy()
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        fgmask = fgbg.apply(gray)
        #cv2.imshow('gray video',gray)
        #human detection
        #Find contours
        contours,hierchy = cv2.findContours(fgmask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)


        if contours:
             areas = []

        for contour in contours:
            ar = cv2.contourArea(contour)
            areas.append(ar)

        max_area = max(areas or [0])

        max_area_index = areas.index(max_area)

        cnt = contours[max_area_index]

        M = cv2.moments(cnt)

        x, y, w, h = cv2.boundingRect(cnt)
        if h < w:
        #if h == h/2:
            j += 1
            
        if j > 5:
            
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,0,255),2)
            
            cv2.putText(frame, 'ABnormal activity found falling down', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (0), 2)
            
            print ("FALL")
            cv2.drawContours(fgmask, [cnt], 0, (0,0,255), 3, maxLevel = 0)
            beep1()

        if h > w:
            j = 0 
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
            cv2.putText(frame, 'Normal Human Behavior', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (255), 2)
            



            
    
        
        # if the frame was not grabbed, then we have reached the end
        # of the stream
        if not grabbed:
                break

        # if the frame dimensions are empty, grab them
        if W is None or H is None:
                (H, W) = frame.shape[:2]

        # construct a blob from the input frame and then perform a forward
        # pass of the YOLO object detector, giving us our bounding boxes
        # and associated probabilities
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416),
                swapRB=True, crop=False)
        net.setInput(blob)
        start = time.time()
        layerOutputs = net.forward(ln)
        end = time.time()

        # initialize our lists of detected bounding boxes, confidences,
        # and class IDs, respectively
        boxes = []
        confidences = []
        classIDs = []

        # loop over each of the layer outputs
        for output in layerOutputs:
                # loop over each of the detections
                for detection in output:
                        # extract the class ID and confidence (i.e., probability)
                        # of the current object detection
                        scores = detection[5:]
                        classID = np.argmax(scores)
                        confidence = scores[classID]

                        # filter out weak predictions by ensuring the detected
                        # probability is greater than the minimum probability
                        if confidence > args["confidence"]:
                                # scale the bounding box coordinates back relative to
                                # the size of the image, keeping in mind that YOLO
                                # actually returns the center (x, y)-coordinates of
                                # the bounding box followed by the boxes' width and
                                # height
                                box = detection[0:4] * np.array([W, H, W, H])
                                (centerX, centerY, width, height) = box.astype("int")

                                # use the center (x, y)-coordinates to derive the top
                                # and and left corner of the bounding box
                                x = int(centerX - (width / 2))
                                y = int(centerY - (height / 2))

                                # update our list of bounding box coordinates,
                                # confidences, and class IDs
                                boxes.append([x, y, int(width), int(height)])
                                confidences.append(float(confidence))
                                classIDs.append(classID)

        # apply non-maxima suppression to suppress weak, overlapping
        # bounding boxes
        idxs = cv2.dnn.NMSBoxes(boxes, confidences, args["confidence"],
                args["threshold"])

        # ensure at least one detection exists
        if len(idxs) > 0:
                # loop over the indexes we are keeping
                for i in idxs.flatten():
                        # extract the bounding box coordinates
                        (x, y) = (boxes[i][0], boxes[i][1])
                        (w, h) = (boxes[i][2], boxes[i][3])

                        # draw a bounding box rectangle and label on the frame
                        color = [int(c) for c in COLORS[classIDs[i]]]
                        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                        text = "{}: {:.4f}".format(LABELS[classIDs[i]],
                                confidences[i])
                        cv2.putText(frame, text, (x, y - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        beep1()
        cv2.imshow('outputWindows',frame)
        if cv2.waitKey(10) & 0xFF == ord('q'):# Press 'ESC' for exiting video
                break 
        

# release the file pointers
print("[INFO] cleaning up...")
vs.release()
cv2.destroyAllWindows()
