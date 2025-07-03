import os
import cv2
import fitz
import time

def screenshot_video(path):
    screenshots = []
    try:
        vidcap = cv2.VideoCapture(path)
        total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_gap = total_frames // 15
        for i in range(15):
            vidcap.set(cv2.CAP_PROP_POS_FRAMES, i * frame_gap)
            success, image = vidcap.read()
            if success:
                filename = f"screenshot_{i+1}.jpg"
                cv2.imwrite(filename, image)
                screenshots.append(filename)
        vidcap.release()
    except Exception as e:
        print("Video screenshot error:", e)
    return screenshots

def screenshot_document(path):
    screenshots = []
    try:
        doc = fitz.open(path)
        for i in range(min(15, len(doc))):
            page = doc.load_page(i)
            pix = page.get_pixmap()
            filename = f"page_{i+1}.jpg"
            pix.save(filename)
            screenshots.append(filename)
    except Exception as e:
        print("Document screenshot error:", e)
    return screenshots

def extract_filename(file):
    return getattr(file, 'file_name', 'unknown')

async def progress_bar(current, total, message):
    percent = current * 100 / total
    done = round(percent / 10)
    bar = '▣' * done + '▢' * (10 - done)
    done_mb = current / 1024**2
    total_mb = total / 1024**2
    time_passed = round(time.time() % 60)
    text = f"""
📥 Downloading file...
┏━━━━✦[{bar}]✦━━━━
┣ 📦 Pʀᴏɢʀᴇꜱꜱ : {percent:.1f}%
┣ ✅ Dᴏɴᴇ : {done_mb:.2f} MB
┣ 📁 Tᴏᴛᴀʟ : {total_mb:.2f} MB
┣ 🕒 Tɪᴍᴇ : {time_passed}s
┗━━━━━━━━━━━━━━━━━━━━
"""
    try:
        await message.edit_text(text)
    except:
        pass
