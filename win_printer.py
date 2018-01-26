import win32print
import win32gui
import win32con

def init_printer(printer_name,media_format,orientation):
    PRINTER_DEFAULTS = {"DesiredAccess":win32print.PRINTER_ALL_ACCESS}
    pHandle = win32print.OpenPrinter(printer_name, PRINTER_DEFAULTS)
    properties = win32print.GetPrinter(pHandle,2)
    pDevModeObj = properties["pDevMode"]
    pDevModeObj.PaperSize = win32print.DeviceCapabilities(printer_name,"", win32con.DC_PAPERS,None)[media_format]
    pDevModeObj.Orientation = orientation
    properties["pDevMode"]=pDevModeObj
    win32print.SetPrinter(pHandle,2,properties,0)
    win32print.ClosePrinter(pHandle)
    
def print_capabilities(printer_name):
    print("capabilities of the printer")
    print(win32print.DeviceCapabilities(printer_name,"", win32con.DC_PAPERS,None))
    print(win32print.DeviceCapabilities(printer_name,"", win32con.DC_PAPERNAMES,None))
    print(win32print.DeviceCapabilities(printer_name,"", win32con.DC_PAPERSIZE,None))
    print(win32print.DeviceCapabilities(printer_name,"", win32con.DC_ENUMRESOLUTIONS,None))
    
def open_printer(printer_name):
    PRINTER_DEFAULTS = {"DesiredAccess":win32print.PRINTER_ALL_ACCESS}
    pHandle = win32print.OpenPrinter(printer_name, PRINTER_DEFAULTS)
    properties = win32print.GetPrinter(pHandle,2)
    pdevmode = properties["pDevMode"]
    print_processor = properties['pPrintProcessor']      # TODO FIX THIS
    printer_handle=win32gui.CreateDC(print_processor,printer_name,None) 
    return (printer_handle,pHandle)

def close_printer(printer_handle,pHandle):
    win32gui.DeleteDC(printer_handle)
    win32print.ClosePrinter(pHandle)
    
def get_printer_config(printer_handle):
    config = {
        'PHYSICALWIDTH': win32print.GetDeviceCaps(printer_handle, win32con.PHYSICALWIDTH),
        'PHYSICALWIDTH': win32print.GetDeviceCaps(printer_handle, win32con.PHYSICALHEIGHT),
        'HORZSIZE': win32print.GetDeviceCaps(printer_handle, win32con.HORZSIZE),
        'VERTSIZE': win32print.GetDeviceCaps(printer_handle, win32con.VERTSIZE),
        'HORZRES': win32print.GetDeviceCaps(printer_handle, win32con.HORZRES),
        'VERTRES': win32print.GetDeviceCaps(printer_handle, win32con.VERTRES),
        'LOGPIXELSX': win32print.GetDeviceCaps(printer_handle, win32con.LOGPIXELSX),
        'LOGPIXELSY': win32print.GetDeviceCaps(printer_handle, win32con.LOGPIXELSY)
        }
    return config

def print_image(printer_handle,img_file,img_size):
    printer_copy_DC = win32gui.CreateCompatibleDC(printer_handle) 
    image_bitmap = win32gui.LoadImage(0,img_file, win32con.IMAGE_BITMAP, img_size[0],img_size[1], win32con.LR_LOADFROMFILE)
    win32gui.SelectObject(printer_copy_DC, image_bitmap)

    win32print.StartDoc(printer_handle,('printed_photo',None,None,0))
    win32print.StartPage(printer_handle)
    win32gui.BitBlt(printer_handle, 0, 0, img_size[0], img_size[1],printer_copy_DC, 0, 0, win32con.SRCCOPY)
    win32print.EndPage(printer_handle)
    win32print.EndDoc(printer_handle)
    
    win32gui.DeleteObject(image_bitmap)
    win32gui.DeleteDC(printer_copy_DC)
