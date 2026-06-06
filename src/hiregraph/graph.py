from langgraph.graph import StateGraph, END

from hiregraph.state import HireGraphState
from hiregraph.nodes.ingest import ingest
from hiregraph.nodes.classify import classify_candidate

builder = StateGraph(HireGraphState)

builder.add_node("ingest", ingest)
builder.add_node("classify", classify_candidate)

builder.set_entry_point("ingest")

builder.add_edge("ingest", "classify")
builder.add_edge("classify", END)

graph = builder.compile()