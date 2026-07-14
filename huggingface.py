from huggingface_hub import HfApi

api = HfApi()

api.upload_folder(
    folder_path=".",
    repo_id="pvmm/msx-105-colors",
    repo_type="space"
)

