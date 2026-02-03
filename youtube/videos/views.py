from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from youtube.logging_utils import get_logger, log_with_context, log_exception
from .models import Video
from .forms import VideoUploadForm
from .imagekit_client import upload_video, upload_thumbnail

logger = get_logger(__name__)


# Create your views here.

@login_required
@require_POST
def video_upload(request):
    log_with_context(logger, 'info', 'Video upload initiated', 
                    user_id=request.user.id)
    
    form = VideoUploadForm(request.POST, request.FILES)
    
    if form.is_valid():
        video_file = form.cleaned_data['video_file']
        custom_thumbnail = request.POST.get("thumbnail_data", "")
        
        log_with_context(logger, 'info', 'Processing video upload',
                        filename=video_file.name, 
                        size_bytes=video_file.size,
                        content_type=video_file.content_type,
                        user_id=request.user.id)
        
        try:
            result = upload_video(
                file_data=video_file.read(),
                file_name=video_file.name
            )
            
            log_with_context(logger, 'info', 'Video uploaded to ImageKit',
                            file_id=result['file_id'],
                            filename=video_file.name)
            
            thumbnail_url = ""
            if custom_thumbnail and custom_thumbnail.startswith("data:image"):
                try:
                    base_name = video_file.name.rsplit(".", 1)[0]
                    thumb_result = upload_thumbnail(
                        file_data=custom_thumbnail,
                        file_name=f"{base_name}_thumb.jpg"
                    )
                    thumbnail_url = thumb_result["url"]
                    log_with_context(logger, 'info', 'Custom thumbnail uploaded',
                                    file_id=thumb_result['file_id'])
                except Exception as e:
                    log_exception(logger, 'Thumbnail upload failed', e,
                                user_id=request.user.id,
                                filename=f"{base_name}_thumb.jpg")
            
            video = Video.objects.create(
                user=request.user,
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                file_id=result["file_id"],
                video_url=result["url"],
                thumbnail_url=thumbnail_url
            )
            
            log_with_context(logger, 'info', 'Video record created',
                            video_id=video.id,
                            user_id=request.user.id,
                            title=video.title[:50])  # Truncate title for logging
            
            return JsonResponse({
                "success": True,
                "video_id": video.id,
                "message": "Video uploaded successfully."
            })
        except Exception as e:
            log_exception(logger, 'Video upload failed', e,
                        user_id=request.user.id,
                        filename=video_file.name)
            return JsonResponse({"success": False, "error": "An error occurred during upload. Please try again."})
    
    errors = []
    for field, field_errors in form.errors.items():
        for error in field_errors:
            errors.append(f"{field}: {error}" if field != "__all__" else error)
    
    log_with_context(logger, 'warning', 'Form validation failed',
                    user_id=request.user.id,
                    errors='; '.join(errors))
    return JsonResponse({"success": False, "errors": ";".join(errors)})


@login_required
def video_upload_page(request):
    return render(request, "videos/upload.html", {"form": VideoUploadForm()})