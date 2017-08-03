from pylab import *
import sphviewer


# Script to rotate around a density distribution in 200 frames

# read in relevant columns from your file
x,y,z, mass, den = loadtxt(sys.argv[1], unpack=True, usecols=[1,2,3,7, 9], skiprows=1, delimiter=',')


# set up arrays recognized by py-sphviewer
pos = zeros(shape=(3, len(den)))
pos[0][:] = x
pos[1][:] = y
pos[2][:] = z

# initialize sphviewer particles structure
Particles = sphviewer.Particles(pos, mass)

for ii in range(200):
    print sys.argv[1], ii


    # set up a scene
    Scene = sphviewer.Scene(Particles)
    camera = Scene.Camera.get_params()


    # make a full rotation in 200 frames (theta in degrees) 
    theta = double(ii)/200.0*360

    # gradually ease in from 1000 to 800 

    radius = 1000 - double(ii)

    # place camera at thera and r
    Scene.update_camera(r=radius,t = 0, p = theta, xsize=1000, ysize=1000, x=0.0, y=0.0, z=0.0)

    # create the image

    Render = sphviewer.Render(Scene)
    Render.set_logscale()
    img = Render.get_image()
    extent = Render.get_extent()
    fig = plt.figure(1,figsize=(6,6))
    ax1 = fig.add_subplot(111)
    ax1.imshow(img, extent=extent, origin='lower', cmap='afmhot')

    axis('off')
   
    # save the image
    savefig('supernova_den_%03d.png' %ii, bbox_inches='tight')



