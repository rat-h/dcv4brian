from numpy import *
from brian2 import *
from dcv4brian import *


defaultclock.dt=0.1*ms

prefs.codegen.target = 'cython'

Nnrn=1000
taum = 20*ms
taue = 5*ms
Vt = -50
Vr = -60
El = -55



eqs = '''
dv/dt  = (I + int(i==0)*int(t<40*ms)*10 -(v-El))/taum : 1 (unless refractory)
dI/dt  = (w/(1+exp(-(S-Vt))) - I)/taue     : 1 (unless refractory)
S : 1
w : 1
'''

N = NeuronGroup(Nnrn, eqs, threshold='v>Vt', reset='v = Vr; I = 0', refractory=1*ms, method='euler')
N.v = 'Vr'
N.w   = 50.
N.S = 'Vr'


W = Synapses(N, N, """
    dly                     : integer (constant) # delay
    S_post = dcvsetget(i,v_pre,dly,t/ms)  : 1  (summed)
""")
xdly  = array([ 200+i*3 for i in range(Nnrn) ])
W.connect(j='(i+1)%Nnrn')
W.dly = xdly

dcvinit(amax(xdly).astype(int)+5,Nnrn,defaultclock.dt/ms,array([Vr for l in range(Nnrn)]),c_target=True)


run(20000*ms,report='text')

