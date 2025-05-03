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

# Client Initialization
app = Client("vmprotect-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.document & filters.private)
async def handle_file(client, message: Message):
    """Handles the incoming message with a document file."""
    
    # Check if the message is from the owner
    if message.from_user.id != OWNER_USER_ID:
        await message.reply("❌ You are not authorized to use this bot.")
        return

    file_name = message.document.file_name
    file_path = f"./{file_name}"

    # Save the uploaded file
    await message.download(file_path)

    if file_name == "convertRules.txt":
        os.rename(file_path, RULES_FILE)
        await message.reply("✅ convertRules.txt has been saved to server.")
        return
    
    # Check if the rules file exists
    if not os.path.exists(RULES_FILE):
        await message.reply("❌ convertRules.txt not uploaded yet. Please send it first.")
        os.remove(file_path)
        return
    
    # Notify that the APK file has been received and is being processed
    processing_message = await message.reply("📦 APK file received. Processing, please wait...")

    # Execute the JAR command for APK protection
    cmd = [
        "java", "-jar", JAR_PATH,
        "apk", file_path,
        RULES_FILE,
        MAPPING_FILE
    ]
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        await message.reply(f"❌ Protection failed:\n{stderr.decode().strip()}")
    else:
        # Check for output files in the build output directory
        output_files = [
            os.path.join(BUILD_OUTPUT_DIR, f)
            for f in os.listdir(BUILD_OUTPUT_DIR)
            if f.endswith(".apk") or f.startswith("protected_")
        ]

        for out_file in output_files:
            # Rename the output file to `actual-filename-ModderSU.COM.apk`
            new_file_name = f"{os.path.splitext(file_name)[0]}-ModderSU.COM.apk"
            new_file_path = os.path.join(BUILD_OUTPUT_DIR, new_file_name)
            os.rename(out_file, new_file_path)

            await message.reply_document(new_file_path, caption="✅ APK uploaded successfully.")
            os.remove(new_file_path)  # Remove the renamed file after sending

    # Clean up input file
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete the processing message after sending results
    await processing_message.delete()

    # Clean up the build output directory contents
    try:
        for f in os.listdir(BUILD_OUTPUT_DIR):
            full_path = os.path.join(BUILD_OUTPUT_DIR, f)
            if os.path.isfile(full_path):
                os.remove(full_path)
        
        # Notify that the output directory has been cleaned
        cleanup_message = await message.reply("✅ Output directory cleaned.")

        # Wait for 5 seconds before deleting the cleanup message
        await asyncio.sleep(5)
        await cleanup_message.delete()

    except Exception as e:
        print(f"⚠️ Error cleaning build directory: {e}")
        await message.reply(f"⚠️ Error cleaning output directory: {str(e)}")

if __name__ == "__main__":
    app.run()
