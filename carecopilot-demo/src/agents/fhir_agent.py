"""
Mock FHIR Agent with self-contained conversion
No circular imports - completely independent
"""
from typing import Dict, Any, List
from datetime import datetime

class FHIRAgent:
    """Mock FHIR agent for converting clinical notes to FHIR format"""
    
    def convert_to_fhir(self, clinical_text: str, patient_name: str) -> Dict[str, Any]:
        """Convert clinical note to FHIR bundle with entity extraction"""
        try:
            # Simple entity extraction simulation
            entities = self._extract_entities(clinical_text)
            
            # Generate FHIR bundle
            bundle = self._create_fhir_bundle(patient_name, entities)
            
            # Count resources
            resource_count = len([entry for entry in bundle.get("entry", []) if entry.get("resource")])
            
            return {
                "success": True,
                "bundle": bundle,
                "entities_extracted": entities,
                "resource_count": resource_count,
                "summary": {
                    "conditions": len(entities.get("conditions", [])),
                    "medications": len(entities.get("medications", [])),
                    "observations": len(entities.get("observations", []))
                },
                "processing_time": 0.834
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "bundle": {},
                "entities_extracted": {}
            }
    
    def _extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """Extract medical entities from clinical text"""
        text_lower = text.lower()
        entities = {"conditions": [], "medications": [], "observations": []}
        
        # Common medical conditions
        conditions_map = {
            "diabetes": "Type 2 diabetes mellitus",
            "hypertension": "Essential hypertension", 
            "pneumonia": "Community-acquired pneumonia",
            "heart": "Cardiovascular disease",
            "blood pressure": "Hypertension"
        }
        
        # Common medications
        medications_map = {
            "metformin": "Metformin 500mg",
            "lisinopril": "Lisinopril 10mg",
            "aspirin": "Aspirin 81mg",
            "atorvastatin": "Atorvastatin 20mg",
            "azithromycin": "Azithromycin 250mg",
            "glipizide": "Glipizide 5mg"
        }
        
        # Extract conditions
        for keyword, condition in conditions_map.items():
            if keyword in text_lower:
                entities["conditions"].append({
                    "text": condition,
                    "confidence": 0.85 + (len(keyword) * 0.02),
                    "start": text_lower.find(keyword),
                    "end": text_lower.find(keyword) + len(keyword)
                })
        
        # Extract medications
        for keyword, medication in medications_map.items():
            if keyword in text_lower:
                entities["medications"].append({
                    "text": medication,
                    "confidence": 0.90 + (len(keyword) * 0.01),
                    "start": text_lower.find(keyword),
                    "end": text_lower.find(keyword) + len(keyword)
                })
        
        # Extract vital signs as observations
        vitals = ["blood pressure", "temperature", "heart rate", "hba1c"]
        for vital in vitals:
            if vital in text_lower:
                entities["observations"] = entities.get("observations", [])
                entities["observations"].append({
                    "text": vital.title(),
                    "confidence": 0.88,
                    "type": "vital-sign"
                })
        
        return entities
    
    def _create_fhir_bundle(self, patient_name: str, entities: Dict) -> Dict[str, Any]:
        """Create a FHIR Bundle from extracted entities"""
        bundle = {
            "resourceType": "Bundle",
            "id": f"carecopilot-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": "transaction",
            "timestamp": datetime.now().isoformat(),
            "entry": []
        }
        
        # Patient resource
        patient_resource = {
            "fullUrl": f"Patient/{patient_name.replace(' ', '_')}",
            "resource": {
                "resourceType": "Patient",
                "id": patient_name.replace(' ', '_'),
                "name": [{"given": patient_name.split()[:-1], "family": patient_name.split()[-1]}],
                "active": True
            },
            "request": {"method": "PUT", "url": f"Patient/{patient_name.replace(' ', '_')}"}
        }
        bundle["entry"].append(patient_resource)
        
        # Condition resources
        for i, condition in enumerate(entities.get("conditions", [])):
            condition_resource = {
                "fullUrl": f"Condition/condition_{i+1}",
                "resource": {
                    "resourceType": "Condition",
                    "id": f"condition_{i+1}",
                    "subject": {"reference": f"Patient/{patient_name.replace(' ', '_')}"},
                    "code": {
                        "coding": [{"display": condition["text"]}],
                        "text": condition["text"]
                    },
                    "clinicalStatus": {"coding": [{"code": "active"}]},
                    "recordedDate": datetime.now().strftime("%Y-%m-%d")
                },
                "request": {"method": "POST", "url": "Condition"}
            }
            bundle["entry"].append(condition_resource)
        
        # Medication resources
        for i, medication in enumerate(entities.get("medications", [])):
            med_resource = {
                "fullUrl": f"MedicationStatement/med_{i+1}",
                "resource": {
                    "resourceType": "MedicationStatement",
                    "id": f"med_{i+1}",
                    "subject": {"reference": f"Patient/{patient_name.replace(' ', '_')}"},
                    "medicationCodeableConcept": {
                        "coding": [{"display": medication["text"]}],
                        "text": medication["text"]
                    },
                    "status": "active",
                    "effectiveDateTime": datetime.now().strftime("%Y-%m-%d")
                },
                "request": {"method": "POST", "url": "MedicationStatement"}
            }
            bundle["entry"].append(med_resource)
        
        return bundle

# Create global instance
fhir_agent = FHIRAgent()
