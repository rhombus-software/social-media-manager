from .StratusManager import StratusManager
from .Agent import MediaWorkflowPipeline
from argparse import ArgumentParser
import json
def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--file-name", required=True)
    args = parser.parse_args()
    file_name = args.file_name
    if not file_name:
        print("File name not passed")
        return
    stratus = StratusManager(bucket_name="raw")
    stratus.download_file(file_name, file_name)
    wf = MediaWorkflowPipeline()
    analyzed_data = wf.run(file_path=file_name)
    with open("data.json", "w") as file:
        json.dump(analyzed_data["final_json_payload"], file)
    stratus.upload_file("data.json", f"{file_name}_metadata.json")
    print("Job Completed")
