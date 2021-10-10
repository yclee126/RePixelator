# RePixelator 1.0.0

Converts resized pixel arts to their original resolution using FFT analysis.

The program finds the most dominant frequency in the X and Y direction, which is the original pixel resolution of the image.
Edge pixel offset is corrected using phase data of FFT output.

Up to x50 zoomed image, down to 4x4 converted image size is supported.


## Install

Python >= 3.5 is required.

`pip install repixelator`
`pip install wxpython>=4.0.0` (for GUI, optional. Read GUI section for details)


## CLI

`repixelator in_file out_file [mul [nr_sigma [edge_thr]]]`

The arguments are purely positional.


## GUI

GUI requires wxpython phoenix(>=4.0.0).
Type `repixelator-gui` in the command line to launch the GUI.

On Linux it's best to find pre-built wheel for wxpython.
The wheel build takes about 1-2 hours and it also might fail in the process if you're unlucky.
This is actually the primary reason why I made wxpython dependency to optional, I didn't want to give headache to someone.
<details>
	<summary>For building wxpython wheel on Linux, you might have to install these packages first.</summary>
	(Tested with Linux Mint 20)
	`sudo apt install make gcc libgtk-3-dev libgstreamer-gl1.0-0 freeglut3 freeglut3-dev python3-gst-1.0 libglib2.0-dev ubuntu-restricted-extras libgstreamer-plugins-base1.0-dev`
</details>


## Python API

- OpenCV BGR image -> OpenCV BGR image
`rePixelate(img: np.ndarray, mul=4, nr_sigma=0.0, edge_threshold=1.0) -> (bool, np.ndarray)`

- File -> File
`rePixelateFile(in_file: str, out_file: str, mul='4', nr_sigma='0.0', edge_threshold='1.0') -> bool`

`bool` tells if the conversion was successful or not.


## Parameters

- mul (int)
Image pre zoom multiplier, used to spread out generated derivative edges.
If you clearly see the pixels are huge enough (>5px), you can decrease this value to save resources.

- nr_sigma (float)
Noise reduction (Gaussian blur) sigma value.
This option is not suitable for most images, only use with problematic noisy images.
On GUI, the slider value is halved for convenience.

- edge_threshold (float)
If the image has cropped pixels on the edge, the program will offset the whole image to remove the more thin side.
If the offset value is greater than this value, the edge will be included by expanding the edge with the image.
Too small edge threshold will create "dirty edges", because there is not enough information to recreate the edge.
Note that the offset value is not very stable, so setting low value is not good in general.


## Dependencies
```
opencv-python
numpy
wxpython>=4.0.0 (optional)
```