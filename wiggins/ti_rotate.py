from pylab import *
import sphviewer



x,y,z, mass, den, ti = loadtxt(sys.argv[1], unpack=True, usecols=[1,2,3,7, 9,34], skiprows=1, delimiter=',')



pos = zeros(shape=(3, len(den)))
pos[0][:] = x
pos[1][:] = y
pos[2][:] = z

Particles = sphviewer.Particles(pos, ti)
for ii in range(105, 200):
    print sys.argv[1], ii



    Scene = sphviewer.Scene(Particles)
    camera = Scene.Camera.get_params()
    theta = double(ii)/200.0*360
    radius = 1000 - double(ii)
    Scene.update_camera(r=radius, t = 0.0, p = theta, xsize=1000, ysize=1000, x=0.0, y=0.0, z=0.0)

    Render = sphviewer.Render(Scene)
    Render.set_logscale()
    img = Render.get_image()
    extent = Render.get_extent()
    fig = plt.figure(1,figsize=(6,6))
    ax1 = fig.add_subplot(111)
    ax1.imshow(img, extent=extent, origin='lower', cmap='hot')

    axis('off')
    savefig('supernova_ti_%03d.png' %ii, bbox_inches='tight')



