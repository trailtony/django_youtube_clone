import os
from imagekitio import ImageKit
from youtube.logging_utils import get_logger, log_with_context, log_exception

logger = get_logger(__name__)

def get_imagekit_client():
    return ImageKit()
    
def upload_video(file_data: bytes, file_name: str, folder: str = "videos") -> dict:
    public_key = os.environ.get("IMAGEKIT_PUBLIC_KEY")
    
    if not public_key:
        logger.error("IMAGEKIT_PUBLIC_KEY not found in environment variables")
        raise ValueError("ImageKit public key is not configured")
    
    logger.info(f"Uploading video to ImageKit: {file_name}")
    
    try:
        client = get_imagekit_client()
        
        response = client.files.upload(
            file=file_data,
            file_name=file_name,
            public_key=public_key
        )
        
        logger.info(f"Video upload successful: {file_name} -> File ID: {response.file_id}")
        
        return {
            "file_id": response.file_id,
            "url": response.url
        }
    except Exception as e:
        logger.error(f"Failed to upload video {file_name} to ImageKit: {str(e)}", exc_info=True)
        raise
    
    
def upload_thumbnail(file_data: bytes, file_name: str, folder: str = "thumbnails") -> dict:
    import base64
    public_key = os.environ.get("IMAGEKIT_PUBLIC_KEY")
    
    if not public_key:
        logger.error("IMAGEKIT_PUBLIC_KEY not found in environment variables")
        raise ValueError("ImageKit public key is not configured")
    
    logger.info(f"Uploading thumbnail to ImageKit: {file_name}")
    
    try:
        if file_data.startswith("data:"):
            base64_data = file_data.split(",", 1)[1]
            image_bytes = base64.b64decode(base64_data)
        else:
            image_bytes = base64.b64decode(file_data)
            
        client = get_imagekit_client()
        
        response = client.files.upload(
            file=image_bytes,
            file_name=file_name,
            public_key=public_key
        )
        
        logger.info(f"Thumbnail upload successful: {file_name} -> File ID: {response.file_id}")
        
        return {
            "file_id": response.file_id,
            "url": response.url
        }
    except Exception as e:
        logger.error(f"Failed to upload thumbnail {file_name} to ImageKit: {str(e)}", exc_info=True)
        raise
    
    