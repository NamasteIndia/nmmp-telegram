import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

# Configuration
API_ID =   # Telegram API ID
API_HASH = "" # Telegram API Hash
BOT_TOKEN = "" # Make BOT using @botfather and enter the token
JAR_PATH = "/root/nmmp/nmm-protect/build/libs/protect.jar" # No need to change if renamed the JAR file.
RULES_FILE = "convertRules.txt" # Can be uploaded using the BOT
MAPPING_FILE = "mapping.txt" # Make one empty txt file in the ROOT directory 
BUILD_OUTPUT_DIR = "/root/build"  # Directory to be cleaned after processing
OWNER_USER_ID =   # Replace with your actual Telegram user ID

# Upload tracking maps
upload_start_times = {}
last_uploaded_percent = {}

async def progress(current, total, message, start_time):
    elapsed_time = time.time() - start_time
    percent = int(current * 100 / total)
    speed_kb = (current / elapsed_time) / 1024 if elapsed_time > 0 else 0
    try:
        await message.edit(
            f"Download Progress: {percent}% - Speed: {speed_kb:.2f} KB/s\nTime elapsed: {elapsed_time:.2f} seconds"
        )
    except:
        pass

async def upload_progress(current, total, message, *args):
    percent = int(current * 100 / total)
    key = message.id

    if key not in upload_start_times:
        upload_start_times[key] = time.time()

    if last_uploaded_percent.get(key) == percent:
        return
    last_uploaded_percent[key] = percent

    elapsed = time.time() - upload_start_times[key]
    speed_kb = (current / elapsed) / 1024 if elapsed > 0 else 0

    try:
        if percent < 100:
            await message.edit(f"Upload Progress: {percent}% - Speed: {speed_kb:.2f} KB/s")
        else:
            await message.edit(f"✅ Uploaded in {elapsed:.2f} seconds.")
            del upload_start_times[key]
            del last_uploaded_percent[key]
    except:
        pass

async def update_processing_message(processing_message, start_time, stop_event):
    while not stop_event.is_set():
        elapsed_time = time.time() - start_time
        try:
            await processing_message.edit(
                f"📦 APK file received. Processing, please wait...\nTime elapsed: {elapsed_time:.2f} seconds"
            )
            await asyncio.sleep(15)
        except:
            break

app = Client("vmprotect-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("ping") & filters.private)
async def ping(client, message: Message):
    start_time = time.time()
    await message.reply("🏓 Pong!")
    ping_speed = (time.time() - start_time) * 1000
    await message.reply(f"🕒 Ping speed: {ping_speed:.2f} ms")

@app.on_message(filters.command("getrules") & filters.private)
async def get_rules(client, message: Message):
    if os.path.exists(RULES_FILE):
        await message.reply_document(RULES_FILE, caption="📄 Here is the current convertRules.txt file.")
    else:
        await message.reply("❌ convertRules.txt does not exist on the server.")

@app.on_message(filters.document & filters.private)
async def handle_file(client, message: Message):
    if message.from_user.id != OWNER_USER_ID:
        await message.reply("❌ You are not authorized to use this bot.")
        return

    file_name = message.document.file_name
    file_path = f"./{file_name}"

    download_msg = await message.reply("Downloading the file, please wait...")
    start_time = time.time()
    await message.download(file_path, progress=progress, progress_args=(download_msg, start_time))

    if file_name == "convertRules.txt":
        os.rename(file_path, RULES_FILE)
        await download_msg.edit("✅ convertRules.txt has been saved to server.")
        return

    if not os.path.exists(RULES_FILE):
        await download_msg.edit("❌ convertRules.txt not uploaded yet. Please send it first.")
        os.remove(file_path)
        return

    processing_message = await message.reply("📦 APK file received. Processing, please wait...")
    processing_start_time = time.time()
    stop_event = asyncio.Event()
    asyncio.create_task(update_processing_message(processing_message, processing_start_time, stop_event))

    cmd = ["java", "-jar", JAR_PATH, "apk", file_path, RULES_FILE, MAPPING_FILE]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()
    stop_event.set()
    await processing_message.edit("✅ APK Processing done!")

    if proc.returncode != 0:
        await message.reply(f"❌ Protection failed:\n{stderr.decode().strip()}")
    else:
        output_files = [
            os.path.join(BUILD_OUTPUT_DIR, f)
            for f in os.listdir(BUILD_OUTPUT_DIR)
            if f.endswith(".apk") or f.startswith("protected_")
        ]

        for out_file in output_files:
            new_file_name = f"{os.path.splitext(file_name)[0]}-ModderSU.COM.apk"
            new_file_path = os.path.join(BUILD_OUTPUT_DIR, new_file_name)
            os.rename(out_file, new_file_path)

            upload_msg = await message.reply("Uploading the file back to you, please wait...")
            await message.reply_document(
                new_file_path,
                caption="✅ APK uploaded successfully.",
                progress=upload_progress,
                progress_args=(upload_msg,)
            )
            os.remove(new_file_path)

    if os.path.exists(file_path):
        os.remove(file_path)

    try:
        for f in os.listdir(BUILD_OUTPUT_DIR):
            full_path = os.path.join(BUILD_OUTPUT_DIR, f)
            if os.path.isfile(full_path):
                os.remove(full_path)
        cleanup_message = await message.reply("✅ Output directory cleaned.")
        await asyncio.sleep(5)
        await cleanup_message.delete()
    except Exception as e:
        await message.reply(f"⚠️ Error cleaning output directory: {str(e)}")

if __name__ == "__main__":
    app.run()
