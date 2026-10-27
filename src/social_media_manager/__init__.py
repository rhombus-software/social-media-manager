from .StratusManager import StratusManager
from .Agent import MediaWorkflowPipeline
import json
def main() -> None:
    stratus = StratusManager(bucket_name="raw")
    stratus.download_file("12.mp4", "video.mp4")
    wf = MediaWorkflowPipeline()
    analyzed_data = wf.run(file_path='video.mp4')
    with open("data.json", "w") as file:
        json.dump(analyzed_data["final_json_payload"], file)
    stratus.upload_file("data.json", "12.json")
    print("Hello from social-media-manager!", stratus)
