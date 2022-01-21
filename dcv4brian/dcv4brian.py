from numpy import *
from brian2 import *
import os

protofunctions="""
void _dcvupdate(double x, int i){
    if ( i == 0 )
        dcvIndex = (dcvIndex == 0)?(dcvDsize-1):(dcvIndex-1);
    dcvtbl[dcvIndex][i] = x;
    return ;
}
double _dcvget(int dly, int varid){
    return dcvtbl[(dcvIndex+dly)%dcvDsize][varid] ;
}
"""

def dcvinit(tblsize :int,nvar:int,init:ndarray,c_target:bool=True):
    """
    It generates dcv4brian.c file with all required static variables
    for cpp and cython targets.
    Parameters:
        tblsize  - int     - max number of steps to remember
        nvar     - int     - number of delayed continues variables (DCV)
        init     - ndarray - 1D array with initial value for each DCV
                           - this values fill up the table, therefore
                           - if a variable is a membrane potential of a 
                           - neurons, initialize it at resting potential
                           - if a variable is current or synaptic conductance
                           - initialize it with zero.
        c_only   - bool    - Set yo False if you need numpy code
    """
    
    if c_target:
        with open("dcv4brian.c","w") as fd:
            fd.write("#ifndef __DCV4BRIAN__\n")
            fd.write("#define __DCV4BRIAN__\n")        
            fd.write(f"static double dcv_dt    = {dt};\n")
            fd.write(f"static int    dcvDsize  = {tblsize:d};\n")
            fd.write(f"static int    dcvVsize  = {nvar:d};\n")
            fd.write(f"static int    dcvIndex  = 0;\n")
            fd.write(f"static double dcvtbl[{tblsize:d}][{nvar:d}] = {{"+"\n")
            for cid in range(tblsize):
                fd.write("   {")
                for x in range(nvar):
                    fd.write(f"{init[x]}"+("," if x != nvar-1 else "}") )
                fd.write(",\n" if cid != tblsize-1 else "\n")
            fd.write("};\n")
            fd.write(protofunctions+"\n")
            fd.write("#endif\n")
    else:
        dcvinit.dcvtbl = zeros((tblsize,nvar))
        for n in range(tblsize): dcvinit.dcvtbl[n] = init
        dcvinit.dcvIndex = 0
        dcvinit.dcvDsize = tblsize
        dcvinit.dcvVsize = nvar
    
    

@implementation('cpp', '''
#include <dcv4brian.c>;
void dcvupdate(double x, int i){
    _dcvupdate(x,i);
    return 0;
}
''',include_dirs=[os.getcwd()])
@implementation('cython',f'''
cdef extern from "{os.getcwd()}/dcv4brian.c":
    void _dcvupdate(double, int)
    double _dcvget(int, int)
cdef void dcvupdate(double x, int i):
    _dcvupdate(x,i)
    return 0
''',include_dirs=[os.getcwd()])
@check_units(arg=[1],result=1)
def dcvupdate(x,i):
    """
    dcvupdate shifts index and records current condition of dynamic variables
    given by `x`. To use this numpy realization you need initialize delayed continues variable
    `dcvinit` with argument c_target = False
    Inputs:
        x - a value
        i - an index
    
    """
    dcvinit.dcvIndex = (dcvinit.dcvDsize-1) if dcvinit.dcvIndex == 0 else (dcvinit.dcvIndex-1)
    dcvinit.dcvtbl[dcvinit.dcvIndex,i] = x
    return 0


@implementation('cpp', '''
double dcvget(int dly, int varid){
    return _dcvget(dly, varid);
}
''',include_dirs=[os.getcwd()])
@implementation('cython',f'''
cdef double dcvget(int dly, int varid):
    return _dcvget(dly, varid)
''',include_dirs=[os.getcwd()])
@check_units(arg=[1,1],result=1)
def dcvget(dly,varid):
    """
    `dcvget` returns a value of continues variable defined by variable ID (`varid`)
    `dly` steps ago.
    """
    dcvinit.dcvtbl[(dcvinit.dcvIndex+dly)%dcvinit.dcvDsize,varid]
    return 0
