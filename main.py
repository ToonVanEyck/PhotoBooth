import threading
import cv2
import numpy as np
import math
from win_printer import print_capabilities, print_image, init_printer,  open_printer, close_printer, get_printer_config
from qr_gen import gen_vouchers_codes, store_voucher_codes
import win32con
from time import sleep

def start_countdown_timer():
    t = threading.Timer(countdown_delay, countdown)
    t.start()

def countdown():
    global countdown_val
    countdown_val -= 1
    if countdown_val > 0:
        start_countdown_timer()

def overlay(over):
    if over != None:
        overlay_img, overlay_img_alpha = over
        overlay_img_beta  = cv2.bitwise_not(overlay_img_alpha)
        overlay_img_alpha_norm = overlay_img_alpha / 255.0
        overlay_img_beta_norm  = overlay_img_beta  / 255.0
        global img
        img = cv2.add( cv2.multiply(overlay_img , overlay_img_alpha_norm ,dtype = 0) , cv2.multiply(img , overlay_img_beta_norm,dtype = 0) )
    return

def start(event, x, y, flags, param):
    global state
    if state == "idle" and event == cv2.EVENT_LBUTTONDOWN:
        state = "init_countdown"

# ------ SETUP -------
# Camera setup
camera_resolution = (640,480)
#camera_resolution = (1280,720)
camera_aspect_ratio = camera_resolution[0]/camera_resolution[1]

overlay_size = (1920,1080)
new_overlay_size = (math.ceil(overlay_size[0]/(overlay_size[1]/camera_resolution[1])),camera_resolution[1])
# IDLE overlay
idle_overlay       = "Idle/1920x1080/totem.png"
idle_overlay_alpha = "Idle/1920x1080/totem_alpha.png"
# COUNTDOWN overlay directory
countdown_directory = "Countdown/1920x1080/totem_"
countdown_delay = 0.1
# Time to show each picture in between captures
show_picture_delay = 0.0
# Output template
template_img_file = "Print/9x6 inch/bicky_bier.png"
template_img_alpha_file = "Print/9x6 inch/bicky_bier_alpha.png"
single_output_img_size = (1200,900) 
total_output_img_size = (2700,1800)
# Printers
pdf_printer_name = "Microsoft Print to PDF"
foto_printer_name = "MITSUBISHI CP9550D/DW(USB)"
#  paper_size = x |   FOTO    |   PDF
#-----------------+-----------+---------
#  paper_size = 0 # (3.5x5")  | Letter
#  paper_size = 1 # (4x6")    | Tabloid
#  paper_size = 2 # (5x7")    | Legal
#  paper_size = 3 # (6x8")    | Statement
#  paper_size = 4 # (6x8.5")  | Exclusive
#  paper_size = 5 # (6x9")    | A3
#  paper_size = 6 # (2x6"x2)  | A4            # 1040x1580
#  paper_size = 7 # (2x6"x2)  | A5            # 520x1580
paper_size = 5
printer_name = foto_printer_name
# ------ LOAD OVERLAYS ------
roi_width_shift = int((new_overlay_size[0]-camera_resolution[0])/2)
idle_overlay_img        = cv2.resize(cv2.imread(idle_overlay),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
idle_overlay_img_alpha  = cv2.resize(cv2.imread(idle_overlay_alpha),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
idle = (idle_overlay_img,idle_overlay_img_alpha)
cd_3_overlay_img        = cv2.resize(cv2.imread(countdown_directory + "3.png"),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
cd_3_overlay_img_alpha  = cv2.resize(cv2.imread(countdown_directory + "3_alpha.png"),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
cd_3 = (cd_3_overlay_img ,cd_3_overlay_img_alpha )
cd_2_overlay_img        = cv2.resize(cv2.imread(countdown_directory + "2.png"),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
cd_2_overlay_img_alpha  = cv2.resize(cv2.imread(countdown_directory + "2_alpha.png"),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
cd_2 = (cd_2_overlay_img ,cd_2_overlay_img_alpha )
cd_1_overlay_img        = cv2.resize(cv2.imread(countdown_directory + "1.png"),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
cd_1_overlay_img_alpha  = cv2.resize(cv2.imread(countdown_directory + "1_alpha.png"),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
cd_1 = (cd_1_overlay_img ,cd_1_overlay_img_alpha )
cd = (cd_1,cd_2,cd_3)
# ------ INIT --------
my_window = "PhotoBooth" 
state = "idle"
countdown_val = 0
overlay_img_file = ""
overlay_img_alpha_file = ""
current_picture = 1
nr_of_pictures = 4
output_picture = []
total_output_img = np.zeros((total_output_img_size[1],total_output_img_size[0],3),np.uint8)
init_printer(printer_name,paper_size,win32con.DMORIENT_LANDSCAPE)
printer = open_printer(printer_name)
print(get_printer_config(printer[0]))

cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH,camera_resolution[0])
cam.set(cv2.CAP_PROP_FRAME_HEIGHT,camera_resolution[1])
cv2.namedWindow(my_window)#,cv2.WINDOW_NORMAL) 
#cv2.setWindowProperty(my_window,cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN);
cv2.setMouseCallback(my_window, start)


while True:
    ret_val, img = cam.read()
    img = cv2.flip(img, 1)
    if state == "idle":
        overlay_img = idle
        # got to next state by clicking screen => start()
    elif state == "init_countdown":
        countdown_val=3
        start_countdown_timer()
        state = "countdown"
    elif state == "countdown":
        if countdown_val !=0:
            overlay_img = cd[countdown_val-1]
        else :
            overlay_img = None
            state = "picture"
    elif state == "picture":
        cv2.imwrite("Output/picture_"+str(current_picture)+".png",img)
        resized_img = cv2.resize(img, single_output_img_size)
        output_picture.append(resized_img)
        current_picture+=1
        cv2.imshow(my_window, img)
        sleep(show_picture_delay)
        if current_picture <= nr_of_pictures:
            state = "init_countdown"
        else:
            state = "process"
    elif state == "process":
        total_output_img[0:900, 0:1200]        = output_picture[0]
        total_output_img[900:1800, 0:1200]     = output_picture[1]
        total_output_img[0:900, 1500:2700]     = output_picture[2]
        total_output_img[900:1800, 1500:2700]  = output_picture[3]
        
        dummy = img
        img = total_output_img
        template_overlay       = cv2.imread(template_img_file)
        template_overlay_alpha  = cv2.imread(template_img_alpha_file)
        template = (template_overlay, template_overlay_alpha)
        overlay(template)
        cv2.imwrite("Output/picture_total.png",img)
        height, width = img.shape[:2]
#         if height < width:
#             img = cv2.flip(img, 1)
#             img = cv2.transpose(img)
        cv2.imwrite("Output/picture_total.bmp",img)
        
        img = dummy
        state = "print"
    elif state == "print": 
        state = "end"
    elif state == "end":
        break

    overlay(overlay_img)
    cv2.imshow(my_window, img)

    
    if cv2.waitKey(1) == 27: 
        break  # esc to quit
cv2.destroyAllWindows()

