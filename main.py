import threading
import cv2
import camera
import shelve
import numpy as np
import math
from win_printer import print_capabilities, print_image, init_printer,  open_printer, close_printer, get_printer_config
from qr_gen import gen_vouchers_codes, store_voucher_codes, init_vouchers
import win32con
import win32print
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol
from time import sleep, time
import configparser
import logging
from time import gmtime, strftime
import os.path
from ast import literal_eval as make_tuple
import re


def load_img(file,size):
    img= cv2.imread(file,cv2.IMREAD_UNCHANGED)
    if size != None:
        img = cv2.resize(img,size)
    x,y = img.shape[0:2]
    alpha = np.dstack((img[0:x,0:y,3],img[0:x,0:y,3],img[0:x,0:y,3]))
    return cv2.multiply(img[0:x,0:y,0:3],alpha / 255.0,dtype = 0), cv2.bitwise_not(alpha) / 255.0

def start_timer(time,func):
    t = threading.Timer(time,func)
    t.start()

def goto_scan():
    global state
    state = "scan"
    
def goto_init_countdown():
    global state
    state = "init_countdown"

def countdown():
    global countdown_val
    global conf
    countdown_val -= 1
    if countdown_val > 0:
        start_timer(conf.getfloat('countdown_t'),countdown)

def overlay(img,over):
    if over != None:
        overlay_img, overlay_img_beta_norm = over
        img = cv2.add(overlay_img  , cv2.multiply(img , overlay_img_beta_norm,dtype = 0) )
    return img

def add_pillar(img,pillar):
    display_img=pillar
    display_img[0:corr_camera_resolution[1],roi_width_shift:corr_camera_resolution[0]+roi_width_shift] = img  
    return display_img

def start(event, x, y, flags, param):
    global state
    if state == "idle" and event == cv2.EVENT_LBUTTONDOWN:
        state = "init_countdown"

def check_file_exists(fname):
    if os.path.isfile(fname) == False:
        logging.warning(fname+' Not found!')
        return False
    return True

logging.basicConfig(filename='photobooth.log',level=logging.DEBUG)
start_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
logging.info("---------- PhotoBooth started at "+start_time+" ----------")

conf = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
conf.read("config")
conf = conf['conf']
if conf['mode'] == "voucher":
    init_state = "scan"
elif conf['mode'] == "free":
    init_state = "idle"
else:
    logging.warning('No valid \'mode\' defined in config file.')
    exit()
state = init_state

all_files_exist = True
all_files_exist = all_files_exist and check_file_exists(conf.get('pillar_overlay'))
all_files_exist = all_files_exist and check_file_exists(conf['idle_overlay'])
all_files_exist = all_files_exist and check_file_exists(conf['scan_overlay'])
all_files_exist = all_files_exist and check_file_exists(conf['accept_overlay'])
all_files_exist = all_files_exist and check_file_exists(conf['deny_overlay'])
all_files_exist = all_files_exist and check_file_exists(conf['countdown_dir']+"1.png")
all_files_exist = all_files_exist and check_file_exists(conf['countdown_dir']+"2.png")
all_files_exist = all_files_exist and check_file_exists(conf['countdown_dir']+"3.png")
all_files_exist = all_files_exist and check_file_exists(conf['output_template'])
all_files_exist = all_files_exist and check_file_exists(conf['voucher_template'])
if all_files_exist == False:
    exit()
    
if conf.getint('num_v_generate') > 0:
    color1 = conf['color1']
    color2 = conf['color2']
    if color1 == "none" or color1 == "None":
        color1 = None
    else:
        tuple([x/255 for x in make_tuple("("+conf['color1']+")")])
    if color2 == "none" or color2 == "None":
        color2 = None
    else:
        tuple([x/255 for x in make_tuple("("+conf['color2']+")")])
    design = (conf.getfloat('qr_size'),color1,color2,conf['voucher_template'])
    print(design)
    init_vouchers(conf['voucher_key'],conf.getint('num_v_generate'),conf['voucher_path'],design,conf['v_pdf_path'])
    exit()


camera_resolution = make_tuple("("+conf['camera_res']+")")
corr_camera_resolution = (int(camera_resolution[1]*4/3),camera_resolution[1])
camera_offset = int((camera_resolution[0]-corr_camera_resolution[0])/2)
display_size  = make_tuple("("+conf['display_res']+")")
camera_aspect_ratio = camera_resolution[0]/camera_resolution[1]
display_aspect_ratio = (display_size[0]/display_size[1])

init_printer(conf['printer'],conf.getint('media_format'),win32con.DMORIENT_PORTRAIT)
printer_handle,pHandle =  open_printer(conf['printer'])
pconfig = get_printer_config(printer_handle)
print_img_size = (pconfig['PHYSICALWIDTH'],pconfig['PHYSICALHEIGHT'])
# Output template
template_img_file = "Print/9x6 inch/bicky_bier.png"
template_img_alpha_file = "Print/9x6 inch/bicky_bier_alpha.png"

m=re.findall("\d+.?\d+",conf['img_origins'])
i_org  = [make_tuple(x) for x in m]
num_pictures = len(i_org)
m=re.findall("\d+.?\d+",conf['img_sizes'])
if len(m) == 1:
    i_size = [make_tuple(m[0]) for i in range(num_pictures)]
elif len(m) == num_pictures:
    i_size = [make_tuple(x) for x in m]
