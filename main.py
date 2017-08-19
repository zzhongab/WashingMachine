# author: Caton ZHONG Zixuan
# updated at: 2017-08-02

import cv2
import numpy as np
import json
import time
import os
import commands
import re
import send_email
import requests
import socket
import urllib2

# Time for a whole cycle
cycle_time = 15

# Number of frames to throw away while the camera adjusts to light levels
ramp_frames = 30

# Initialize the counter so that we can give different names to images
num = 1

cropped_path = '/home/ustone/cropped.jpg'

# Load the conf file
#conf = '/home/caton/conf.json'


# initial prev_remaining_minutes to -1
prev_remaining_minutes = -1



def internet_on():
    try:
        urllib2.urlopen('https://www.google.com.hk', timeout=1)
        return True
    except urllib2.URLError as err: 
        return False  


# local log
def local_log(text):
    new_content = '['+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()) +']  '+text + '\n'
    with open('/home/ustone/log.txt', 'a+') as f:
        f.write(new_content)
    f.close()

# http log
def http_log(text):
    new_content = '['+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()) +']  '+text + '\n'
    with open('/home/ustone/http_log.txt', 'a+') as f:
        f.write(new_content)
    f.close()

# error log
def error_log(text):
    new_content = '['+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()) +']  '+text + '\n'
    with open('/home/ustone/error_log.txt', 'a+') as f:
        f.write(new_content)
    f.close()

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('google.com.hk', 0))
    return s.getsockname()[0]

def get_image():
# read is the easiest way to get a full image out of a VideoCapture object.
    retval, im = camera.read()
    return im

# Rotate the image given an angle
def rotate_bound(image, angle):
    # grab the dimensions of the image and then determine the
    # center
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
 
    # grab the rotation matrix (applying the negative of the
    # angle to rotate clockwise), then grab the sine and cosine
    # (i.e., the rotation components of the matrix)
    M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
 
    # compute the new bounding dimensions of the image
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
 
    # adjust the rotation matrix to take into account translation
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
 
    # perform the actual rotation and return the image
    return cv2.warpAffine(image, M, (nW, nH))

def process_image(image_path,crop_,illumination_):
    # Read the image
    img=cv2.imread(image_path)

    # Rotate image
    img=rotate_bound(img,90)

    # Transform image
    # pts1 = np.float32([[0,110],[480,0],[0,640],[480,400]])
    pts1 = np.float32([[crop_[4],crop_[0]],[crop_[5],crop_[1]],[crop_[4],640-crop_[2]],[crop_[5],640-crop_[3]]])
    pts2 = np.float32([[0,0],[640,0],[0,480],[640,480]])
    M = cv2.getPerspectiveTransform(pts1,pts2)
    img = cv2.warpPerspective(img,M,(640,480))

    cv2.imwrite(cropped_path,img)

    # Blur the image
    img = cv2.blur(img,(5,5))

    # Convert BGR to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Define range of green color in HSV
    lower_green = np.array([0,0,illumination_])
    upper_green = np.array([150,255,255])

    # Threshold the HSV image to get only bright part
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # Bitwise-AND mask and original image
    res = cv2.bitwise_and(img,img, mask=mask)

    # Convert BGR to GRAY
    res = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)

    # Define kernel and process image
    kernel = np.ones((2,2),np.uint8)
    res=cv2.erode(res, kernel, iterations=5)
    res=cv2.dilate(res, kernel, iterations=3)
    res=cv2.erode(res, kernel, iterations=erode_times)
    res=cv2.dilate(res, kernel, iterations=4)


    # rotate 
    res = rotate_bound(res,ssocr_rotate)

    # Convert to black-and-white
    cv2.bitwise_not(res,res)

    # Save the image
    #path = "/home/caton/images_bw/" + image_name
    output_path = "/home/ustone/output.png"
    cv2.imwrite(output_path,res)
    return output_path




