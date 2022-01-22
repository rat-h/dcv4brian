from numpy import *
from brian2 import *
from dcv4brian import *


defaultclock.dt=0.1*ms

#prefs.codegen.target = 'cython'

taum = 20*ms
taue = 5*ms
Vt = -50
Vr = -60
El = -55



eqs = '''
dv/dt  = (I + int(i==0)*int(t<40*ms)*10 -(v-El))/taum : 1 (unless refractory)
dI/dt  = (S - I)/taue     : 1 (unless refractory)
S : 1
'''

N = NeuronGroup(4, eqs, threshold='v>Vt', reset='v = Vr; I = 0', refractory=1*ms, method='euler')
N.v = 'Vr'


W = Synapses(N, N, """
    w : 1 # synaptic weight
    dly : integer (constant) # delay
    S_post = w/(1+exp(-(dcvget(dly,i)-Vt))) : 1  (summed)
    #S_post = w/(1+exp(-(v_pre-Vt))) : 1  (summed)
""")

W.connect(i=[0,1,2,3],j=[1,2,3,0])
W.dly = [ int(round((100+i*10)*ms/defaultclock.dt)) for i in range(4) ]
W.w   = 50.

M = StateMonitor(N, ['v','I','S'], record=True)
dcvinit(amax(W.dly).astype(int)+5,4,array([Vr,Vr,Vr,Vr]),c_target=True)
updater     = N.run_regularly('return_ = dcvupdate(v, i)')


run(2000*ms)

axv = subplot(3,1,1)
plot(M.t/ms,M[0].v,"-",lw=2,label="0")
plot(M.t/ms,M[1].v,"-",lw=2,label="1")
plot(M.t/ms,M[2].v,"-",lw=2,label="2")
plot(M.t/ms,M[3].v,"-",lw=2,label="3")
legend(loc=0)
axi = subplot(3,1,2,sharex=axv)
plot(M.t/ms,M[0].I,"-")
plot(M.t/ms,M[1].I,"-")
plot(M.t/ms,M[2].I,"-")
plot(M.t/ms,M[3].I,"-")
axs = subplot(3,1,3,sharex=axv)
plot(M.t/ms,M[0].S,"-")
plot(M.t/ms,M[1].S,"-")
plot(M.t/ms,M[2].S,"-")
plot(M.t/ms,M[3].S,"-")
show()
