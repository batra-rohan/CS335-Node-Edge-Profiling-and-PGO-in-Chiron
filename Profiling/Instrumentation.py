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
        array_incr_inst=ChironAST.AssignmentCommand(":edge_counters"+"["+str(idx)+"]",":edge_counters"+"["+str(idx)+"]" + " +1",True)
        irHandler.addInstruction(ir,array_incr_inst,instr_added)

        # add instruction(source assignment)
        source_ass_inst=ChironAST.AssignmentCommand(":edge_source"+"["+str(idx)+"]",str(block_A.irID+1),True)
        irHandler.addInstruction(ir,source_ass_inst,instr_added+1)

        # add instruction(target assignment)
        target_ass_inst=ChironAST.AssignmentCommand(":edge_target"+"["+str(idx)+"]",str(block_B.irID+1),True)
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
        #Adding node counter instruction at the start of each basic block
        array_incr_inst=ChironAST.AssignmentCommand(":node_counters"+"["+str(index)+"]",":node_counters"+"["+str(index)+"]" + " +1",True)
        irHandler.addInstruction(ir,array_incr_inst,lidx+instr_added,add_node_cnt=1)
        instr_added+=1

def compute_edge_weights(cfg, loop_multiplier=10):
    def dfs_backedges(cfg, start, visited, rec_stack, backedges):
        visited.add(start)
        rec_stack.add(start)
        for neighbor in cfg.successors(start):
            if neighbor not in visited:
                dfs_backedges(cfg, neighbor, visited, rec_stack, backedges)
            elif neighbor in rec_stack:
                backedges.add((start, neighbor))
        rec_stack.remove(start)

    def find_backedges(cfg):
        visited = set()
        rec_stack = set()
        backedges = set()
        for node in cfg.nodes():
            if node not in visited:
                dfs_backedges(cfg, node, visited, rec_stack, backedges)
        return backedges

    def find_nat_loop(cfg, x, y):
        """Returns the natural loop for backedge x -> y."""
        loop_nodes = set([y])
        stack = [x]
        while stack:
            node = stack.pop()
            if node not in loop_nodes:
                loop_nodes.add(node)
                stack.extend(cfg.predecessors(node))
        return loop_nodes

    def find_loop_entries(cfg, backedges):
        loop_entries = {}
        for x, y in backedges:
            nat_loop = find_nat_loop(cfg, x, y)
            if y not in loop_entries:
                loop_entries[y] = []
            loop_entries[y].append((x, nat_loop))
        return loop_entries

    def loop_exit_edges(cfg, loop_nodes):
        exits = set()
        for a in loop_nodes:
            for b in cfg.successors(a):
                if b not in loop_nodes:
                    exits.add((a, b))
        return exits

    backedges = find_backedges(cfg)
    loop_entries = find_loop_entries(cfg, backedges)
    edge_weights = {}
    node_weights = {}

    def topological_sort(cfg):
        visited = set()
        postorder = []

        def visit(node):
            if node not in visited:
                visited.add(node)
                for neighbor in cfg.successors(node):
                    visit(neighbor)
                postorder.append(node)

        for node in cfg.nodes():
            visit(node)

        postorder.reverse()
        return postorder

    topo_order = topological_sort(cfg)

    for node in topo_order:
        incoming_edges = [(u, node) for u in cfg.predecessors(node) if (u, node) not in backedges]
        node_weights[node] = sum(edge_weights.get(edge, 0) for edge in incoming_edges)

        is_loop_entry = node in loop_entries
        W = node_weights[node] * loop_multiplier if is_loop_entry else node_weights[node]

        exits = loop_exit_edges(cfg, set().union(*(loop[1] for loop in loop_entries.get(node, [])))) if is_loop_entry else set()
        num_non_exit = len([v for v in cfg.successors(node) if (node, v) not in exits])

        for succ in cfg.successors(node):
            edge = (node, succ)
            if edge in exits:
                edge_weights[edge] = W / len(exits) if exits else 0
            else:
                edge_weights[edge] = (W - sum(edge_weights[e] for e in exits)) / num_non_exit if num_non_exit else 0

    cfg.set_edge_weights(edge_weights)

def add_instrumentation_code(irHandler):
    ir=irHandler.ir
    #Computing leader Indices
    leaderIndices=compute_leader_indices(ir)

    # Constructing the CFG for the original code
    cfg = cfgB.buildCFG(ir, "control_flow_graph", False)

    compute_edge_weights(cfg)

    # Print the edges of the CFG along with their weights
    cfg_edges = cfg.edges()
    edge_weights = cfg.get_edge_weights()

    print("CFG Edges and Weights:")
    for edge in cfg_edges:
        weight = edge_weights.get(edge, 0)
        print(f"Edge {edge[0].irID} -> {edge[1].irID}, Weight: {weight}")

    cfg_edges=cfg.edges()
    num_edges=len(cfg_edges)

    #Node Counters Initialisation
    node_array_init_inst=ChironAST.ArrayInitialise("node_counters",len(leaderIndices))
    irHandler.addInstruction(ir,node_array_init_inst,0)

    #Edge counter array Initialisation
    edge_array_init_inst=ChironAST.ArrayInitialise("edge_counters",num_edges)
    irHandler.addInstruction(ir,edge_array_init_inst,0)
    #Edge source and target arrays Initialisation
    edge_source_init_inst=ChironAST.ArrayInitialise("edge_source",num_edges)
    irHandler.addInstruction(ir,edge_source_init_inst,0)
    edge_target_init_inst=ChironAST.ArrayInitialise("edge_target",num_edges)
    irHandler.addInstruction(ir,edge_target_init_inst,0)
    global instr_added
    instr_added=4
    # Add instrumentation code for edges
    add_edge_instrum_code(irHandler,ir,cfg)
    edge_code=instr_added
    # Add instrumentation code for nodes
    add_node_instrum_code(leaderIndices,irHandler,ir)
    # Jump to the user source code after initialisation
    goto_code_inst=ChironAST.ConditionCommand(False)
    irHandler.addInstruction(ir,goto_code_inst,4,offset=edge_code-3)
    return leaderIndices
