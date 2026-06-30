from typing import List, Optional, Set
from backend.graph.schemas import GraphNode, GraphEdge, PatientGraph
from backend.graph.repository import GraphRepository
from backend.entity_extractor.repository import EntityRepository
from backend.entity_extractor.schemas import MedicalEntity, EntityType
from backend.relationship_extractor.repository import RelationshipRepository
from backend.relationship_extractor.schemas import MedicalRelationship
from backend.config import GRAPH_MAX_DEPTH

class RelationalGraphRepository(GraphRepository):
    """Implementation of GraphRepository that uses our Postgres tables."""
    
    def _entity_to_node(self, entity: MedicalEntity) -> GraphNode:
        return GraphNode(
            id=entity.id or "unknown",
            label=entity.entity_type.value,
            properties={
                "value": entity.value,
                "confidence": entity.confidence,
                "patient_id": entity.patient_id,
                **entity.metadata
            }
        )
        
    def _relationship_to_edge(self, rel: MedicalRelationship) -> GraphEdge:
        return GraphEdge(
            id=rel.id or "unknown",
            source_id=rel.source_entity_id or "unknown",
            target_id=rel.target_entity_id or "unknown",
            relationship_type=rel.relationship_type.value,
            properties={
                "confidence": rel.confidence,
                "source_value": rel.source_entity_value,
                "target_value": rel.target_entity_value,
                **rel.metadata
            }
        )

    async def create_node(self, node: GraphNode) -> str:
        entity = MedicalEntity(
            patient_id=node.properties.get("patient_id", "unknown"),
            entity_type=EntityType(node.label),
            value=node.properties.get("value", ""),
            confidence=node.properties.get("confidence", 1.0),
            metadata={k:v for k,v in node.properties.items() if k not in ["patient_id", "value", "confidence"]}
        )
        return EntityRepository.create(entity)
        
    async def create_edge(self, edge: GraphEdge) -> str:
        rel = MedicalRelationship(
            patient_id=edge.properties.get("patient_id", "unknown"),
            source_entity_id=edge.source_id,
            target_entity_id=edge.target_id,
            source_entity_value=edge.properties.get("source_value", ""),
            target_entity_value=edge.properties.get("target_value", ""),
            relationship_type=edge.relationship_type,
            confidence=edge.properties.get("confidence", 1.0),
            metadata={k:v for k,v in edge.properties.items() if k not in ["confidence", "source_value", "target_value", "patient_id"]}
        )
        return RelationshipRepository.create(rel)
        
    async def delete_node(self, node_id: str) -> bool:
        return EntityRepository.delete(node_id)
        
    async def delete_edge(self, edge_id: str) -> bool:
        return RelationshipRepository.delete(edge_id)
        
    async def get_neighbors(self, node_id: str, max_depth: int = 1) -> List[GraphNode]:
        depth = min(max_depth, GRAPH_MAX_DEPTH)
        visited = set()
        queue = [(node_id, 0)]
        result_nodes: List[GraphNode] = []
        
        while queue:
            current_id, current_depth = queue.pop(0)
            if current_id in visited or current_depth > depth:
                continue
                
            visited.add(current_id)
            if current_depth > 0:
                entity = EntityRepository.get_by_id(current_id)
                if entity:
                    result_nodes.append(self._entity_to_node(entity))
                    
            if current_depth < depth:
                rels = RelationshipRepository.get_by_entity(current_id)
                for r in rels:
                    if r.source_entity_id and r.source_entity_id not in visited:
                        queue.append((r.source_entity_id, current_depth + 1))
                    if r.target_entity_id and r.target_entity_id not in visited:
                        queue.append((r.target_entity_id, current_depth + 1))
                        
        return result_nodes
        
    async def get_patient_graph(self, patient_id: str) -> PatientGraph:
        entities = EntityRepository.get_by_patient(patient_id, limit=1000)
        rels = RelationshipRepository.get_by_patient(patient_id, limit=2000)
        
        nodes = [self._entity_to_node(e) for e in entities]
        edges = [self._relationship_to_edge(r) for r in rels]
        
        return PatientGraph(
            patient_id=patient_id,
            nodes=nodes,
            edges=edges,
            node_count=len(nodes),
            edge_count=len(edges)
        )
        
    async def get_related_entities(self, entity_value: str, patient_id: str, relationship_types: Optional[List[str]] = None) -> List[GraphNode]:
        entities = EntityRepository.search_by_value(patient_id, entity_value)
        if not entities:
            return []
            
        result_nodes = []
        for e in entities:
            rels = RelationshipRepository.get_by_entity(e.id)
            for r in rels:
                if relationship_types and r.relationship_type.value not in relationship_types:
                    continue
                    
                related_id = r.target_entity_id if r.source_entity_id == e.id else r.source_entity_id
                if related_id:
                    related_e = EntityRepository.get_by_id(related_id)
                    if related_e:
                        result_nodes.append(self._entity_to_node(related_e))
                        
        # Deduplicate
        unique_nodes = {n.id: n for n in result_nodes}
        return list(unique_nodes.values())
