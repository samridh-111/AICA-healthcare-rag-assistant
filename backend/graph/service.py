from typing import List, Optional
from backend.graph.schemas import GraphNode, GraphEdge, PatientGraph
from backend.graph.repository import GraphRepository
from backend.graph.relational_adapter import RelationalGraphRepository

class GraphService:
    def __init__(self, graph_repo: Optional[GraphRepository] = None):
        self.repo = graph_repo or RelationalGraphRepository()
        
    async def get_patient_graph(self, patient_id: str) -> PatientGraph:
        return await self.repo.get_patient_graph(patient_id)
        
    async def get_entity_neighbors(self, entity_id: str, depth: int = 1) -> List[GraphNode]:
        return await self.repo.get_neighbors(entity_id, max_depth=depth)
        
    async def find_related_entities(self, entity_value: str, patient_id: str, relationship_types: Optional[List[str]] = None) -> List[GraphNode]:
        return await self.repo.get_related_entities(entity_value, patient_id, relationship_types)
        
    async def build_graph_from_extraction(self, patient_id: str, entities: List, relationships: List) -> PatientGraph:
        """
        Creates nodes and edges from raw extraction data.
        In the relational model, they are already persisted during extraction,
        so we just fetch the resulting graph.
        """
        # If we had Neo4j, we would iterate and create_node/create_edge here
        # But our RelationalGraphRepository reads directly from the SQL tables
        return await self.repo.get_patient_graph(patient_id)
