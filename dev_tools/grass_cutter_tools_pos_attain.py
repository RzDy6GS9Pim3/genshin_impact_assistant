from source.interaction_background import InteractionBGD
from unit import *

itt = InteractionBGD(hwndname='GrasscutterTools  - by jie65535  - v1.6.8')

# cv2.imshow('123', itt.capture())
# cv2.waitKey(0)
while 1:
    time.sleep(0.1)
    itt.keyPress('F5')