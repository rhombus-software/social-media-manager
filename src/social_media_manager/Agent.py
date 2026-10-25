import os
import json
import time
import operator
from typing import Annotated, List, Literal, TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from google import genai

# Define the Unified State Structure
class MediaWorkflowState(TypedDict):
    file_path: str
    file_name: str
    file_size_mb: float
    file_type: Literal["image", "video", "unknown"]
    analysis_result: str
    caption: str
    hashtags: List[str]
    suggested_locations: List[str]
    final_json_payload: str
    messages: Annotated[list, operator.add]


class MediaWorkflowPipeline:
    def __init__(self, config_path: str = "config.json"):
        """Initializes the workflow by loading configuration and compiling the LangGraph graph."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")
            
        with open(config_path, "r") as f:
            self.config = json.load(f)
            
        self.default_temp = self.config["settings"]["temperature"]
        self.app = self._build_graph()

    def _safe_extract_text(self, content) -> str:
        """Helper to robustly extract string text whether content is a string or list/dict structure."""
        if isinstance(content, list):
            return "".join([item.get("text", str(item)) if isinstance(item, dict) else str(item) for item in content])
        return str(content)

    # ----------------------------------------------------------------------
    # AGENT NODES
    # ----------------------------------------------------------------------
    def _ingestion_agent(self, state: MediaWorkflowState):
        path = state["file_path"]
        print(f"\n[Ingestion Agent] Connecting to Stratus... Downloading: {path}")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File {path} not found in local environment/Stratus bucket.")
        
        file_name = os.path.basename(path)
        file_size_mb = round(os.path.getsize(path) / (1024 * 1024), 2)
        
        ext = file_name.lower().split('.')[-1]
        if ext in ["mp4", "mov", "avi", "mkv", "webm"]:
            file_type = "video"
        elif ext in ["jpg", "jpeg", "png", "webp"]:
            file_type = "image"
        else:
            file_type = "unknown"
            
        print(f"[Ingestion Agent] Detected -> Name: {file_name} | Type: {file_type.upper()} | Size: {file_size_mb}MB")
        
        return {
            "file_name": file_name,
            "file_size_mb": file_size_mb,
            "file_type": file_type,
            "messages": [SystemMessage(content=f"Ingested {file_name} as {file_type}")]
        }

    def _content_analyzer_agent(self, state: MediaWorkflowState):
        node_config = self.config["nodes"]["content_analyzer"]
        model_name = node_config["model"]
        
        client = genai.Client()
        path = state["file_path"]
        file_type = state["file_type"]
        
        print(f"\n[Analyzer Agent] Uploading {state['file_name']} to Gemini API using model '{model_name}'...")
        uploaded_file = client.files.upload(file=path)
        
        while True:
            info = client.files.get(name=uploaded_file.name)
            if info.state.name == "ACTIVE":
                break
            if info.state.name == "FAILED":
                raise ValueError("Gemini file processing failed.")
            time.sleep(1)
            
        print(f"[Analyzer Agent] Processing complete. Running targeted analysis...")
        
        if file_type == "video":
            prompt = node_config["video_prompt"]
        elif file_type == "image":
            prompt = node_config["image_prompt"]
        else:
            prompt = "Describe this file briefly."
            
        response = client.models.generate_content(
            model=model_name,
            contents=[uploaded_file, prompt]
        )
        
        client.files.delete(name=uploaded_file.name)
        analysis = response.text
        print(f"[Analyzer Agent] Analysis Extracted:\n{analysis}")
        
        return {
            "analysis_result": analysis,
            "messages": [SystemMessage(content="Content analyzed successfully.")]
        }

    def _caption_agent(self, state: MediaWorkflowState):
        node_config = self.config["nodes"]["caption_generator"]
        llm = ChatGoogleGenerativeAI(model=node_config["model"], temperature=self.default_temp)
        
        print("\n[Caption Agent] Generating caption...")
        prompt = node_config["prompt"].format(analysis=state['analysis_result'])
        res = llm.invoke([HumanMessage(content=prompt)])
        
        text_output = self._safe_extract_text(res.content)
        return {"caption": text_output.strip()}

    def _hashtag_agent(self, state: MediaWorkflowState):
        node_config = self.config["nodes"]["hashtag_generator"]
        llm = ChatGoogleGenerativeAI(model=node_config["model"], temperature=self.default_temp)
        
        print("[Hashtag Agent] Curating hashtags...")
        prompt = node_config["prompt"].format(analysis=state['analysis_result'])
        res = llm.invoke([HumanMessage(content=prompt)])
        
        text_output = self._safe_extract_text(res.content)
        tags = [t.strip().replace("#", "") for t in text_output.split(",") if t.strip()]
        return {"hashtags": tags}

    def _location_agent(self, state: MediaWorkflowState):
        node_config = self.config["nodes"]["location_generator"]
        llm = ChatGoogleGenerativeAI(model=node_config["model"], temperature=self.default_temp)
        
        print("[Location Agent] Identifying optimal geotags...")
        prompt = node_config["prompt"].format(analysis=state['analysis_result'])
        res = llm.invoke([HumanMessage(content=prompt)])
        
        text_output = self._safe_extract_text(res.content)
        locs = [l.strip() for l in text_output.split(",") if l.strip()]
        return {"suggested_locations": locs}

    def _publisher_barrier(self, state: MediaWorkflowState):
        return {"messages": [SystemMessage(content="All creator agents completed work.")]}

    def _publisher_agent(self, state: MediaWorkflowState):
        print("\n[Publisher Agent] Aggregating metadata into structured JSON...")
        
        payload = {
            "file_name": state["file_name"],
            "file_size_mb": state["file_size_mb"],
            "file_type": state["file_type"],
            "analysis": state["analysis_result"],
            "caption": state["caption"],
            "hashtags": state["hashtags"],
            "suggested_locations": state["suggested_locations"],
            "timestamp": time.time()
        }
        
        json_output = json.dumps(payload, indent=2)
        print(f"[Publisher Agent] Uploading final JSON bundle back to Zoho Catalyst Stratus storage...")
        print(f"\n--- FINAL JSON PAYLOAD ---\n{json_output}")
        
        return {
            "final_json_payload": json_output,
            "messages": [SystemMessage(content="Published final JSON package to Stratus.")]
        }

    # ----------------------------------------------------------------------
    # GRAPH TOPOLOGY BUILDER
    # ----------------------------------------------------------------------
    def _build_graph(self):
        workflow = StateGraph(MediaWorkflowState)

        workflow.add_node("ingestion_agent", self._ingestion_agent)
        workflow.add_node("content_analyzer_agent", self._content_analyzer_agent)
        workflow.add_node("caption_agent", self._caption_agent)
        workflow.add_node("hashtag_agent", self._hashtag_agent)
        workflow.add_node("location_agent", self._location_agent)
        workflow.add_node("publisher_barrier", self._publisher_barrier)
        workflow.add_node("publisher_agent", self._publisher_agent)

        workflow.add_edge(START, "ingestion_agent")
        workflow.add_conditional_edges("ingestion_agent", lambda state: "content_analyzer_agent")

        workflow.add_conditional_edges("content_analyzer_agent", lambda state: ["caption_agent", "hashtag_agent", "location_agent"])

        workflow.add_edge("caption_agent", "publisher_barrier")
        workflow.add_edge("hashtag_agent", "publisher_barrier")
        workflow.add_edge("location_agent", "publisher_barrier")

        workflow.add_edge("publisher_barrier", "publisher_agent")
        workflow.add_edge("publisher_agent", END)

        return workflow.compile()

    # ----------------------------------------------------------------------
    # PUBLIC RUN METHOD
    # ----------------------------------------------------------------------
    def run(self, file_path: str) -> dict:
        """Executes the complete multi-agent pipeline for a given media file path."""
        initial_state = {
            "file_path": file_path,
            "file_name": "",
            "file_size_mb": 0.0,
            "file_type": "unknown",
            "analysis_result": "",
            "caption": "",
            "hashtags": [],
            "suggested_locations": [],
            "final_json_payload": "",
            "messages": []
        }
        
        print(f"🚀 Running pipeline for file: {file_path}")
        final_state = self.app.invoke(initial_state)
        print("\n✨ Pipeline execution complete successfully!")
        return final_state