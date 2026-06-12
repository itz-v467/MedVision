from langgraph.graph import StateGraph, END
import operator
from typing import TypedDict, Annotated, Sequence
import logging

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    query: str
    patient_id: str
    retrieved_docs: list
    generated_summary: dict

class RAGOrchestrator:
    def __init__(self):
        self.workflow = StateGraph(AgentState)
        self.workflow.add_node("retrieve", self.retrieve_node)
        self.workflow.add_node("generate", self.generate_node)
        self.workflow.set_entry_point("retrieve")
        self.workflow.add_edge("retrieve", "generate")
        self.workflow.add_edge("generate", END)
        self.app = self.workflow.compile()

    def retrieve_node(self, state: AgentState):
        logger.info(f"Retrieving documents for query: {state['query']}")
        # In a real app, query Qdrant here using qdrant_connector
        state['retrieved_docs'] = [{"text": "Patient has opacity in left lung.", "id": "doc1"}]
        return state

    def generate_node(self, state: AgentState):
        logger.info(f"Generating summary for patient {state['patient_id']}")
        from backend.ai.llm.gemini_provider import gemini_provider
        
        evidence = " ".join([d['text'] for d in state.get('retrieved_docs', [])])
        summary = gemini_provider.generate_clinical_summary(
            patient_context=state['query'], 
            retrieved_evidence=evidence
        )
        state['generated_summary'] = summary
        return state

    def run(self, query: str, patient_id: str):
        state = {"query": query, "patient_id": patient_id, "retrieved_docs": [], "generated_summary": {}}
        result = self.app.invoke(state)
        return result['generated_summary']

rag_orchestrator = RAGOrchestrator()
