"""Vector database for long-term agent memory"""
import chromadb
from chromadb.config import Settings
import json
import hashlib
from datetime import datetime
from config import CHROMA_DIR, COLLECTION_NAME


class AgentMemory:
    """Long-term memory using ChromaDB"""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    
    def _generate_id(self, text: str) -> str:
        """Generate unique ID from text"""
        return hashlib.md5(text.encode()).hexdigest()[:16]
    
    def save_research(self, product_name: str, category: str, research_data: dict):
        """Save research results to memory"""
        try:
            doc_id = self._generate_id(f"{product_name}_{datetime.now().isoformat()}")
            
            # Create searchable text
            searchable_text = f"""
            Product: {product_name}
            Category: {category}
            Research: {json.dumps(research_data, ensure_ascii=False)[:2000]}
            """
            
            self.collection.add(
                documents=[searchable_text],
                metadatas=[{
                    "product_name": product_name,
                    "category": category,
                    "timestamp": datetime.now().isoformat(),
                    "data": json.dumps(research_data, ensure_ascii=False)
                }],
                ids=[doc_id]
            )
            return True
        except Exception as e:
            print(f"⚠️ Memory save error: {e}")
            return False
    
    def add_research(self, product_data: dict, market_data: dict):
        """Compatibility wrapper for dashboard clients."""
        return self.save_research(
            product_data.get("product_name", "Unknown"),
            product_data.get("category", "Unknown"),
            {"product_analysis": product_data, "market_research": market_data},
        )

    def get_all(self) -> list:
        """Return all stored research in a dashboard-friendly shape."""
        try:
            results = self.collection.get(include=["metadatas"])
            records = []
            for record_id, metadata in zip(results.get("ids", []), results.get("metadatas", [])):
                records.append({
                    "id": record_id,
                    "product_name": metadata.get("product_name", "Unknown"),
                    "category": metadata.get("category", "Unknown"),
                    "timestamp": metadata.get("timestamp", ""),
                    "data": json.loads(metadata.get("data", "{}")),
                })
            return sorted(records, key=lambda item: item.get("timestamp", ""), reverse=True)
        except Exception as e:
            print(f"Memory list error: {e}")
            return []

    def search_similar(self, product_name: str, category: str, n_results: int = 3) -> list:
        """Find similar past research"""
        try:
            query = f"Product: {product_name} Category: {category}"
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            similar = []
            if results['metadatas']:
                for meta in results['metadatas'][0]:
                    similar.append({
                        "product_name": meta.get("product_name"),
                        "category": meta.get("category"),
                        "timestamp": meta.get("timestamp"),
                        "data": json.loads(meta.get("data", "{}"))
                    })
            return similar
        except Exception as e:
            print(f"⚠️ Memory search error: {e}")
            return []
    
    def get_all_count(self) -> int:
        """Get total number of stored memories"""
        try:
            return self.collection.count()
        except:
            return 0
    
    def clear_all(self):
        """Clear all memories (use with caution!)"""
        try:
            self.client.delete_collection(COLLECTION_NAME)
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            print(f"⚠️ Clear error: {e}")
            return False
