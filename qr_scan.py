from threading import Thread
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol
import shelve

class QRScanner:
    def __init__(self, vc):
        self.stream = vc
        self.code = decode(self.stream.read(),symbols=[ZBarSymbol.QRCODE])
        self.stopped = False
        
    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self
     
    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return
 
            # otherwise, read the next frame from the stream
            self.code = decode(self.stream.read(),symbols=[ZBarSymbol.QRCODE])
 
    def read(self):
        # return the frame most recently read
        return self.code
 

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
        
