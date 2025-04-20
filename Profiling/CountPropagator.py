import csv

# We have implemented the optimal Eprfl(Ecnt) from the paper: Optimally Profiling and Tracing Programs THOMAS BALL and JAMES R. LARUS 
# doi: https://dl.acm.org/doi/pdf/10.1145/183432.183527 


class EdgeCountPropagator:

    """Class to collect all edge and node counts from the instrumented edge data"""

    def __init__(self, cfg, edge_source_array, edge_target_array, edge_instr_values,instru_edges):
        self.cfg = cfg

        self.count_instr_edges = [(src,dst)for src, dst in zip(edge_source_array, edge_target_array)]
        self.known_counts = dict(zip(self.count_instr_edges, edge_instr_values))
        self.edge_list=[self.give_ir_ids(e) for e in instru_edges]
        self.all_edges =[self.give_ir_ids(e) for e in cfg.edges()]
        self.cnt = {e: self.known_counts.get(e, 0) for e in self.all_edges}

    def give_ir_ids(self,edge):
        a=-1 if edge[0].irID=="START" else edge[0].irID
        b=-1 if edge[1].irID=="START" else edge[1].irID
        return (a,b)
    
    def give_node_ir(self,n):
        if(n.irID=="START"):
            return -1
        else:
            return n.irID
        
    def propogate_counts(self):
        for node in self.cfg.nodes():
            if node and node.irID == "START":
                start_node = node
                break
        self._dfs(start_node,None)
    
    def _dfs(self,v,parent_edge):
        in_edges = [(u, v) for u in self.cfg.predecessors(v)]
        out_edges = [(v, w) for w in self.cfg.successors(v)]

        in_sum=0
        for e in in_edges:
            e_irs=self.give_ir_ids(e)
            if(e!=parent_edge and e_irs not in self.edge_list):
                self._dfs(e[0],e,)
            in_sum=in_sum+self.cnt[e_irs]
        
        out_sum=0
        for e in out_edges:
            e_irs=self.give_ir_ids(e)
            if(e!=parent_edge and e_irs not in self.edge_list):
                self._dfs(e[1],e)
            out_sum=out_sum+self.cnt[e_irs]

        if parent_edge is not None:
            self.cnt[self.give_ir_ids(parent_edge)]=max(in_sum,out_sum)-min(in_sum,out_sum)


    def compute_node_counts(self):
        node_count=[]
        for node in self.cfg.nodes():
            out_edges = [(node, w) for w in self.cfg.successors(node)]
            n_count=0
            for edge in out_edges:
                n_count+=self.cnt[self.give_ir_ids(edge)]
            node_count.append((self.give_node_ir(node),n_count))
        return node_count


    def write_to_csv(self, edge_csv_path, node_csv_path):
        with open(edge_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Source", "Target", "Count"])
            for (u, v), freq in self.cnt.items():
                u=u if u=="END" else u+1
                v=v if v=="END" else v+1
                writer.writerow([u, v, freq])

        node_count = self.compute_node_counts()
        with open(node_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Node", "Count"])
            for items in node_count:
                node=items[0]
                node=node if node=="END" else node+1
                count=items[1]
                writer.writerow([node, count])