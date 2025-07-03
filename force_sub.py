FSUB_CHANNEL = "PrimeXBots"  # <-- এখানেই আপনার চ্যানেল ইউজারনেম দিন (e.g., 'MyChannel')

async def is_subscribed(client, user_id):
    try:
        member = await client.get_chat_member(FSUB_CHANNEL, user_id)
        return member.status in ("member", "creator", "administrator")
    except:
        return False

async def get_channel_name(client):
    try:
        chat = await client.get_chat(FSUB_CHANNEL)
        return chat.title
    except:
        return "our channel"
