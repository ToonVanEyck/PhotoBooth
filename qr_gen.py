import hashlib
import shelve
import pyqrcode
import cv2
import numpy as np
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import black, white, green, blue, red
from reportlab.lib.pagesizes import A4
import configparser

def gen_vouchers_codes(name,nr):
    vouchers = []
    for x in range(0, nr):
        voucher_id=(str(name+":"+str(x)))
        voucher_hash=hashlib.sha224(voucher_id.encode()).hexdigest()
        vouchers.append((voucher_hash,"NEW"))
    return vouchers
    
def store_voucher_codes(vouchers, shelve_file):
    v_shelve = shelve.open(shelve_file,flag='n')
    v_shelve.update({'num_vouchers':len(vouchers),'used_vouchers':0})
    v_shelve.update(vouchers)
    v_shelve.close()
    
def qrcode_to_img(qr_code):
    row = []
    matrix = []
    size = 0
    for c in qr_code.text():
        if c == '1' :
            row.append(0)
        elif c == '0':
            row.append(255)
        elif c == '\n':
            size+=1
            matrix.append(row)
            row= []
    return  (np.array(matrix,dtype=np.uint8)[3:size-3,3:size-3])

def draw_qr_code(canv,qr_img,size,qr_origin,color1,color2=None):
    resolution = qr_img.shape[0]
    pixel = size/resolution
    for y in range(0,resolution):
                for x in range(0,resolution):
                    if color1 != None and qr_img[y][x] == 0 :
                        canv.setFillColor(color1)
                        canv.rect((qr_origin[0]+x*pixel)*cm,(qr_origin[1]-y*pixel)*cm, pixel*cm,pixel*cm, stroke=False, fill=True)
                    elif color2 != None and qr_img[y][x] == 255:
                        canv.setFillColor(color2)
                        canv.rect((qr_origin[0]+x*pixel)*cm,(qr_origin[1]-y*pixel)*cm, pixel*cm,pixel*cm, stroke=False, fill=True)
                        

def generate_voucher_pdf(pdf_file,voucher_codes,design):
    qr_size, color1, color2, template = design
    num_vouchers = len(voucher_codes)
    page_size = A4
    canv = Canvas(pdf_file, pagesize=page_size)
    voucher_size = ((page_size[0]/4)/cm,(page_size[1]/5)/cm)
    for p in range(int((num_vouchers-1)/20)+1):
        v_todo = 20*(p+1)
        if v_todo > num_vouchers:
            v_todo = num_vouchers
        for v in range(p*20,v_todo):  
            qr = pyqrcode.create(str(voucher_codes[v][0]), error='M')
            qr_img = qrcode_to_img(qr)
            voucher_xy =(v%4,4-(int(v/4)-5*p))
            voucher_origin = (voucher_xy[0]*voucher_size[0],voucher_xy[1]*voucher_size[1])
            qr_origin = (voucher_origin[0]+(voucher_size[0]-qr_size)/2,voucher_origin[1]+voucher_size[1]-(voucher_size[0]-qr_size)/2-qr_size/qr_img.shape[0])
            canv.drawImage(template, voucher_origin[0]*cm,voucher_origin[1]*cm, voucher_size[0]*cm, voucher_size[1]*cm)
            draw_qr_code(canv,qr_img,qr_size,qr_origin,color1,color2)
        canv.showPage()
    canv.save()

def init_vouchers(key,num,voucher_path,design,v_pdf_path):
    codes = gen_vouchers_codes(key,num)
    store_voucher_codes(codes,voucher_path)
    generate_voucher_pdf(v_pdf_path,codes,design)


