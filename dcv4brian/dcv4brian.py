from numpy import *
from brian2 import *
import os

protofunction='''

void _dcvinit(){
     dcvtbl = (double **) malloc( sizeof(double *) * dcvDsize );
     for (int r=0 ; r<dcvDsize; r++){
        dcvtbl[r] = (double *) malloc (sizeof(double) * dcvVsize);
        memcpy(dcvtbl[r],dcvtblinit,dcvVsize*sizeof(double));
     }
}

double _dcvsetget(int varid, double varval, int dly, int t_in_steps){
    if ( t_in_steps != dcvTime ){
        if ( dcvtbl == NULL) _dcvinit() ;
        dcvIndex = (dcvIndex == 0)?(dcvDsize-1):(dcvIndex-1);
        dcvTime  = t_in_steps;
    }
    dcvtbl[dcvIndex][varid] = varval;
    return dcvtbl[(dcvIndex+dly)%dcvDsize][varid] ;
}
'''

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
    dcvinit.c_target = c_target
    if c_target:
        with open("dcv4brian.c","w") as fd:
            fd.write("#ifndef __DCV4BRIAN__\n")
            fd.write("#define __DCV4BRIAN__\n")
            fd.write(f"const  int    dcvDsize  = {tblsize:d};\n")
            fd.write(f"const  int    dcvVsize  = {nvar:d};\n")
            fd.write(f"static int    dcvIndex  = 0;\n")
            fd.write(f"static int    dcvTime   = -1;\n")
            fd.write(f"static double **dcvtbl  = NULL;\n")
            fd.write(f"const  double dcvtblinit[{nvar:d}] = ")
            fd.write("   {")
            for x in range(nvar):
                fd.write(f"{init[x]}"+("," if x != nvar-1 else "}") )
            fd.write("; \n")
            fd.write(protofunction+"\n")
            fd.write("#endif\n")
        dcvinit.dcvtbl   = None
        dcvinit.dcvIndex = 0
        dcvinit.dcvTime  = 0
        dcvinit.dcvDsize = tblsize
        dcvinit.dcvVsize = nvar
            
    else:
        
        dcvinit.dcvtbl   = zeros((tblsize,nvar))
        for n in range(tblsize): dcvinit.dcvtbl[n] = copy(init)
        dcvinit.dcvIndex = 0
        dcvinit.dcvTime  = 0
        dcvinit.dcvDsize = tblsize
        dcvinit.dcvVsize = nvar
    
    

@implementation('cpp', '''
#include <string.h>;
#include <dcv4brian.c>;
double dcvsetget(int varid, double varval, int dly, int t_in_steps){
    return _dcvsetget(varid,varval,dly,t_in_steps);
}
''',include_dirs=[os.getcwd()])
@implementation('cython',f'''
cdef extern from "{os.getcwd()}/dcv4brian.c":
    double _dcvsetget(int, double, int, int)
cdef double dcvsetget(int varid, double varval, int dly, int t_in_steps):
    return _dcvsetget(varid,varval,dly,t_in_steps);
''',include_dirs=[os.getcwd()])
@check_units(arg=[1,1,1,1],result=1)
def dcvsetget(varid:(int,ndarray), varval:(float,ndarray), dly:int, t_in_steps:int):
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
    if t_in_steps != dcvinit.dcvTime:
        dcvinit.dcvIndex = (dcvinit.dcvDsize-1) if dcvinit.dcvIndex == 0 else (dcvinit.dcvIndex-1)
        dcvinit.dcvTime = t_in_steps
    dcvinit.dcvtbl[dcvinit.dcvIndex,varid] = copy(varval)
    return dcvinit.dcvtbl[(dcvinit.dcvIndex+dly)%dcvinit.dcvDsize,varid]
