import sys
from cfg.ChironCFG import *
import ChironAST.ChironAST as ChironAST
import cfg.cfgBuilder as cfgB
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


    # Constructing the CFG
    cfg = cfgB.buildCFG(ir, "control_flow_graph", False)
    cfg_edges=cfg.edges()
    num_edges=len(cfg_edges)


    #Node Counters Initialisation
    node_array_init_inst=ChironAST.ArrayInitialise("node_counters",len(leaderIndices))
    irHandler.addInstruction(ir,node_array_init_inst,0)


    #Edge counter arrays Initialisation
    edge_array_init_inst=ChironAST.ArrayInitialise("edge_counters",num_edges)
    irHandler.addInstruction(ir,edge_array_init_inst,0)
    edge_source_init_inst=ChironAST.ArrayInitialise("edge_source",num_edges)
    irHandler.addInstruction(ir,edge_source_init_inst,0)
    edge_target_init_inst=ChironAST.ArrayInitialise("edge_target",num_edges)
    irHandler.addInstruction(ir,edge_target_init_inst,0)


    instr_added=4
    for index,lidx in enumerate(leaderIndices):
        #Adding Counters in basic blocks
        array_incr_inst=ChironAST.ArrayIncrement("node_counters",index)
        irHandler.addInstruction(ir,array_incr_inst,lidx+instr_added)
        instr_added+=1

    for idx,edge in enumerate(cfg_edges):
        print("Idx",idx)
        block_A=edge[0]
        block_B=edge[1]
        print("Edge!")
        print(block_A.irID)
        print(block_B.irID)
        if(block_A.irID=="START" or block_B.irID=="END"):
            continue
        # add instruction(counter increment [idx],instr_added)
        array_incr_inst=ChironAST.ArrayIncrement("edge_counters",index)
        irHandler.addInstruction(ir,array_incr_inst,instr_added)

        # add instruction(source assignment[idx]=blockA.irid,instrr_added+1)
        source_ass_inst=ChironAST.ArrayAssignment("edge_source",index,block_A.irID)
        irHandler.addInstruction(ir,source_ass_inst,instr_added+1)

        # add instruction(target assignment, instr_added+2)
        target_ass_inst=ChironAST.ArrayAssignment("edge_target",index,block_B.irID)
        irHandler.addInstruction(ir,target_ass_inst,instr_added+2)

        # add instruction(go to [(num_edges-idx-1)*4+block_B.irID+1],instr_added+3)
        goto_inst=ChironAST.ConditionCommand(False)
        irHandler.addInstruction(ir,goto_inst,instr_added+3,block_B.irID+1)
        
        instr_added+=4

        # modify instruction (block_a.irlist[-1][1]==instr_added - (block_a.irid + len(block_a.irlist)-1))
        lstinstr = block_A.irID+len(block_A.instrlist)-1
        print("last instr",lstinstr+instr_added)
        print("ir length",len(ir))
        irHandler.update_target(ir,lstinstr+instr_added,-(lstinstr+1))
        #
        #

    return leaderIndices
