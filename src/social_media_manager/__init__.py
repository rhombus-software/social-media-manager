from .StratusManager import StratusManager
from .Agent import MediaWorkflowPipeline
def main() -> None:
    stratus = StratusManager(bucket_name="raw")
    stratus.download_file("12.mp4", "video.mp4")
    wf = MediaWorkflowPipeline()
    wf.run(file_path='video.mp4')
    # stratus.upload_file("video.mp4", "video.mp4")
    print("Hello from social-media-manager!", stratus)
