from .StratusManager import StratusManager
def main() -> None:
    stratus = StratusManager(bucket_name="raw")
    stratus.download_file("12.mp4", "video.mp4")
    stratus.upload_file("video.mp4", "video.mp4")
    print("Hello from social-media-manager!", stratus)
