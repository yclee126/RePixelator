import numpy as np
import cv2
import subprocess

sizes = (16, 32, 64, 128, 256)
for size in sizes:
    x, y = size, size
    img = np.zeros((x*y), dtype='uint8')

    for i in range(y):
        for j in range(x):
            if j < x/2:
                f = i/y
                img[i*y+j] = int((4*f**3 if f < 0.5 else 1-(-2*f+2)**3/2)*256) # cubic ease function
            else:
                img[i*y+j] = 255 if i < y/2 else 0

    img = np.reshape(img, (x, y))
    cv2.imwrite(f'icon-{size}.png', img)

icons = [f'icon-{i}.png' for i in sizes]
subprocess.run(['magick'] + icons + ['icon.ico'])