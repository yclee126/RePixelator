# RePixelator v1.0.0 by yclee126
# Works on Python 3.5 or higher
#
# This program converts enlarged pixel arts into their original resolution through FFT analysis.

__version__ = '1.0.0'

import cv2
import numpy as np
from pathlib import Path
import sys


def rePixelateFile(in_file: str, out_file: str, mul='4', nr_sigma='0.0', edge_threshold='1.0') -> bool:
    print(in_file)
    
    animation = False
    try:
        img = cv2.imdecode(np.fromfile(in_file, dtype='uint8'), cv2.IMREAD_COLOR) # non-ASCII path workaround
        img.shape
    except:
        try:
            cap = cv2.VideoCapture(in_file)
            if cap is None or not cap.isOpened():
                raise ValueError
            animation = True
        except:
            print('File read error or non-ASCII path error for animated images.')
            return False
    
    if not animation:
        ret, img = rePixelate(img, int(mul), float(nr_sigma), float(edge_threshold))
        if not ret:
            return False
        
        try:
            ext = str(Path(out_file).suffix)
            cv2.imencode(ext, img)[1].tofile(out_file)
            return True
        except:
            print('File write error.\nCheck for write permission or output file extension.')
            return False
    
    else: # this also includes static .gif files which can't be rewinded
        _, img = cap.read()
        _, img_conv = rePixelate(img, int(mul), float(nr_sigma), 0)
        h, w, _ = img_conv.shape
        
        i = 0
        while True:
            img = cv2.resize(img, (w, h), cv2.INTER_AREA)
            path = str(Path(out_file).parent / Path(out_file).stem) + f'_frame{i+1:04d}' + str(Path(out_file).suffix)
            try:
                cv2.imwrite(path, img)
            except:
                print('File write error.\nCheck for write permission or output file extension.')
                return False
            
            i += 1
            ret, img = cap.read()
            if not ret:
                cap.release()
                print(i, 'frames converted')
                return True

def rePixelate(img: np.ndarray, mul=4, nr_sigma=0.0, edge_threshold=1.0) -> (bool, np.ndarray):
    h, w, c = img.shape
    print(f'Image: {w}x{h}')
    
    img = cv2.resize(img, None, fx=mul, fy=mul, interpolation=cv2.INTER_LINEAR)
    h, w, c = img.shape

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if nr_sigma > 0:
        gray = cv2.GaussianBlur(gray, (0, 0), nr_sigma, borderType=cv2.BORDER_REPLICATE)
    
    edges_x = cv2.Scharr(gray, -1, 1, 0);
    edges_y = cv2.Scharr(gray, -1, 0, 1);
    
    line_x = np.mean(edges_x, axis=0)
    line_x = np.log(line_x+1)
    
    line_y = np.mean(edges_y, axis=1)
    line_y = np.log(line_y+1)

    def FFT(line):
        line = line - np.mean(line)
        n = len(line)
        
        complex = np.fft.fft(line)
        mag = np.abs(complex) / n
        phase = np.rad2deg(np.angle(complex))

        mag = mag[range(int(n / 2))]
        phase = phase[range(int(n / 2))]
        
        start = int(max(n/mul/50, 4)) # down to 1/50 scale OR at least 4x4 converted size
        index = np.argmax(mag[start:]) + start
        phase = phase[index]
        
        return index, phase
    
    conv_x, phase_x = FFT(line_x)
    conv_y, phase_y = FFT(line_y)
    print(f'FFT: {conv_x}x{conv_y}')
    print(f'Pixel size: {w/mul/conv_x:.3f}x{h/mul/conv_y:.3f}')
    if not conv_x or not conv_y:
        print('FFT error')
        return False, np.array([])
    
    # calc offset
    pixsize_x = w / conv_x
    pixsize_y = h / conv_y
    offset_x = pixsize_x * phase_x / 360
    offset_y = pixsize_y * phase_y / 360
    print(f'Offset: x={offset_x/mul:.2f}, y={offset_y/mul:.2f}')
    
    # process offset pixels
    if edge_threshold > 0:
        edge_threshold *= mul
        
        dir_x = np.sign(offset_x) if abs(offset_x) > edge_threshold else 0
        dir_y = np.sign(offset_y) if abs(offset_y) > edge_threshold else 0
        
        if dir_x or dir_y:
            new_w, new_h = w, h
            pxxi, pxyi = round(pixsize_x), round(pixsize_y)
            
            # determine edges to include
            if dir_x:
                print('Left' if dir_x < 0 else 'Right', end='')
                new_w += pxxi
                conv_x += 1
                
            if dir_x and dir_y:
                print('+', end='')
                
            if dir_y:
                print('Up' if dir_y < 0 else 'Down', end='')
                new_h += pxyi
                conv_y += 1
                
            print(' edge included')
            
            # paste image to new canvas
            new_img = np.zeros((new_h, new_w, c), dtype='uint8')
            
            if dir_x >= 0 and dir_y >= 0:
                new_img[:h, :w] = img
            elif dir_x < 0 and dir_y >= 0:
                new_img[:h, new_w-w:] = img
            elif dir_x >= 0 and dir_y < 0:
                new_img[new_h-h:, :w] = img
            elif dir_x < 0 and dir_y < 0:
                new_img[new_h-h:, new_w-w:] = img
            
            img = new_img
            h, w, c = img.shape
            
            # fill border
            oxi, oyi = int(-pxxi*dir_x), int(-pxyi*dir_y)
            
            if oxi > 0:
                for i in range(oxi):
                    img[:, i] = img[:, oxi]
            else:
                for i in range(-oxi):
                    img[:, w-1-i] = img[:, w-1-(-oxi)]
            
            if oyi > 0:
                for i in range(oyi):
                    img[i, :] = img[oyi, :]
            else:
                for i in range(-oyi):
                    img[h-1-i, :] = img[h-1-(-oyi), :]
    
    print(f'Final: {conv_x}x{conv_y}')
    
    # apply offset
    oxi, oyi = int(offset_x), int(offset_y)
    matrix = np.array([[1, 0, oxi], [0, 1, oyi]], dtype='float')
    img = cv2.warpAffine(img, matrix, (w, h), borderMode=cv2.BORDER_REPLICATE)
    
    # shrink image
    img = cv2.resize(img, (conv_x, conv_y), cv2.INTER_AREA)
    
    return True, img

def main(args = sys.argv[1:]):
    print('RePixelator', __version__, 'by yclee126')
    print('Usage: in_file out_file [nZoom [fNoise [fEdge_thr]]]')
    print('Example: in.png out.png 4 0 0.8\n')
    
    if args and rePixelateFile(*args):
        print('\nFile converted')

if __name__ == '__main__':
    main()