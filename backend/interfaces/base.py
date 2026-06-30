from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ClinicalAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, file_path: str, patient_id: str) -> Dict[str, Any]:
        """Analyze a clinical file (e.g., X-ray, ECG) and return structured findings."""
        pass

    @abstractmethod
    async def get_supported_formats(self) -> List[str]:
        """Return a list of supported file formats."""
        pass

class DocumentProcessor(ABC):
    @abstractmethod
    async def process(self, file_path: str, patient_id: str) -> Dict[str, Any]:
        """Process a document and return structured clinical data."""
        pass

    @abstractmethod
    async def extract_text(self, file_path: str) -> str:
        """Extract raw text from the document."""
        pass

class StreamProcessor(ABC):
    @abstractmethod
    async def process_stream(self, source: str, patient_id: str) -> Dict[str, Any]:
        """Process a continuous stream (audio, video, wearable) and return findings."""
        pass

    @abstractmethod
    async def get_supported_formats(self) -> List[str]:
        """Return a list of supported stream protocols or formats."""
        pass

class AlertGenerator(ABC):
    @abstractmethod
    async def evaluate(self, patient_id: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate patient context and generate a list of alerts if criteria are met."""
        pass

    @abstractmethod
    async def get_alert_types(self) -> List[str]:
        """Return the types of alerts this generator can produce."""
        pass

class KnowledgeGraphProvider(ABC):
    @abstractmethod
    async def connect(self):
        """Establish connection to the graph database."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close connection to the graph database."""
        pass

    @abstractmethod
    async def query(self, cypher: str) -> List[Dict[str, Any]]:
        """Execute a graph query (e.g., Cypher) and return results."""
        pass

    @abstractmethod
    async def create_node(self, label: str, properties: Dict[str, Any]) -> str:
        """Create a node and return its ID."""
        pass

    @abstractmethod
    async def create_relationship(self, from_id: str, to_id: str, rel_type: str, properties: Dict[str, Any]) -> str:
        """Create a relationship between two nodes and return its ID."""
        pass
