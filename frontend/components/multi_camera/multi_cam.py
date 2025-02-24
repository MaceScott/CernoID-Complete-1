from contextlib import contextmanager

@contextmanager
def camera_session(camera):
    try:
        camera.open()
        yield camera
    finally:
        camera.release()

# Usage:
with camera_session(cv2.VideoCapture(0)) as cam:
    frame = cam.read() 