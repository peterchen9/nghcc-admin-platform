"""
影音下載 API
整合 yt-dlp，提供影片資訊查詢與下載功能
"""
import os
import re
import tempfile
import mimetypes

from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import yt_dlp


# 暫存下載目錄
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), 'humnos_downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _safe_filename(name: str) -> str:
    """移除非法字元並截斷至 100 字元"""
    safe = re.sub(r'[\\/*?:"<>|]', '', name)
    return safe[:100]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def video_info(request):
    """
    取得影片資訊（標題、時長、縮圖等）
    POST body: { "url": "https://..." }
    """
    url = request.data.get('url', '').strip()
    if not url:
        return Response({'error': '請提供影片網址'}, status=400)

    # 清除 playlist 參數
    clean_url = re.sub(r'&list=[^&]+', '', url)

    ydl_opts = {
        'noplaylist': True,
        'skip_download': True,
        'quiet': True,
        'user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android'],
            }
        },
        'nocheckcertificate': True,
        'ffmpeg_location': '/usr/bin/ffmpeg',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            return Response({
                'title': info.get('title', ''),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', ''),
                'url': clean_url,
            })
    except Exception as e:
        return Response({'error': f'無法取得影片資訊: {str(e)}'}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def video_download(request):
    """
    下載影片/音檔並回傳檔案
    POST body: {
        "url": "https://...",
        "format": "mp4" | "mp3",
        "quality": "1080" | "720" | "480" | "360",
        "bitrate": "320k" | "256k" | "128k",
        "filename": "自訂檔名（選填）"
    }
    """
    url = request.data.get('url', '').strip()
    format_choice = request.data.get('format', 'mp4')
    quality = request.data.get('quality', '720')
    audio_bitrate = request.data.get('bitrate', '256k')
    custom_name = request.data.get('filename', '').strip()

    if not url:
        return Response({'error': '請提供影片網址'}, status=400)

    clean_url = re.sub(r'&list=[^&]+', '', url)

    # 檔名模板
    if custom_name:
        outtmpl = os.path.join(DOWNLOAD_DIR, f'{_safe_filename(custom_name)}.%(ext)s')
    else:
        outtmpl = os.path.join(DOWNLOAD_DIR, '%(title).100s.%(ext)s')

    ydl_opts = {
        'noplaylist': True,
        'outtmpl': outtmpl,
        'user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android'],
            }
        },
        'nocheckcertificate': True,
        'rm_cache_dir': True,
        'ffmpeg_location': '/usr/bin/ffmpeg',
    }

    if format_choice == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': audio_bitrate.replace('k', ''),
            }],
        })
    else:
        target_q = quality or '720'
        ydl_opts.update({
            'format': (
                f'bestvideo[height<={target_q}][ext=mp4]'
                f'+bestaudio[ext=m4a]'
                f'/best[height<={target_q}]/best'
            ),
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=True)
            file_path = ydl.prepare_filename(info)

            if format_choice == 'mp3':
                file_path = os.path.splitext(file_path)[0] + '.mp3'

        if not os.path.exists(file_path):
            return Response({'error': '下載的檔案不存在'}, status=500)

        # 設定 Content-Type
        content_type = 'audio/mpeg' if format_choice == 'mp3' else 'video/mp4'
        filename = os.path.basename(file_path)

        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
            as_attachment=True,
            filename=filename,
        )

        # 下載完成後刪除暫存檔案（透過 streaming_content wrapper）
        original_streaming = response.streaming_content

        def cleanup_streaming():
            try:
                yield from original_streaming
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

        response.streaming_content = cleanup_streaming()
        return response

    except Exception as e:
        return Response({'error': f'下載發生錯誤: {str(e)}'}, status=500)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def humnos_page_view(request):
    return render(request, 'humnos/humnos_page.html')

