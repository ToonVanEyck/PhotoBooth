import hashlib
import shelve
import pyqrcode
import cv2
import numpy as np
from pip._vendor.distlib.locators import Page

event_name = "PhotoVoucher"
nr_of_codes = 15
def gen_vouchers(name,nr):
    vouchers = []
    for x in range(0, nr):
        voucher_id=(str(name+":"+str(x)))
        voucher_hash=hashlib.sha224(voucher_id.encode()).hexdigest()
        vouchers.append((voucher_hash,0))
    return vouchers
    
def store_vouchers(vouchers, shelf_file):
    v_shelve = shelve.open(shelf_file)
    v_shelve.update(vouchers)
    v_shelve.close()
    
def qrcode_to_img(qrcode):
    row = []
    matrix = []
    for c in voucher_code.text():
        if c == '1' :
            row.append(0)
        elif c == '0':
            row.append(255)
        elif c == '\n':
            matrix.append(row)
            row= []
    return  (np.array(matrix,dtype=np.uint8))



voucher_code = pyqrcode.create('9a997912665133d2f8bb492789f4172291ae3fab89ddf5fd819c8502', error='M')
qr_img = qrcode_to_img(voucher_code)
print(qr_img.dtype, qr_img.copy, qr_img.shape)
large=cv2.resize(qr_img,(700,700),interpolation=cv2.INTER_NEAREST)
cv2.imwrite("Vouchers/test.png",large)
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, cm
c = canvas.Canvas('vouchers.pdf')

c.drawImage("Vouchers/test.png", 100, 0, 5*cm, 5*cm)
#c.showPage()
c.save()
print(c.getpdfdata())
# big_code.png('code.png')
# big_code.show()

img=cv2.imread("Vouchers/simple.png",cv2.IMREAD_GRAYSCALE)
print(img.dtype, img.copy, img.shape)

from reportlab.lib.colors import black, white, pink, lightblue
from reportlab.lib.pagesizes import A4, legal, landscape, portrait
from reportlab.pdfgen.canvas import Canvas

def generateNumberedPages(numPages, pageSize, orientation, bgColor, outPath):
    "Generate a 10 page document with one big number per page."
  
    if orientation == "landscape":
        pageSize = landscape(pageSize)
    canv = Canvas(outPath, pagesize=pageSize)
  
    for i in range(numPages):
        canv.setFont("Helvetica", 500)
        text = u"%s" % i
        if i % 2 == 0:
            canv.setStrokeColor(bgColor)
            canv.setFillColor(bgColor)
            canv.rect(0, 0, pageSize[0], pageSize[1], stroke=True, fill=True)
            canv.setFillColor(black)
        elif i % 2 == 1:
            canv.setStrokeColor(black)
            canv.setFillColor(black)
            canv.rect(0, 0, pageSize[0], pageSize[1], stroke=True, fill=True)
            canv.setFillColor(bgColor)
        if orientation == "portrait":
            canv.drawCentredString(pageSize[0]/2.0, pageSize[1]*0.3, u"%s" % i) 
        elif orientation == "landscape":
            canv.drawCentredString(pageSize[0]/2.0, pageSize[1]*0.21, u"%s" % i) 
        canv.showPage()
  
    canv.save()

def generate_voucher_pdf(pdf_file):
    qr_size = 3
    page_size = A4
    canv = Canvas(pdf_file, pagesize=page_size)
    voucher_size = ((page_size[0]/4)/cm,(page_size[1]/5)/cm)
    qr_x_offset = (voucher_size[0]-qr_size)/2
    qr_y_offset = voucher_size[1]-qr_size-qr_x_offset
    print(qr_x_offset,qr_y_offset)
    num_vouchers = 65
    for p in range(int((num_vouchers-1)/20)+1):
        v_left = 20*(p+1)
        if v_left > num_vouchers:
            v_left = num_vouchers
        print(p*20,v_left)
        for v in range(p*20,v_left):
            page_num = p
            row_num = int(v/4)-5*page_num
            col_num = v%4
            canv.drawImage("Vouchers/template.png", col_num*voucher_size[0]*cm,row_num*voucher_size[1]*cm, voucher_size[0]*cm, voucher_size[1]*cm)
            canv.drawImage("Vouchers/test.png", (col_num*voucher_size[0]+qr_x_offset)*cm,(row_num*voucher_size[1]+qr_y_offset)*cm, qr_size*cm, qr_size*cm)
        canv.showPage()
    canv.save()
    


generate_voucher_pdf("vouchers.pdf")

