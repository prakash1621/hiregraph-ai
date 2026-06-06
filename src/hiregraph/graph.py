from langgraph.graph import StateGraph, END
from hiregraph.state import HireGraphState
from hiregraph.nodes.ingest import ingest

builder = StateGraph(HireGraphState)
builder.add_node("ingest", ingest)
builder.set_entry_point("ingest")
builder.add_edge("ingest", END)

graph = builder.compile()
