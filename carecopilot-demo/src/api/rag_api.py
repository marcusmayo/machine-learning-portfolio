"""
Mock RAG API with self-contained responses
No circular imports - completely independent
"""
from typing import Dict, Any
from datetime import datetime

class QueryEngine:
    """Mock RAG service for demo purposes with realistic responses"""
    
    def __init__(self):
        self.mock_documents = [
            {
                "document_id": "PT001_discharge_summary",
                "content": "DISCHARGE INSTRUCTIONS: 1. Follow up with primary care physician in 1-2 weeks. 2. Continue medications as prescribed: Aspirin 81mg daily, Metoprolol 25mg twice daily. 3. Monitor vital signs daily: Temperature: 97.8°F, Heart Rate: 68 bpm, Blood Pressure: 128/84 mmHg.",
                "patient_id": "PT001",
                "similarity": 0.462
            },
            {
                "document_id": "PT002_progress_note", 
                "content": "Progress Note: Patient shows improvement in post-operative recovery. Surgical site healing well. Discharge planning initiated. Medications reviewed: continue current regimen. Follow-up scheduled with surgeon in 10 days.",
                "patient_id": "PT002",
                "similarity": 0.391
            },
            {
                "document_id": "PT003_medical_summary",
                "content": "Medical Summary: 45-year-old patient with Type 2 diabetes mellitus, well-controlled on Metformin 1000mg BID. Recent HbA1c: 6.8%. No complications noted. Continue current diabetes management plan.",
                "patient_id": "PT003", 
                "similarity": 0.334
            }
        ]
    
    def query(self, search_query: str) -> Dict[str, Any]:
        """Simulate RAG query with realistic medical responses"""
        try:
            # Filter documents based on query keywords
            query_lower = search_query.lower()
            relevant_docs = []
            
            for doc in self.mock_documents:
                content_lower = doc["content"].lower()
                if any(keyword in content_lower for keyword in query_lower.split()):
                    relevant_docs.append(doc)
            
            if not relevant_docs:
                # If no exact matches, return all documents with lower similarity
                relevant_docs = [{**doc, "similarity": doc["similarity"] * 0.6} for doc in self.mock_documents]
            
            # Generate contextual answer
            if "discharge" in query_lower:
                answer = "Based on the discharge documentation, patients should follow up with their primary care physician within 1-2 weeks, continue prescribed medications including Aspirin 81mg daily and Metoprolol 25mg twice daily, and monitor vital signs regularly."
            elif "medication" in query_lower:
                answer = "Current medications include Aspirin 81mg daily, Metoprolol 25mg twice daily, and Metformin 1000mg BID for diabetes management. All medications should be continued as prescribed."
            elif "summary" in query_lower:
                answer = "Medical summaries show patients with well-controlled conditions including Type 2 diabetes (HbA1c: 6.8%) and post-operative recovery progressing well with appropriate follow-up care scheduled."
            else:
                answer = f"Found relevant medical information related to '{search_query}'. Review the source documents below for detailed clinical information and patient care instructions."
            
            return {
                "success": True,
                "answer": answer,
                "search_results": [
                    {
                        "document_id": doc["document_id"],
                        "content": doc["content"],
                        "similarity": doc["similarity"],
                        "chunk_index": 0,
                        "patient_id": doc["patient_id"]
                    } for doc in relevant_docs[:3]
                ],
                "total_results": len(relevant_docs),
                "query_time": 0.145
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "search_results": [],
                "total_results": 0
            }

# Create global instance
query_engine = QueryEngine()