# The working loop
while True:
    conf = '/home/ustone/conf.json'
    with open(conf, 'r') as json_file:
        json_data=json_file.read().replace('\n', '')
    conf_json = json.loads(json_data)

    crop = conf_json['crop']
    illumination = conf_json['illumination']
    machine_type = conf_json['type']
    token = conf_json['token']
    machine_id = conf_json['id']
    ssocr_rotate = conf_json['ssocr_rotate']
    erode_times = conf_json['erode']
    # internet
    while(internet_on()==False):
        time.sleep(2)
    # set ERROR to false
    ERROR = False
    # Record the starting time
    start_time = time.time()
    
    # Save at most 300 pictures
    num = num % 300
     
    # Now we can initialize the camera capture object with the cv2.VideoCapture class.
    # All it needs is the index to a camera port.
    camera = cv2.VideoCapture(0)
    camera.set(3,640)
    camera.set(4,480)
     
    # Captures a single image from the camera and returns it in PIL format
    for i in xrange(ramp_frames):
        temp = get_image()
    # Take the actual image we want to keep
    camera_capture = get_image()
    image_path = "/home/ustone/images/" + str(num) + ".jpg"
    # A nice feature of the imwrite method is that it will automatically choose the
    # correct format based on the file extension you provide. Convenient!
    try:
        os.remove(image_path)
    except OSError:
        pass

    camera_capture = cv2.resize(camera_capture, (640, 480))
    cv2.imwrite(image_path, camera_capture)

    # Release the camera
    del(camera)
   


    # TODO: remove hardcode here 
    # image_path="/home/ustone/sample.jpg"


    output_path = process_image(image_path,crop,illumination)

    # Get the output of the screen
    '''To be modified during the installation process'''
    ssocr_output = commands.getoutput("/usr/local/bin/ssocr -T -d -1 " + output_path)
    local_log('ssocr: '+ssocr_output)
    # Get the numeric string
    digits = re.sub("[^0-9]", "", ssocr_output)
    # check the length of recognized digits string
    if (len(digits) == 0):
        # no pixel
        if(ssocr_output[:4] == 'iter'):
            OCCUPIED = True
            remaining_minutes = 0
        # no digit
        else:
            OCCUPIED = False
            remaining_minutes = -1
            ERROR = True
            ERROR_CODE = "no recognized digits"
    
    # only one digit
    elif(len(digits) == 1):
        OCCUPIED = False
        remaining_minutes = -1
        ERROR = True
        ERROR_CODE = "length of recognized digits is only 1"

    # maybe right
    elif (len(digits) == 2 and len(ssocr_output) == 2):
        # skip 8
        if('8' in ssocr_output and abs(prev_remaining_minutes-int(digits))>1):
            OCCUPIED = False
            remaining_minutes = -1 
        # strange characters
        elif('_' in ssocr_output or '-' in ssocr_output):
            OCCUPIED = False
            remaining_minutes = -1 
            ERROR = True
            ERROR_CODE = "strange character in ssocr"
        # right
        else:
            OCCUPIED = True
            remaining_minutes = int(digits)

    elif(len(digits) == 2 and len(ssocr_output) > 2):
        # skip 8
        if('8' in ssocr_output and abs(prev_remaining_minutes-int(digits))>1):
            OCCUPIED = False
            remaining_minutes = -1 
        # not allow _ and -
        elif('_' in ssocr_output or '-' in ssocr_output):
            OCCUPIED = False
            remaining_minutes = -1 
            ERROR = True
            ERROR_CODE = "strange character in ssocr"
        # give chance to .
        elif('.' in ssocr_output and abs(prev_remaining_minutes-int(digits))<=1):
            OCCUPIED = True
            remaining_minutes = int(digits)
        # strange characters
        else:
            OCCUPIED = False
            remaining_minutes = -1 
            ERROR = True
            ERROR_CODE = "strange character in ssocr"
    else:  
        OCCUPIED = False
        remaining_minutes = -1
        ERROR = True
        ERROR_CODE = "length of recognized digits string is greater than 2"



    '''
    CHECK ERROR
    '''
    if(remaining_minutes!=-1):
        # number too large
        if(machine_type == "washer" and remaining_minutes>34):
            OCCUPIED = False
            ERROR = True
            ERROR_CODE = "number too large"
        # greater than that of last one
        if ((remaining_minutes>prev_remaining_minutes )and (prev_remaining_minutes!=-1)):
            OCCUPIED = False
            ERROR = True
            ERROR_CODE = "number of remianing minutes is greater than that in last minute"
        # maybe one digit missed 
        if (prev_remaining_minutes-remaining_minutes >5):
            OCCUPIED = False
            ERROR = True
            ERROR_CODE = "maybe one digit is missed"
        # less than last one by too many
        if (prev_remaining_minutes-remaining_minutes >2 and prev_remaining_minutes-remaining_minutes<=5 ):
            OCCUPIED = False
            ERROR = True
            ERROR_CODE = "number of remianing minutes is less than that in last minute by more than TWO"

    # Update prev_remaining_minutes
    prev_remaining_minutes = remaining_minutes

    '''
    REPORT ERROR IF NEEDED
    '''


    # report ERROR
    if(ERROR == True):
        send_email.log("ERROR",image_path,cropped_path,output_path,ssocr_output,ERROR_CODE)
        error_log(ssocr_output+"   "+ERROR_CODE)

    # send data to server
    if(OCCUPIED == True):
        url = 'http://188.166.220.165/api/update-machine'
        payload = {'machine_id': machine_id,'token':token,'remaining_minutes':remaining_minutes,'ip':get_ip(),"Content-Type": "application/json"}
        headers = {'Content-Type': 'application/jsons'}
        response = requests.post(url, data=json.dumps(payload),headers=headers)
        if (response.status_code == 200):
            conf_json = response.json()
            with open('/home/ustone/conf.json', 'w') as f:
                json.dump(response.json(), f)
            http_log('response: '+json.dumps(response.json()))

    else:
        url = 'http://188.166.220.165/api/update-machine'
        payload = {'machine_id': machine_id,'token':token,'remaining_minutes':-1,'ip':get_ip(),"Content-Type": "application/json"}
        headers = {'Content-Type': 'application/jsons'}
        response = requests.post(url, data=json.dumps(payload),headers=headers)
        if (response.status_code == 200):
            conf_json = response.json()
            with open('/home/ustone/conf.json', 'w') as f:
                json.dump(response.json(), f)
            http_log('response: '+json.dumps(response.json()))

    # send images to server
    send_email.web_images(image_path,cropped_path,output_path,ssocr_output)


    
    # Increase the counter
    num = num + 1
    
    # calculate the sleeping time
    total_time = cycle_time
    while(total_time<(time.time() - start_time)):
        total_time = total_time + cycle_time
    # Get the sleeping time
    sleep_time = total_time-(time.time() - start_time)

    if(sleep_time>0):
        time.sleep(sleep_time)
    else:
        time.sleep(cycle_time)

error_log('jump out of the loop')



