"""
视频/图片清晰度判断工具
支持视频文件（mp4, avi, mov等）和图片文件（jpg, png, jpeg等）
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ffprobe 路径缓存
_ffprobe_path_cache: Optional[str] = None


class VideoInfo:
    """视频信息类"""
    
    def __init__(self, width: int, height: int, quality: str):
        self.width = width
        self.height = height
        self.quality = quality
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "width": self.width,
            "height": self.height,
            "quality": self.quality
        }
    
    def __repr__(self) -> str:
        return f"VideoInfo(width={self.width}, height={self.height}, quality={self.quality})"


def get_video_quality(video_path: str) -> str:
    """
    获取视频清晰度
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        清晰度字符串（如 480p, 720p, 1080p, 2K, 4K等）
    """
    info = get_video_info(video_path)
    return info.quality


def get_video_info(video_path: str) -> VideoInfo:
    """
    获取视频/图片详细信息
    支持视频文件（mp4, avi, mov等）和图片文件（jpg, png, jpeg等）
    
    Args:
        video_path: 视频/图片文件路径
        
    Returns:
        VideoInfo 对象
        
    Raises:
        FileNotFoundError: 文件不存在
        RuntimeError: ffprobe 执行失败或解析失败
    """
    # 检查文件是否存在
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"文件不存在: {video_path}")
    
    # 使用 ffprobe 获取视频/图片信息
    # ffprobe 可以将图片识别为视频流，所以使用相同的命令即可
    ffprobe_path = get_ffprobe_path()
    cmd = [
        ffprobe_path,
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-select_streams", "v:0",
        video_path,
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ffprobe 执行超时: {video_path}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"执行 ffprobe 失败: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError(f"ffprobe 未找到，请先安装 ffmpeg 或设置 FFPROBE_PATH 环境变量")
    
    # 解析 JSON 输出
    try:
        probe_output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"解析 ffprobe 输出失败: {e}")
    
    streams = probe_output.get("streams", [])
    if not streams:
        raise RuntimeError("未找到视频流或图片流")
    
    width = streams[0].get("width", 0)
    height = streams[0].get("height", 0)
    
    if width <= 0 or height <= 0:
        raise RuntimeError(f"无法获取有效的分辨率信息: {width}x{height}")
    
    quality = determine_quality(width, height)
    
    return VideoInfo(width=width, height=height, quality=quality)


def determine_quality(width: int, height: int) -> str:
    """
    根据分辨率判断清晰度
    
    行业标准说明：
    视频清晰度等级（如1080p、720p）在行业标准中通常指的是视频的"短边"分辨率：
      - 横屏视频（宽度 > 高度）：短边 = 高度（垂直分辨率）
      - 竖屏视频（高度 > 宽度）：短边 = 宽度（水平分辨率）
    
    这是因为清晰度等级反映的是视频在显示时的"有效分辨率"：
      - 横屏：1920x1080 = 1080p（短边=高度1080）
      - 竖屏：1080x1920 = 1080p（短边=宽度1080）
    
    注意：传统行业标准（如ITU-R BT.709）主要基于横屏视频定义，以垂直分辨率为准。
    但对于竖屏视频（特别是手机录屏），按短边判断更符合实际显示效果和用户认知。
    实际应用中，YouTube、Netflix等平台对竖屏视频也采用短边判断方法。
    
    标准清晰度等级（按短边分辨率）：
      - 240p: 短边 >= 240 像素（低清）
      - 360p: 短边 >= 360 像素（低清）
      - 480p: 短边 >= 480 像素（SD - Standard Definition，标清）
      - 720p: 短边 >= 720 像素（HD - High Definition，高清）
      - 1080p: 短边 >= 1080 像素（Full HD，全高清）
      - 1440p: 短边 >= 1440 像素（2K/QHD - Quad HD，2K高清）
      - 2160p: 短边 >= 2160 像素（4K/UHD - Ultra HD，超高清）
    
    判断示例：
      - 1920x1080（横屏）= 1080p（短边=高度1080）
      - 1080x1920（竖屏）= 1080p（短边=宽度1080）
      - 1280x720（横屏）= 720p（短边=高度720）
      - 720x1280（竖屏）= 720p（短边=宽度720）
    
    参考标准：
      - ITU-R BT.709（HDTV标准）
      - ITU-R BT.2020（UHDTV标准）
      - SMPTE（电影电视工程师协会）标准
    
    Args:
        width: 宽度（像素）
        height: 高度（像素）
        
    Returns:
        清晰度字符串
    """
    # 根据视频方向确定判断基准
    # 横屏（w > h）：以高度判断；竖屏（h > w）：以宽度判断
    # 即：以短边为准
    if width > height:
        # 横屏：以高度（短边）判断
        resolution = height
    else:
        # 竖屏：以宽度（短边）判断
        resolution = width
    
    # 4K (2160p) - Ultra HD / UHD
    # 行业标准：短边 >= 2160 像素
    # 常见分辨率：3840x2160（横屏），2160x3840（竖屏）
    if resolution >= 2160:
        return "4K (2160p)"
    
    # 2K (1440p) - Quad HD / QHD
    # 行业标准：短边 >= 1440 像素
    # 常见分辨率：2560x1440（横屏），1440x2560（竖屏）
    if resolution >= 1440:
        return "2K (1440p)"
    
    # 1080p - Full HD
    # 行业标准：短边 >= 1080 像素
    # 常见分辨率：1920x1080（横屏），1080x1920（竖屏）
    if resolution >= 1080:
        return "1080p"
    
    # 720p - HD (High Definition)
    # 行业标准：短边 >= 720 像素
    # 常见分辨率：1280x720（横屏），720x1280（竖屏）
    if resolution >= 720:
        return "720p"
    
    # 480p - SD (Standard Definition)
    # 行业标准：短边 >= 480 像素
    # 常见分辨率：854x480（横屏），480x854（竖屏）
    if resolution >= 480:
        return "480p"
    
    # 360p - 低清
    # 行业标准：短边 >= 360 像素
    # 常见分辨率：640x360（横屏），360x640（竖屏）
    if resolution >= 360:
        return "360p"
    
    # 240p - 低清
    # 行业标准：短边 >= 240 像素
    # 常见分辨率：426x240（横屏），240x426（竖屏）
    if resolution >= 240:
        return "240p"
    
    # 低于240p - 超低清
    return f"{width}x{height} (低清)"


def find_ffprobe_path() -> str:
    """
    查找 ffprobe 的路径
    优先级：环境变量 > PATH > 常见安装路径
    
    Returns:
        ffprobe 路径
    """
    # 1. 检查环境变量
    env_path = os.getenv("FFPROBE_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path
    
    # 2. 检查 PATH 中是否有 ffprobe
    try:
        which_result = subprocess.run(
            ["which", "ffprobe"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if which_result.returncode == 0:
            path = which_result.stdout.strip()
            if path and os.path.isfile(path):
                return path
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # 使用 shutil.which（跨平台）
    import shutil
    path = shutil.which("ffprobe")
    if path:
        return path
    
    # 3. 尝试常见的安装路径
    import glob
    
    common_paths = [
        "/opt/homebrew/bin/ffprobe",                    # macOS Homebrew (Apple Silicon)
        "/usr/local/bin/ffprobe",                       # macOS Homebrew (Intel) / Linux
        "/usr/bin/ffprobe",                             # Linux 系统路径
        "C:\\ffmpeg\\bin\\ffprobe.exe",                 # Windows 常见路径
        "C:\\Program Files\\ffmpeg\\bin\\ffprobe.exe", # Windows 程序目录
    ]
    
    for path_pattern in common_paths:
        # 处理通配符路径（如 Homebrew Cellar）
        if "*" in path_pattern:
            matches = glob.glob(path_pattern)
            if matches:
                return matches[0]
        # 直接检查文件是否存在
        if os.path.isfile(path_pattern):
            return path_pattern
    
    # 如果都找不到，返回默认值，让系统尝试
    return "ffprobe"


def get_ffprobe_path() -> str:
    """
    获取 ffprobe 路径（带缓存）
    
    Returns:
        ffprobe 路径
    """
    global _ffprobe_path_cache
    if _ffprobe_path_cache is None:
        _ffprobe_path_cache = find_ffprobe_path()
    return _ffprobe_path_cache


def reset_ffprobe_path_cache():
    """重置路径缓存（主要用于测试）"""
    global _ffprobe_path_cache
    _ffprobe_path_cache = None


def check_ffprobe_available() -> Optional[str]:
    """
    检查 ffprobe 是否可用
    
    Returns:
        如果可用返回 None，否则返回错误信息
    """
    path = get_ffprobe_path()
    try:
        result = subprocess.run(
            [path, "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
        return None
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
        return f"ffprobe 未找到或不可用 (路径: {path})，请先安装 ffmpeg 或设置 FFPROBE_PATH 环境变量: {e}"


def main():
    """主函数 - 命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="获取视频/图片清晰度信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s scripts/image/000714.jpg
  %(prog)s /path/to/video.mp4
  %(prog)s --quality scripts/image/10340.jpg
  %(prog)s --check
        """
    )
    parser.add_argument(
        "file_path",
        type=str,
        nargs="?",
        help="视频或图片文件路径"
    )
    parser.add_argument(
        "--quality",
        action="store_true",
        help="仅输出清晰度（不输出详细信息）"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="检查 ffprobe 是否可用"
    )
    
    args = parser.parse_args()
    
    # 检查 ffprobe 是否可用
    if args.check:
        error = check_ffprobe_available()
        if error:
            print(f"错误: {error}")
            sys.exit(1)
        else:
            path = get_ffprobe_path()
            print(f"✓ ffprobe 可用 (路径: {path})")
            sys.exit(0)
    
    # 如果没有提供文件路径，显示帮助
    if not args.file_path:
        parser.print_help()
        sys.exit(1)
    
    # 检查文件是否存在
    if not os.path.exists(args.file_path):
        print(f"错误: 文件不存在: {args.file_path}")
        sys.exit(1)
    
    try:
        # 获取视频/图片信息
        info = get_video_info(args.file_path)
        
        # 输出结果
        if args.quality:
            # 仅输出清晰度
            print(info.quality)
        elif args.json:
            # JSON 格式输出
            print(json.dumps(info.to_dict(), indent=2, ensure_ascii=False))
        else:
            # 详细信息输出
            print(f"文件: {args.file_path}")
            print(f"分辨率: {info.width} x {info.height}")
            print(f"清晰度: {info.quality}")
    
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

