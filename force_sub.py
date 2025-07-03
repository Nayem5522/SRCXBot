from pyrogram.errors import UserNotParticipant, ChatAdminRequired, ChannelPrivate

# 🔁 Force Subscribe Channel (Set without @)
FSUB_CHANNEL = "PRIMECINEZONE"

async def is_subscribed(client, user_id):
    try:
        member = await client.get_chat_member(FSUB_CHANNEL, user_id)
        return member.status in ("member", "administrator", "creator")
    except UserNotParticipant:
        return False
    except ChatAdminRequired:
        print("❌ Bot is not an admin in the channel!")
        return False
    except ChannelPrivate:
        print("❌ Channel is private or bot is not in the channel.")
        return False
    except Exception as e:
        print(f"🔥 Subscription Check Error: {e}")
        return False

async def get_channel_name(client):
    try:
        chat = await client.get_chat(FSUB_CHANNEL)
        return chat.title or "our channel"
    except Exception as e:
        print(f"⚠️ Error fetching channel name: {e}")
        return "our channel"
