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

def add_edge_instrum_code(irHandler, ir, cfg, selected_edges):
    global instr_added
    # Get the set of edges selected for instrumentation (edges not in max spanning tree)
    cfg_edges = selected_edges
    for idx,edge in enumerate(cfg_edges):
        block_A=edge[0]
        block_B=edge[1]
        if(block_A.irID=="END" or block_B.irID=="END"):
        #Skiping end blocks
            continue
        if(block_A.irID=="START"):
            block_A.irID=-1
        if(block_B.irID=="START"):
            block_B.irID=-1
        lstinstr_pos = block_A.irID+len(block_A.instrlist)+instr_added
        # print(ir[lstinstr_pos][0])
        # if(not isinstance(ir[lstinstr_pos][0], ChironAST.ConditionCommand)):
        #     print("Inside")
        #     print(ir[lstinstr_pos][0])
        #     goto_inst=ChironAST.ConditionCommand(False)
        #     irHandler.addInstruction(ir,goto_inst,lstinstr_pos+1,offset=-(block_A.irID+len(block_A.instrlist)+1))

        # add instruction(edge counter increment )
        array_incr_inst=ChironAST.AssignmentCommand(":edge_counters"+"["+str(idx)+"]",":edge_counters"+"["+str(idx)+"]" + " +1",True)
        irHandler.addInstruction(ir,array_incr_inst,instr_added)

        # add instruction(source assignment)
        source_ass_inst=ChironAST.AssignmentCommand(":edge_source"+"["+str(idx)+"]",str(block_A.irID),True)
        irHandler.addInstruction(ir,source_ass_inst,instr_added+1)

        # add instruction(target assignment)
        target_ass_inst=ChironAST.AssignmentCommand(":edge_target"+"["+str(idx)+"]",str(block_B.irID),True)
        irHandler.addInstruction(ir,target_ass_inst,instr_added+2)

        # add instruction(go to target block)
        goto_inst=ChironAST.ConditionCommand(False)
        irHandler.addInstruction(ir,goto_inst,instr_added+3,offset=block_B.irID+2)
        
        instr_added+=4

        # modify instruction (modify source block jump)
        irHandler.update_target(ir,lstinstr_pos+4,-(block_A.irID+len(block_A.instrlist)+4)) 

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

    # Step 1: Topological Order
    topo_order = topological_sort(cfg)

    # Step 2: Assign START node weight
    START = next((n for n in cfg.nodes() if n.irID == "START"), None)
    if START is not None:
        node_weights[START] = 1.0
    else:
        raise ValueError("START node not found in CFG.")

    for node in topo_order:
        if node not in node_weights:
            incoming_edges = [(u, node) for u in cfg.predecessors(node) if (u, node) not in backedges]
            node_weights[node] = sum(edge_weights.get(edge, 0) for edge in incoming_edges)

        is_loop_entry = node in loop_entries
        W = node_weights[node] * loop_multiplier if is_loop_entry else node_weights[node]

        exits = loop_exit_edges(cfg, set().union(*(loop[1] for loop in loop_entries.get(node, [])))) if is_loop_entry else set()
        num_non_exit = len([v for v in cfg.successors(node) if (node, v) not in exits])

        for succ in cfg.successors(node):
            edge = (node, succ)
            if edge in backedges:
                continue  # skip for now
            if edge in exits:
                edge_weights[edge] = W / len(exits) if exits else 0
            else:
                edge_weights[edge] = (W - sum(edge_weights.get(e, 0) for e in exits)) / num_non_exit if num_non_exit else 0

    cfg.set_edge_weights(edge_weights)

def compute_edges_for_instrumentation(cfg):
    import heapq

    edge_weights = cfg.get_edge_weights()
    edges = cfg.edges()
    nodes = list(cfg.nodes())
    for n in nodes:
        if(n.irID=="START"):
            startBB=n
        if(n.irID=="END"):
            endBB=n
    
    # Convert edge_weights to max-heap format by negating weights
    max_heap = []
    for idx, (u, v) in enumerate(edges):
        weight = edge_weights.get((u, v))
        if weight is None:
            weight = 0
        heapq.heappush(max_heap, (-weight, idx, u, v))
    
    parent = {node: node for node in nodes}
    
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rootX = find(x)
        rootY = find(y)
        if rootX != rootY:
            parent[rootY] = rootX
            return True
        return False

    spanning_tree_edges = set() 
    spanning_tree_edges.add((endBB,startBB))
    union(endBB,startBB)
    while max_heap and len(spanning_tree_edges) < len(nodes) - 1:
        neg_w, _, u, v = heapq.heappop(max_heap)
        if union(u, v):
            spanning_tree_edges.add((u, v))
    
    all_edges = set(edges)
    instrumentation_edges = all_edges - spanning_tree_edges
    return instrumentation_edges

def add_instrumentation_code(irHandler):
    ir=irHandler.ir
    #Computing leader Indices
    leaderIndices=compute_leader_indices(ir)

    # Constructing the CFG for the original code
    cfg = cfgB.buildCFG(ir, "control_flow_graph", False)
    #        # Print the edges in the CFG
    # print("Edges in the CFG:")
    # for edge in cfg.edges():
    #     print(f"{edge[0].irID} -> {edge[1].irID}")
    compute_edge_weights(cfg)
    # cfg_edges = cfg.edges()
    # edge_weights = cfg.get_edge_weights()

    # print("CFG Edges and Weights:")
    # for edge in cfg_edges:
    #     weight = edge_weights.get(edge, 0)
    #     print(f"Edge {edge[0].irID} -> {edge[1].irID}, Weight: {weight}")


    instrumentation_edges = compute_edges_for_instrumentation(cfg)
    print("Edges to be instrumented (not in max spanning tree):")
    for edge in instrumentation_edges:
        print(f"Edge {edge[0].irID} -> {edge[1].irID}")
    # instrumentation_edges = cfg.edges()

    # Print the edges of the CFG along with their weights


    cfg_edges=cfg.edges()
    num_edges=len(instrumentation_edges)

    #Edge counter array Initialisation
    edge_array_init_inst=ChironAST.ArrayInitialise("edge_counters",num_edges)
    irHandler.addInstruction(ir,edge_array_init_inst,0)
    #Edge source and target arrays Initialisation
    edge_source_init_inst=ChironAST.ArrayInitialise("edge_source",num_edges)
    irHandler.addInstruction(ir,edge_source_init_inst,0)
    edge_target_init_inst=ChironAST.ArrayInitialise("edge_target",num_edges)
    irHandler.addInstruction(ir,edge_target_init_inst,0)
    global instr_added
    instr_added=3
    # Add instrumentation code for selected edges
    add_edge_instrum_code(irHandler, ir, cfg, instrumentation_edges)
    edge_code=instr_added
    # Jump to the user source code after initialisation
    goto_code_inst=ChironAST.ConditionCommand(False)
    irHandler.addInstruction(ir,goto_code_inst,3,offset=edge_code-2)
    return instrumentation_edges
