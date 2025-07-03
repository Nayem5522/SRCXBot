import os
import cv2
import fitz  # PyMuPDF
import time

# ⏯️ VIDEO FILE থেকে স্ক্রিনশট (১৫টি)
def screenshot_video(path, count=15):
    screenshots = []
    try:
        vidcap = cv2.VideoCapture(path)
        total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            return screenshots
        frame_gap = max(1, total_frames // (count + 1))

        for i in range(1, count + 1):
            vidcap.set(cv2.CAP_PROP_POS_FRAMES, i * frame_gap)
            success, image = vidcap.read()
            if success:
                filename = f"{path}_screenshot_{i}.jpg"
                cv2.imwrite(filename, image)
                screenshots.append(filename)
        vidcap.release()
    except Exception as e:
        print("Video screenshot error:", e)
    return screenshots

# 📄 DOCUMENT FILE (PDF) থেকে স্ক্রিনশট (১৫টি)
def screenshot_document(path, count=15):
    screenshots = []
    try:
        doc = fitz.open(path)
        total_pages = len(doc)
        page_gap = max(1, total_pages // (count + 1))

        for i in range(1, count + 1):
            page_num = min(i * page_gap, total_pages - 1)
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            filename = f"{path}_page_{page_num+1}.jpg"
            pix.save(filename)
            screenshots.append(filename)
        doc.close()
    except Exception as e:
        print("Document screenshot error:", e)
    return screenshots

# 📁 ফাইলনেম বের করা (না থাকলে fallback)
def extract_filename(file):
    return getattr(file, 'file_name', None) or "unknown_file"

# 📦 ফাইল ডাউনলোড প্রোগ্রেস বার
async def progress_bar(current, total, message):
    try:
        percent = current * 100 / total
        done = round(percent / 10)
        bar = '▣' * done + '▢' * (10 - done)
        done_mb = current / 1024**2
        total_mb = total / 1024**2
        time_passed = round(time.time() % 60)

        text = f"""
📥 Downloading file...
┏━━━━✦[{bar}]✦━━━━
┣ 🟢 Progress : {percent:.1f}%
┣ ✅ Done     : {done_mb:.2f} MB
┣ 📁 Total    : {total_mb:.2f} MB
┣ ⏱️ Time     : {time_passed}s
┗━━━━━━━━━━━━━━━━━━━━
"""
        await message.edit_text(text)
    except:
        pass
