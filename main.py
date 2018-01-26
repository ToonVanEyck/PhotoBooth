import threading
import cv2
import shelve
import numpy as np
import math
from win_printer import print_capabilities, print_image, init_printer,  open_printer, close_printer, get_printer_config
from qr_gen import gen_vouchers_codes, store_voucher_codes
import win32con
import win32print
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol
from time import sleep
import code

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
    global countdown_delay
    countdown_val -= 1
    if countdown_val > 0:
        start_timer(countdown_delay,countdown)

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
# SCAN overlay
scan_overlay       = "Idle/1920x1080/scan.png"
scan_overlay_alpha = "Idle/1920x1080/scan_alpha.png"
# ACCEPT overlay
accept_overlay       = "Idle/1920x1080/accept.png"
accept_overlay_alpha = "Idle/1920x1080/accept_alpha.png"
# DENY overlay
deny_overlay       = "Idle/1920x1080/deny.png"
deny_overlay_alpha = "Idle/1920x1080/deny_alpha.png"
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
printer_name = pdf_printer_name
# Start_state
start_state = "scan"
# ------ LOAD OVERLAYS ------
roi_width_shift = int((new_overlay_size[0]-camera_resolution[0])/2)
idle_overlay_img        = cv2.resize(cv2.imread(idle_overlay),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
idle_overlay_img_alpha  = cv2.resize(cv2.imread(idle_overlay_alpha),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
idle = (idle_overlay_img,idle_overlay_img_alpha)
scan_overlay_img        = cv2.resize(cv2.imread(scan_overlay),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
scan_overlay_img_alpha  = cv2.resize(cv2.imread(scan_overlay_alpha),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
scan = (scan_overlay_img,scan_overlay_img_alpha)
accept_overlay_img        = cv2.resize(cv2.imread(accept_overlay),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
accept_overlay_img_alpha  = cv2.resize(cv2.imread(accept_overlay_alpha),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
accept = (accept_overlay_img,accept_overlay_img_alpha)
deny_overlay_img        = cv2.resize(cv2.imread(deny_overlay),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
deny_overlay_img_alpha  = cv2.resize(cv2.imread(deny_overlay_alpha),new_overlay_size)[0:camera_resolution[1], roi_width_shift:roi_width_shift+camera_resolution[0]]
deny = (deny_overlay_img,deny_overlay_img_alpha)
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
state = start_state
countdown_val = 0
overlay_img_file = ""
overlay_img_alpha_file = ""
current_picture = 1
nr_of_pictures = 4
output_picture = []
total_output_img = np.zeros((total_output_img_size[1],total_output_img_size[0],3),np.uint8)
init_printer(printer_name,paper_size,win32con.DMORIENT_LANDSCAPE)
v_shelve = shelve.open("Vouchers/data/vouchers")

PRINTER_DEFAULTS = {"DesiredAccess":win32print.PRINTER_ALL_ACCESS} 
printer = win32print.OpenPrinter(printer_name,PRINTER_DEFAULTS)
print(get_printer_config(printer))

cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH,camera_resolution[0])
cam.set(cv2.CAP_PROP_FRAME_HEIGHT,camera_resolution[1])
cv2.namedWindow(my_window)#,cv2.WINDOW_NORMAL) 
#cv2.setWindowProperty(my_window,cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN);
cv2.setMouseCallback(my_window, start)



while True:
    ret_val, capture = cam.read()
    img = cv2.flip(capture, 1)
    if state == "idle":
        overlay_img = idle 
        # got to next state by clicking screen => start()
    elif state == "scan":
        overlay_img = scan 
        code = decode(capture,symbols=[ZBarSymbol.QRCODE])
        if len(code) == 1:
            if v_shelve[code[0].data.decode("utf-8")] == "NEW":
                v_shelve[code[0].data.decode("utf-8")] = "USED"
                print("ok")
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
    else:
        pass
    overlay(overlay_img)
    cv2.imshow(my_window, img)

    
    if cv2.waitKey(1) == 27: 
        v_shelve.close()
        break  # esc to quit
cv2.destroyAllWindows()