else:
    logging.warning('Not enough img_sizes specified, need 1 or '+str(num_pictures)+"!")
    exit()
    

total_size = (math.ceil(display_aspect_ratio*camera_resolution[1]),camera_resolution[1])
roi_width_shift = int((total_size[0]-corr_camera_resolution[0])/2)

pillar   = load_img(conf['pillar_overlay'],total_size)
idle     = load_img(conf['idle_overlay'],corr_camera_resolution)
scan     = load_img(conf['scan_overlay'],corr_camera_resolution)
accept   = load_img(conf['accept_overlay'],corr_camera_resolution)
deny     = load_img(conf['deny_overlay'],corr_camera_resolution)
cd_3     = load_img(conf['countdown_dir'] + "3.png",corr_camera_resolution)
cd_2     = load_img(conf['countdown_dir'] + "2.png",corr_camera_resolution)
cd_1     = load_img(conf['countdown_dir'] + "1.png",corr_camera_resolution)
cd = (cd_1,cd_2,cd_3)
template = load_img(conf['output_template'],None)
display_img      = np.zeros((total_size[1],total_size[0],3),np.uint8)

# ------ INIT --------
v_shelve = shelve.open(conf['voucher_path'])
countdown_val = 0
current_picture = 0
output_picture = []

vc=camera.WebcamVideoStream(camera_resolution,src=0).start()

cv2.namedWindow(conf['window_name'],cv2.WINDOW_NORMAL)
cv2.setWindowProperty(conf['window_name'],cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN);
cv2.setMouseCallback(conf['window_name'], start)

#                                                  __ _        _                           _     _            
#                                                 / _\ |_ __ _| |_ ___    /\/\   __ _  ___| |__ (_)_ __   ___ 
#                                                 \ \| __/ _` | __/ _ \  /    \ / _` |/ __| '_ \| | '_ \ / _ \
#                                                 _\ \ || (_| | ||  __/ / /\/\ \ (_| | (__| | | | | | | |  __/
#                                                 \__/\__\__,_|\__\___| \/    \/\__,_|\___|_| |_|_|_| |_|\___|                                                          
count = 1
diff_time = 0
while True:
    start_time =  time()
    #ret_val, capture = cam.read()
    capture = vc.read()
    img = cv2.flip(capture, 1)
    img = img [0:camera_resolution[1],camera_offset:corr_camera_resolution[0]+camera_offset]
    if state == "idle":
        overlay_img = idle 
        # got to next state by clicking screen => start()
        
    elif state == "scan":
        overlay_img = scan 
        code = decode(capture,symbols=[ZBarSymbol.QRCODE])
        if len(code) == 1:
            if v_shelve[code[0].data.decode("utf-8")] == "NEW":
                v_shelve[code[0].data.decode("utf-8")] = "USED"
                v_shelve['used_vouchers'] = v_shelve['used_vouchers'] + 1
                v_shelve.sync()
                print(str(v_shelve['used_vouchers'])+"/"+str(v_shelve['num_vouchers']))
                state = "scan_accept"
            else:
                state = "scan_deny"
                
    elif state == "scan_accept":
        overlay_img = accept 
        start_timer(3,goto_init_countdown)
        state = "wait"
        
    elif state == "scan_deny":
        overlay_img = deny 
        start_timer(3,goto_scan)
        state = "wait"
        
    elif state == "init_countdown":
        countdown_val=4
        countdown()
        state = "countdown"
        
    elif state == "countdown":
        if countdown_val !=0:
            overlay_img = cd[countdown_val-1]
        else :
            overlay_img = None
            state = "picture"
            
    elif state == "picture":
        cv2.imwrite("Output/picture_"+str(current_picture)+".png",img)
        resized_img = cv2.resize(img, i_size[current_picture])
        output_picture.append(resized_img)
        current_picture+=1
        show_img = overlay(img,None)
        show_img = add_pillar(show_img, pillar[0])
        cv2.imshow(conf['window_name'], show_img)
        sleep(conf.getfloat('show_pic_t'))
        if current_picture < num_pictures:
            state = "init_countdown"
        else:
            current_picture = 0
            state = "process"
            
    elif state == "process":
        output_img = np.zeros((template[0].shape[0],template[0].shape[1],3),np.uint8)
        for i in range(num_pictures):
            output_img[i_org[i][0]:i_org[i][0]+i_size[i][1], i_org[i][1]:i_org[i][1]+i_size[i][0]] = output_picture[i]
        output_img = overlay(output_img,template)
        if output_img.shape[0] < output_img.shape[1]:
            output_img = cv2.flip(output_img, 1)
            output_img = cv2.transpose(output_img)
        cv2.imwrite("Output/to_print.bmp",output_img)
        state = "print"
        
    elif state == "print": 
        print_image(printer_handle,"Output/to_print.bmp",print_img_size)
        state = init_state
    elif state == "end":
        break
    else:
        pass
    img = overlay(img,overlay_img)
    img = add_pillar(img, pillar[0])
    cv2.imshow(conf['window_name'],img)

    if cv2.waitKey(1) == 27: 
        v_shelve.close()
        break  # esc to quit
    
    diff_time += time() - start_time
    count += 1
    if count == 30:
        count = 1
        diff_time /= 30
        print("FPS:" +str(1/diff_time))
        diff_time = 0
    
cv2.destroyAllWindows()
close_printer(printer_handle, pHandle)
vc.stop()
exit()
