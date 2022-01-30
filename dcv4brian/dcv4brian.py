from numpy import *
from brian2 import *
import os

protofunction='''
double _dcvsetget(int varid, double varval, int dly, double t){
    if ( fabs(t-dcvTime-dcvdt) < 1e-9 ){
        dcvIndex = (dcvIndex == 0)?(dcvDsize-1):(dcvIndex-1);
        dcvTime  = t;
    }
    dcvtbl[dcvIndex][varid] = varval;
    return dcvtbl[(dcvIndex+dly)%dcvDsize][varid] ;
}
'''

def dcvinit(tblsize :int,nvar:int,simdt:float,init:ndarray,c_target:bool=True):
    """
    It generates dcv4brian.c file with all required static variables
    for cpp and cython targets.
    Parameters:
        tblsize  - int     - max number of steps to remember
        nvar     - int     - number of delayed continues variables (DCV)
        simdt    - float   - simulation time step
        init     - ndarray - 1D array with initial value for each DCV
                           - this values fill up the table, therefore
                           - if a variable is a membrane potential of a 
                           - neurons, initialize it at resting potential
                           - if a variable is current or synaptic conductance
                           - initialize it with zero.
        c_only   - bool    - Set yo False if you need numpy code
    """
    dcvinit.c_target = c_target
    if c_target:
        with open("dcv4brian.c","w") as fd:
            fd.write("#ifndef __DCV4BRIAN__\n")
            fd.write("#define __DCV4BRIAN__\n")
            fd.write("#include <math.h>\n")
            fd.write(f"const  int    dcvDsize  = {tblsize:d};\n")
            fd.write(f"const  int    dcvVsize  = {nvar:d};\n")
            fd.write(f"static int    dcvIndex  = 0;\n")
            fd.write(f"static double dcvdt     = {simdt};\n")
            fd.write(f"static double dcvTime   = 0;\n")
            fd.write(f"static double dcvtbl[{tblsize:d}][{nvar:d}] = {{"+"\n")
            for cid in range(tblsize):
                fd.write("   {")
                for x in range(nvar):
                    fd.write(f"{init[x]}"+("," if x != nvar-1 else "}") )
                fd.write(",\n" if cid != tblsize-1 else "\n")
            fd.write("};\n")
            fd.write(protofunction+"\n")
            fd.write("#endif\n")
        dcvinit.dcvtbl   = None
        dcvinit.dcvIndex = 0
        dcvinit.dcvTime  = 0.
        dcvinit.dcvdt    = simdt
        dcvinit.dcvDsize = tblsize
        dcvinit.dcvVsize = nvar
            
    else:
        
        dcvinit.dcvtbl   = zeros((tblsize,nvar))
        for n in range(tblsize): dcvinit.dcvtbl[n] = copy(init)
        dcvinit.dcvIndex = 0
        dcvinit.dcvTime  = 0.
        dcvinit.dcvdt    = simdt
        dcvinit.dcvDsize = tblsize
        dcvinit.dcvVsize = nvar
    
    

@implementation('cpp', '''
#include <dcv4brian.c>;
double dcvsetget(int varid, double varval, int dly, double t){
    return _dcvsetget(varid,varval,dly,t);
}
''',include_dirs=[os.getcwd()])
@implementation('cython',f'''
cdef extern from "{os.getcwd()}/dcv4brian.c":
    double _dcvsetget(int, double, int, double)
cdef double dcvsetget(int varid, double varval, int dly, double t):
    return _dcvsetget(varid,varval,dly,t);
''',include_dirs=[os.getcwd()])
@check_units(arg=[1,1,1,1],result=1)
def dcvsetget(varid:(int,ndarray), varval:(float,ndarray), dly:int, t:float):
    """
    dcvsetget write current variable value into the table and returns
    a value of the same variable delayed by dly steps
    The module has internal time tracker. If (t - dt - internal_time) is less
    than 1e-9 of time units, the module increases table index.
    Inputs:
        varid - int   - variable ID in the table
        varval- float - current vaiable value to be recorded
        dly   - int   - number of steps to read value in the table
        t     - float - current time
    """
    if abs(t-dcvinit.dcvTime-dcvinit.dcvdt) < 1e-9:
        dcvinit.dcvIndex = (dcvinit.dcvDsize-1) if dcvinit.dcvIndex == 0 else (dcvinit.dcvIndex-1)
        dcvinit.dcvTime = t
    dcvinit.dcvtbl[dcvinit.dcvIndex,varid] = copy(varval)
    return dcvinit.dcvtbl[(dcvinit.dcvIndex+dly)%dcvinit.dcvDsize,varid]
