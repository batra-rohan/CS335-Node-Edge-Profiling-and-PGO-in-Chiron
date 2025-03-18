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
    print("Leader Indices")
    for i,lidx in enumerate(leaderIndices):
        print("Index on node",i)
        print("Leader index of block",lidx)

    return leaderIndices
def add_edge_instrum_code(irHandler,ir,cfg):
    global instr_added
    cfg_edges=cfg.edges()
    for idx,edge in enumerate(cfg_edges):
        block_A=edge[0]
        block_B=edge[1]
        if(block_A.irID=="START" or block_B.irID=="END" or cfg.get_edge_label(block_A,block_B)=='Cond_True'):
        #Skiping start , end and fallthrough edges
            continue
        lstinstr_pos = block_A.irID+len(block_A.instrlist)+instr_added
        if(not isinstance(ir[lstinstr_pos][0], ChironAST.ConditionCommand)):
            # Skipping "always" taken edges linked to unconditional instruction
            continue
        # add instruction(edge counter increment )
        array_incr_inst=ChironAST.ArrayIncrement("edge_counters",idx)
        irHandler.addInstruction(ir,array_incr_inst,instr_added)

        # add instruction(source assignment)
        source_ass_inst=ChironAST.ArrayAssignment("edge_source",idx,block_A.irID+1)
        irHandler.addInstruction(ir,source_ass_inst,instr_added+1)

        # add instruction(target assignment)
        target_ass_inst=ChironAST.ArrayAssignment("edge_target",idx,block_B.irID+1)
        irHandler.addInstruction(ir,target_ass_inst,instr_added+2)

        # add instruction(go to target block)
        goto_inst=ChironAST.ConditionCommand(False)
        irHandler.addInstruction(ir,goto_inst,instr_added+3,offset=block_B.irID+2)
        
        instr_added+=4

        # modify instruction (modify source block jump)
        irHandler.update_target(ir,lstinstr_pos+4,-(block_A.irID+len(block_A.instrlist)+4))

def add_node_instrum_code(leaderIndices,irHandler,ir):
    global instr_added
    for index,lidx in enumerate(leaderIndices):
        #Adding Counters in basic blocks
        array_incr_inst=ChironAST.ArrayIncrement("node_counters",index)
        irHandler.addInstruction(ir,array_incr_inst,lidx+instr_added,add_node_cnt=1)
        instr_added+=1

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

    # Node Counter Initialisation of the first node
    # node_counter_init_inst=ChironAST.ArrayAssignment("node_counters",0,1)
    # irHandler.addInstruction(ir,node_counter_init_inst,1)

    #Edge counter arrays Initialisation
    edge_array_init_inst=ChironAST.ArrayInitialise("edge_counters",num_edges)
    irHandler.addInstruction(ir,edge_array_init_inst,0)
    edge_source_init_inst=ChironAST.ArrayInitialise("edge_source",num_edges)
    irHandler.addInstruction(ir,edge_source_init_inst,0)
    edge_target_init_inst=ChironAST.ArrayInitialise("edge_target",num_edges)
    irHandler.addInstruction(ir,edge_target_init_inst,0)
    global instr_added
    instr_added=4
    add_edge_instrum_code(irHandler,ir,cfg)
    edge_code=instr_added
    add_node_instrum_code(leaderIndices,irHandler,ir)
    # Jump to the user source code
    goto_code_inst=ChironAST.ConditionCommand(False)
    irHandler.addInstruction(ir,goto_code_inst,4,offset=edge_code-3)
    return leaderIndices
