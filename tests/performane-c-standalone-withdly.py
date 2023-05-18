from numpy import *
from brian2 import *
from dcv4brian import *


defaultclock.dt=0.1*ms

set_device('cpp_standalone', directory='standalone')


Nnrn=1000
taum = 20*ms
taue = 5*ms
Vt = -50
Vr = -60
El = -55



eqs = '''
dv/dt  = (I + int(i==0)*int(t<40*ms)*10 -(v-El))/taum : 1 (unless refractory)
dI/dt  = (50/(1+exp(-(w*S-Vt))) - I)/taue     : 1 (unless refractory)
S : 1
w : 1
'''

N = NeuronGroup(Nnrn, eqs, threshold='v>Vt', reset='v = Vr; I = 0', refractory=1*ms, method='euler')
N.v = 'Vr'
N.w   = 0.01
N.S = 'Vr'


W = Synapses(N, N, """
    dly                                             : integer (constant) # delay
    S_post = dcvsetget(i,v_pre,dly,t_in_timesteps)  : 1  (summed)
""")
xdly  = array([ [f,t,200+f*3] for f in range(Nnrn) for t in range(Nnrn) if f !=t and random() < 0.3])

W.connect(i=xdly[:,0].flatten(), j=xdly[:,1].flatten())
W.dly = xdly[:,2].flatten()

dcvinit(amax(xdly[:,2]).astype(int)+5,xdly.shape[0],array([Vr for l in xdly]),c_target=True)


run(20000*ms,report='text')

dcvcleanup()
