from numpy import *
from brian2 import *
from dcv4brian import *


defaultclock.dt=0.1*ms

prefs.codegen.target = 'numpy'

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

N = NeuronGroup(4, eqs, threshold='v>Vt', reset='v = Vr; I = 0', refractory=1*ms, method='euler')
N.v = 'Vr'
N.w   = 50.
N.S = 'Vr'


W = Synapses(N, N, """
    dly                     : integer (constant) # delay
    S_post = dcvsetget(i,v_pre,dly,t_in_timesteps)  : 1  (summed)
""")
xdly  = array([ int(round((100+i*30)*ms/defaultclock.dt)) for i in range(4) ])
W.connect(i=[0,1,2,3],j=[1,2,3,0])
W.dly = xdly

M = StateMonitor(N, ['v','I','S'], record=True)
dcvinit(amax(xdly).astype(int)+5,4,array([Vr,Vr,Vr,Vr]),c_target=False)


run(2000*ms)
dcvcleanup()

figure(1,figsize=(16,12))
suptitle("NumPy",fontsize=24)
subplot(4,1,1)
plot(M.t/ms,M[0].v,"-",lw=3,label="neuron-0")
plot(M.t/ms,M[1].S,"-",lw=3,label="delayed in 1")
legend(loc=1,fontsize=16)
subplot(4,1,2)
plot(M.t/ms,M[1].v,"-",lw=3,label="neuron-1")
plot(M.t/ms,M[2].S,"-",lw=3,label="delayed in 2")
legend(loc=1,fontsize=16)
subplot(4,1,3)
plot(M.t/ms,M[2].v,"-",lw=3,label="neuron-2")
plot(M.t/ms,M[3].S,"-",lw=3,label="delayed in 3")
legend(loc=1,fontsize=16)
subplot(4,1,4)
plot(M.t/ms,M[3].v,"-",lw=3,label="neuron-3")
plot(M.t/ms,M[0].S,"-",lw=3,label="delayed in 0")
legend(loc=1,fontsize=16)

show()
