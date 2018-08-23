"""
simple way to animate the layers in a NetCDF file
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import xarray as xr

thaw_fn = './GIPL/SNAP_modified/gipl2f_thawOut_Day_5cm_ar5_5modelAvg_rcp85_1km_ak_Interior_EPSG3338.nc'

ds = xr.open_dataset( thaw_fn )
arr = ds[ 'thawOut_Day' ].values

start_a = arr[0,...] # start with the first slice of the array

fig = plt.figure()

im = plt.imshow(np.ma.masked_where(start_a == -9999, start_a), animated=True, cmap='RdBu')

count = 0 # make a global variable to 'track' the layer count within the function call
def updatefig(*args):
	global count
	if count < arr.shape[0]-1:
		count += 1
	else:
		count = 0
	a = arr[count,...]
	im.set_array(np.ma.masked_where(a == -9999, a) )
	return im,

ani = animation.FuncAnimation(fig, updatefig, interval=200, blit=True)

# save the animation as an mp4.  This requires ffmpeg or mencoder to be
# installed.  The extra_args ensure that the x264 codec is used, so that
# the video can be embedded in html5.  You may need to adjust this for
# your system: for more information, see
# http://matplotlib.sourceforge.net/api/animation_api.html
ani.save('basic_animation.mp4', fps=30, extra_args=['-vcodec', 'libx264'])
plt.show() # show it interactively if your current system allows/is set up for it.

