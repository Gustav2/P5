import matplotlib.pyplot as plt
import numpy as np
import colorsys
from typing import List
from ..config import LOW_POWERED_NODES

class NetworkTopology:
    def __init__(self, nodes: List):
        self.nodes = nodes
        self.edges: List[dict] = []
        self.positions: dict = {}
        
        self._extract_edges()
        self._force_directed_layout()
        self._assign_colors()

    def _extract_edges(self):
        connected = set()
        
        for node in self.nodes:
            neighbors = getattr(node, 'neighbors', {})
            for neighbor_id in neighbors.keys():
                edge_key = tuple(sorted([node.id, neighbor_id]))
                if edge_key not in connected:
                    self.edges.append({'from': node.id, 'to': neighbor_id})
                    connected.add(edge_key)
    
    def _force_directed_layout(self, iterations: int = 300):
        n = len(self.nodes)
        if n == 0:
            return
        
        cols = int(np.ceil(np.sqrt(n)))
        for i, node in enumerate(self.nodes):
            x = (i % cols) * 2.0 + np.random.uniform(-0.3, 0.3)
            y = (i // cols) * 2.0 + np.random.uniform(-0.3, 0.3)
            self.positions[node.id] = np.array([x, y], dtype=float)
        
        adj = {node.id: set() for node in self.nodes}
        for edge in self.edges:
            adj[edge['from']].add(edge['to'])
            adj[edge['to']].add(edge['from'])
        
        k = 2.0
        temp = 1.0
        
        for iteration in range(iterations):
            forces = {node.id: np.array([0.0, 0.0]) for node in self.nodes}
            
            for i, n1 in enumerate(self.nodes):
                for n2 in self.nodes[i+1:]:
                    diff = self.positions[n1.id] - self.positions[n2.id]
                    dist = np.linalg.norm(diff)
                    if dist < 0.01:
                        diff = np.random.uniform(-1, 1, 2)
                        dist = 0.01
                    
                    repulsion = (k * k / dist) * (diff / dist)
                    forces[n1.id] += repulsion
                    forces[n2.id] -= repulsion
            
            for edge in self.edges:
                diff = self.positions[edge['to']] - self.positions[edge['from']]
                dist = np.linalg.norm(diff)
                if dist > 0.01:
                    attraction = (dist / k) * (diff / dist)
                    forces[edge['from']] += attraction * 0.5
                    forces[edge['to']] -= attraction * 0.5
            
            for node in self.nodes:
                force = forces[node.id]
                force_mag = np.linalg.norm(force)
                if force_mag > 0:
                    displacement = (force / force_mag) * min(force_mag, temp)
                    self.positions[node.id] += displacement
            
            temp *= 0.95
        
        all_pos = np.array(list(self.positions.values()))
        center = all_pos.mean(axis=0)
        for node_id in self.positions:
            self.positions[node_id] -= center
    
    def _assign_colors(self):
        low_powered = [n for n in self.nodes if n.id < LOW_POWERED_NODES]
        high_powered = [n for n in self.nodes if n.id >= LOW_POWERED_NODES]
        
        for i, node in enumerate(low_powered):
            hue = 0.5 + (i / max(len(low_powered), 1)) * 0.2
            node._color = colorsys.hsv_to_rgb(hue, 0.7, 0.85)
        
        for i, node in enumerate(high_powered):
            hue = (i / max(len(high_powered), 1)) * 0.15
            node._color = colorsys.hsv_to_rgb(hue, 0.7, 0.85)
        
        n_edges = len(self.edges)
        for i, edge in enumerate(self.edges):
            hue = i / max(n_edges, 1)
            edge['color'] = colorsys.hsv_to_rgb(hue, 0.4, 0.7)
    
    def save(self, filename: str = "topology.png", figsize=(12, 12), node_size=400, show_labels=True):
        _, ax = plt.subplots(figsize=figsize)
        ax.set_aspect('equal')
        ax.set_facecolor('#fafafa')
        
        for edge in self.edges:
            if edge['from'] in self.positions and edge['to'] in self.positions:
                p1 = self.positions[edge['from']]
                p2 = self.positions[edge['to']]
                ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 
                       color=edge['color'], linewidth=1.5, alpha=0.7, zorder=1)
        
        for node in self.nodes:
            pos = self.positions[node.id]
            color = getattr(node, '_color', (0.5, 0.5, 0.5))
            
            ax.scatter(pos[0], pos[1], s=node_size, c=[color],
                      edgecolors='black', linewidths=1.5, zorder=2)
            
            if show_labels:
                ax.annotate(str(node.id), pos, ha='center', va='center',
                           fontsize=8, fontweight='bold', color='white', zorder=3)
        
        ax.axis('off')
        plt.title("Network Topology", fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='#fafafa')
        plt.close()