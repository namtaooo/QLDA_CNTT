import os
import logging
from huggingface_hub import snapshot_download

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cấu hình Model mặc định
DEFAULT_MODEL_REPO = "Qwen/Qwen2-1.5B-Instruct"
LOCAL_MODEL_DIR = "./models/qwen2-1.5b"

def download_model_if_not_exists(repo_id: str = DEFAULT_MODEL_REPO, local_dir: str = LOCAL_MODEL_DIR):
    """
    Kiểm tra xem mô hình đã tồn tại ở local_dir chưa.
    Nếu chưa, tự động tải mô hình từ HuggingFace bằng snapshot_download.
    """
    logger.info(f"Checking if model {repo_id} exists locally at {local_dir}...")
    
    # Kiểm tra xem có file config.np hay model safetensors không (chứng tỏ đã tải)
    is_downloaded = False
    if os.path.exists(local_dir):
        # Kiểm tra sơ bộ xem thư mục có file không thay vì rỗng
        files = os.listdir(local_dir)
        if any(f.endswith('.json') or f.endswith('.safetensors') or f.endswith('.bin') for f in files):
            is_downloaded = True

    if is_downloaded:
        logger.info(f"✅ Model found locally at {local_dir}. Skipping download.")
        return True
    
    logger.info(f"⏳ Model not found. Starting automatic download for {repo_id}. This may take a while depending on your network...")
    
    try:
        # Tải mô hình. ignore_patterns để bỏ qua các file không cần thiết nếu muốn tối ưu
        snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False, # Tải file thật thay vì symlink giữ cache
        )
        logger.info(f"✅ Model successfully downloaded to {local_dir}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download model: {e}")
        return False

if __name__ == "__main__":
    download_model_if_not_exists()
