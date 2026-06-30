from abc import ABC, abstractmethod
from typing import List, Optional
from backend.graph.schemas import GraphNode, GraphEdge, PatientGraph

class GraphRepository(ABC):
    @abstractmethod
    async def create_node(self, node: GraphNode) -> str:
        """Create a node in the graph and return its ID."""
        pass
        
    @abstractmethod
    async def create_edge(self, edge: GraphEdge) -> str:
        """Create a directed edge between two nodes and return its ID."""
        pass
        
    @abstractmethod
    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and all its connected edges."""
        pass
        
    @abstractmethod
    async def delete_edge(self, edge_id: str) -> bool:
        """Delete a specific edge."""
        pass
        
    @abstractmethod
    async def get_neighbors(self, node_id: str, max_depth: int = 1) -> List[GraphNode]:
        """Get all neighboring nodes connected to a given node up to max_depth."""
        pass
        
    @abstractmethod
    async def get_patient_graph(self, patient_id: str) -> PatientGraph:
        """Get the complete knowledge graph for a patient."""
        pass
        
    @abstractmethod
    async def get_related_entities(self, entity_value: str, patient_id: str, relationship_types: Optional[List[str]] = None) -> List[GraphNode]:
        """Search for an entity by value and return its connected nodes, optionally filtered by relationship type."""
        pass
