import sys
from cfg.ChironCFG import *
import ChironAST.ChironAST as ChironAST
def compute_leader_indices(ir):
    leaderIndices = [0,len(ir)]
    # finding leaders in the IR
    for idx, item in enumerate(ir):
        #print(idx, item)
        if isinstance(item[0], ChironAST.ConditionCommand):
            # updating then branch meta data
            if idx + 1 < len(ir) and (idx + 1 not in leaderIndices):
                #  Adds Fall through
                leaderIndices.append(idx + 1)

            if idx + item[1] < len(ir) and (idx + item[1]
                    not in leaderIndices) and (isinstance(item[0], ChironAST.ConditionCommand)):
                # Adds target of the jump
                leaderIndices.append(idx + item[1])
    leaderIndices.sort()
    return leaderIndices
def add_instrumentation_code(irHandler):
    ir=irHandler.ir
    #Computing leader Indices
    leaderIndices=compute_leader_indices(ir)
    #Counters Initialisation
    array_init_inst=ChironAST.ArrayInitialise("node_counters",len(leaderIndices))
    irHandler.addInstruction(ir,array_init_inst,0)
    instr_added=1
    for index,lidx in enumerate(leaderIndices):
        #Adding Counters in basic blocks
        array_incr_inst=ChironAST.ArrayIncrement("node_counters",index)
        irHandler.addInstruction(ir,array_incr_inst,lidx+instr_added)
        instr_added+=1
    return leaderIndices
