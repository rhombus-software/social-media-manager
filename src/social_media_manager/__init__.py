from .StratusManager import StratusManager
from .Agent import MediaWorkflowPipeline
from .FileParser import FileParser
from argparse import ArgumentParser
import json
def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--file-name", required=True)
    parser.add_argument("--wf_flow", required=True)
    args = parser.parse_args()
    file_name = args.file_name
    wf_flow = args.wf_flow
    if not file_name:
        print("File name not passed")
        return
    
    if wf_flow == 'file_parser':
        # Do file parsing
        download_stratus = StratusManager(bucket_name="raw")
        upload_stratus = StratusManager(bucket_name='parsed')
        download_stratus.download_file(file_name, file_name)
        fp = FileParser(file_name)
        output_file_path = fp.extreme_compress_video()
        upload_stratus.upload_file(output_file_path, output_file_path)
        print("File parsing is completed")
    elif wf_flow == 'workflow_trigger':
        download_stratus = StratusManager(bucket_name="parsed")
        upload_stratus = StratusManager(bucket_name='video-metadata')
        download_stratus.download_file(file_name, file_name)
        wf = MediaWorkflowPipeline()
        analyzed_data = wf.run(file_path=file_name)
        with open("data.json", "w") as file:
            json.dump(analyzed_data["final_json_payload"], file)
        upload_stratus.upload_file("data.json", f"{file_name}_metadata.json")
    else:
        print("No workflow added")
    print("Job Completed")
