import threading
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import StringIO
import time
import pygame
import pygame.camera
from pygame.locals import *
from PIL import Image,ImageDraw
import boto3
import traceback
from threading import Thread

DEBUG=1
IMAGE_WIDTH=640
IMAGE_HEIGHT = 480
bounding = []

class AwsRekoFace:

	def __init__(self):
		self.aws_client = boto3.client("rekognition")

        def image_to_byte(self,image):
                img = StringIO.StringIO()
                image.save(img,'JPEG')
                return img.getvalue()

	def find_faces(self,image):
		width,height = image.size
                response = self.aws_client.detect_faces(Image={'Bytes':self.image_to_byte(image)},Attributes=['DEFAULT'])
                print response
                result = []
                try:
                        if response != None:
                                for faceDetail in response['FaceDetails']:
                                        print "Detected Face"
                                        H1=min(int(faceDetail['BoundingBox']['Height']*height),height)
                                        W1=min(int(faceDetail['BoundingBox']['Width']*width),width)
                                        L1=max(int(faceDetail['BoundingBox']['Left']*width),0)
                                        R1=max(0,int(faceDetail['BoundingBox']['Top']*height))
                                        cropped= image.crop((L1,R1,L1+W1,R1+H1))
                                        res = self.search_face(cropped)

                                        result.append([res,(L1,R1,L1+W1,R1+H1)])
                except:
                        traceback.print_exc()
                return result


        def search_face(self,image):
                try:
                        response = self.aws_client.search_faces_by_image(CollectionId='BETTERAVE_FACES',Image={'Bytes':self.image_to_byte(image)})
                        for record in response['FaceMatches']:
                                face = record['Face']
                                return face['ExternalImageId']
                except:
                         traceback.print_exc()
                return 'Unknown'



class CamHandler(BaseHTTPRequestHandler):
	def __init__(self, *args):
		self.bounding = []
	        DEVICE = '/dev/video0'
        	self.SIZE = (IMAGE_WIDTH, IMAGE_HEIGHT)
	        pygame.init()
        	pygame.camera.init()

		self.aws_reko = AwsRekoFace()
		self.camera = pygame.camera.Camera(DEVICE, self.SIZE) 

		BaseHTTPRequestHandler.__init__(self, *args)

	def get_camera_image(self):
		img = self.camera.get_image()
		data = pygame.image.tostring(img,'RGBA')
		img = Image.frombytes('RGBA', self.SIZE, data)
		return img


	def runAPI(self):
		self.send_response(200)
                self.send_header('Content-type','text')
                self.end_headers()
                o = self.wfile
                try:
                	self.camera.start()
                        result = self.aws_reko.find_faces(self.get_camera_image())
                        self.camera.stop()
                        res = ""
                        for id in result:
                        	res+=id[0]+" "
                                o.write(res)
		except Exception as e:
                	print e


	def runIndex(self):
		 self.send_response(200)
                 self.send_header('Content-type','text/html')
                 self.end_headers()
                 self.wfile.write('<html><head></head><body>')
                 self.wfile.write('<img src="/cam.mjpg"/>')
                 self.wfile.write('</body></html>')

	def runMjpgThread(self,image):
		self.bounding=self.aws_reko.find_faces(image)

	def runMjpg(self):
		self.send_response(200)
                self.send_header('Content-type','multipart/x-mixed-replace; boundary=--myboundary')
                self.end_headers()
                o = self.wfile
                self.camera.start()
                frame=0
		result=[]
		t = None
                try:
                	while True:
                        	image = self.get_camera_image()
				if frame==0 or (frame % 15 == 14 and t!=None and not t.isAlive()):
					t = threading.Thread(target=self.runMjpgThread,args=(image,))
					t.start()
				draw = ImageDraw.Draw(image)
				for res in self.bounding:
					[name,coord] = res
					(x0,y0,x1,y1) = coord
					draw.rectangle([x0, y0, x1, y1])
					draw.text([x0,y0],name)

                                data = self.aws_reko.image_to_byte(image)
                                o.write( "--myboundary\r\n" )
                                o.write( "Content-Type: image/jpeg\r\n" )
                                o.write( "Content-Length: %s\r\n" % str(len(data)))
                                o.write( "\r\n" )
                                o.write(data)
                                o.write( "\r\n" )
                                time.sleep(0.05)
                                frame+=1
		except Exception as e:
                	print e
                finally:
                	self.camera.stop()


	def run404(self):
		self.send_response(404)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write('<html><head></head><body>')
                self.wfile.write('404 : Not Found')
                self.wfile.write('</body></html>')

	def do_GET(self):
		try:
			if self.path.endswith('api'):
				self.runAPI()
				return

			if self.path.endswith('index.html'):
				self.runIndex()
				return

			if self.path.endswith('cam.mjpg'):
				self.runMjpg()
				return

			self.run404()

		except Exception as e:
			print e

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""

def main():
	try:
		server = ThreadedHTTPServer(('0.0.0.0', 80), CamHandler)
		print "server started"
		server.serve_forever()
	except KeyboardInterrupt:
		server.socket.close()

if __name__ == '__main__':
	main()



