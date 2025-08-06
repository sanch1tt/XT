# Ultroid ~ UserBot
# Copyright (C) 2023 Ultroid
#
# This file is a part of < https://github.com/ufoptg/UltroidBackup/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/ufoptg/UltroidBackup/blob/main/LICENSE/>.

from . import get_help

__doc__ = get_help("help_tools")

import asyncio
import glob
import io
import os
import re

import pyshorteners

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None
try:
    from htmlwebshot import WebShot
except ImportError:
    WebShot = None

from bs4 import BeautifulSoup
from requests import get
from telethon.errors.rpcerrorlist import MessageTooLongError, YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest as unblock
from telethon.tl import types
from telethon.tl.types import (
    ChannelParticipantAdmin,
    ChannelParticipantsBots,
    DocumentAttributeVideo,
)

from xteam.fns.tools import metadata, translate

from . import *
from . import HNDLR, LOGS, ULTConfig, bash, con, eor, get_string
from . import humanbytes as hb
from . import inline_mention, mediainfo, ultroid_cmd


def sanga_seperator(sanga_list):
    string = "".join(info[info.find("\n") + 1 :] for info in sanga_list)
    string = re.sub(r"^$\n", "", string, flags=re.MULTILINE)
    name, username = string.split("Usernames**")
    name = name.split("Names")[1]
    return name, username


def mentionuser(name, userid):
    return f"[{name}](tg://user?id={userid})"


@ultroid_cmd(pattern="tl( (.*)|$)", manager=True)
async def _(event):
    input_ = event.pattern_match.group(1).strip().split(maxsplit=1)
    txt = input_[1] if len(input_) > 1 else None
    if input_:
        input_ = input_[0]
    if txt:
        text = txt
    elif event.is_reply:
        previous_message = await event.get_reply_message()
        text = previous_message.message
    else:
        return await eor(
            event, f"`{HNDLR}tr LanguageCode` as reply to a message", time=5
        )
    lan = input_ or "en"
    try:
        tt = await translate(text, lang_tgt=lan)
        output_str = f"**Translate**\n\n**Source**:\n`{text}`\n\n**Translation** (`{lan}`):\n`{tt}`"
        await event.eor(output_str)
    except Exception as exc:
        LOGS.exception(exc)
        await event.eor(str(exc), time=5)


@ultroid_cmd(pattern="tr( (.*)|$)", manager=True)
async def _(event):
    input_ = event.pattern_match.group(1).strip().split(maxsplit=1)
    txt = input_[1] if len(input_) > 1 else None
    if input_:
        input_ = input_[0]
    if txt:
        text = txt
    elif event.is_reply:
        previous_message = await event.get_reply_message()

        if previous_message.media and hasattr(previous_message.media, 'poll'):
            poll = previous_message.media.poll
            question_text = poll.question.text
            answers_text = "\n".join([f"- {answer.text.text}" for answer in poll.answers])
            text = f"Poll Question:\n{question_text}\n\nPoll Answers:\n{answers_text}"
        else:
            text = previous_message.message
    else:
        return await eor(
            event, f"`{HNDLR}tl LanguageCode` as reply to a message", time=5
        )

    lan = input_ or "en"
    try:
        tt = await previous_message.translate(lan)
        output_str = f"**Translate**\n\n**Source**:\n`{text}`\n\n**Translation** (`{lan}`):\n`{tt}`"
        await event.eor(output_str)
    except Exception as exc:
        LOGS.exception(exc)
        await event.eor(str(exc), time=5)


@ultroid_cmd(
    pattern="idn( (.*)|$)",
    manager=True,
)
async def _(event):
    ult = event
    if match := event.pattern_match.group(1).strip():
        try:
            ids = await event.client.parse_id(match)
        except Exception as er:
            return await event.eor(str(er))
        return await event.eor(
            f"**Chat ID:**  `{event.chat_id}`\n**User ID:**  `{ids}`"
        )
    data = f"**Current Chat ID:**  `{event.chat_id}`"
    if event.reply_to_msg_id:
        event = await event.get_reply_message()
        data += f"\n**From User ID:**  `{event.sender_id}`"
    if event.media:
        bot_api_file_id = event.file.id
        data += f"\n**Bot API File ID:**  `{bot_api_file_id}`"
    data += f"\n**Msg ID:**  `{event.id}`"
    await ult.eor(data)


@ultroid_cmd(pattern="botsub( (.*)|$)", groups_only=True, manager=True)
async def _(ult):
    mentions = "• **Bots in this Chat**: \n"
    if input_str := ult.pattern_match.group(1).strip():
        mentions = f"• **Bots in **{input_str}: \n"
        try:
            chat = await ult.client.parse_id(input_str)
        except Exception as e:
            return await ult.eor(str(e))
    else:
        chat = ult.chat_id
    try:
        async for x in ult.client.iter_participants(
            chat,
            filter=ChannelParticipantsBots,
        ):
            if isinstance(x.participant, ChannelParticipantAdmin):
                mentions += f"\n⚜️ {inline_mention(x)} `{x.id}`"
            else:
                mentions += f"\n• {inline_mention(x)} `{x.id}`"
    except Exception as e:
        mentions += f" {str(e)}" + "\n"
    await ult.eor(mentions)


@ultroid_cmd(
    pattern="hil( (.*)|$)",
)
async def _(ult):
    input_ = ult.pattern_match.group(1).strip()
    if not input_:
        return await ult.eor("`Input some link`", time=5)
    text = None
    if len(input_.split()) > 1:
        spli_ = input_.split()
        input_ = spli_[0]
        text = spli_[1]
    if not text:
        text = "ㅤㅤㅤㅤㅤㅤㅤ"
    await ult.eor(f"[{text}]({input_})", link_preview=False)


@ultroid_cmd(
    pattern="circles$",
)
async def _(e):
    reply = await e.get_reply_message()
    if not (reply and reply.media):
        return await e.eor("`Reply to a gif or audio file only.`")
    if "audio" in mediainfo(reply.media):
        msg = await e.eor("`Downloading...`")
        try:
            bbbb = await reply.download_media(thumb=-1)
        except TypeError:
            bbbb = ULTConfig.thumb
        im = cv2.imread(bbbb)
        dsize = (512, 512)
        output = cv2.resize(im, dsize, interpolation=cv2.INTER_AREA)
        cv2.imwrite("img.jpg", output)
        thumb = "img.jpg"
        audio, _ = await e.client.fast_downloader(reply.document)
        await msg.edit("`Creating video note...`")
        await bash(
            f'ffmpeg -i "{thumb}" -i "{audio.name}" -preset ultrafast -c:a libmp3lame -ab 64 circle.mp4 -y'
        )
        await msg.edit("`Uploading...`")
        data = await metadata("circle.mp4")
        file, _ = await e.client.fast_uploader("circle.mp4", to_delete=True)
        await e.client.send_file(
            e.chat_id,
            file,
            thumb=thumb,
            reply_to=reply,
            attributes=[
                DocumentAttributeVideo(
                    duration=min(data["duration"], 60),
                    w=512,
                    h=512,
                    round_message=True,
                )
            ],
        )

        await msg.delete()
        [os.remove(k) for k in [audio.name, thumb]]
    elif mediainfo(reply.media) == "gif" or mediainfo(reply.media).startswith("video"):
        msg = await e.eor("**Creating video note**")
        file = await reply.download_media("resources/downloads/")
        if file.endswith(".webm"):
            nfile = await con.ffmpeg_convert(file, "file.mp4")
            os.remove(file)
            file = nfile
        if file:
            await e.client.send_file(
                e.chat_id,
                file,
                video_note=True,
                thumb=ULTConfig.thumb,
                reply_to=reply,
            )
            os.remove(file)
        await msg.delete()

    else:
        await e.eor("`Reply to a gif or audio file only.`")


FilesEMOJI = {
    "py": "🐍",
    "json": "🔮",
    ("sh", "bat"): "⌨️",
    (".mkv", ".mp4", ".avi", ".gif", "webm"): "🎥",
    (".mp3", ".ogg", ".m4a", ".opus"): "🔊",
    (".jpg", ".jpeg", ".png", ".webp", ".ico"): "🖼",
    (".txt", ".text", ".log"): "📄",
    (".apk", ".xapk"): "📲",
    (".pdf", ".epub"): "📗",
    (".zip", ".rar"): "🗜",
    (".exe", ".iso"): "⚙",
}


@ultroid_cmd(
    pattern="Ls( (.*)|$)",
)
async def _(e):
    files = e.pattern_match.group(1).strip()
    if not files:
        files = "*"
    elif files.endswith("/"):
        files += "*"
    elif "*" not in files:
        files += "/*"
    files = glob.glob(files)
    if not files:
        return await e.eor("`Directory Empty or Incorrect.`", time=5)
    allfiles = []
    folders = []
    for file in sorted(files):
        if os.path.isdir(file):
            folders.append(f"📂 {file}")
        else:
            for ext in FilesEMOJI.keys():
                if file.endswith(ext):
                    allfiles.append(f"{FilesEMOJI[ext]} {file}")
                    break
            else:
                if "." in str(file)[1:]:
                    allfiles.append(f"🏷 {file}")
                else:
                    allfiles.append(f"📒 {file}")
    omk = [*sorted(folders), *sorted(allfiles)]
    text = ""
    fls, fos = 0, 0
    flc, foc = 0, 0
    for i in omk:
        try:
            emoji = i.split()[0]
            name = i.split(maxsplit=1)[1]
            nam = name.split("/")[-1]
            if os.path.isdir(name):
                size = 0
                for path, dirs, files in os.walk(name):
                    for f in files:
                        fp = os.path.join(path, f)
                        size += os.path.getsize(fp)
                if hb(size):
                    text += f"{emoji} `{nam}`  `{hb(size)}" + "`\n"
                    fos += size
                else:
                    text += f"{emoji} `{nam}`" + "\n"
                foc += 1
            else:
                if hb(int(os.path.getsize(name))):
                    text += (
                        f"{emoji} `{nam}`  `{hb(int(os.path.getsize(name)))}" + "`\n"
                    )
                    fls += int(os.path.getsize(name))
                else:
                    text += f"{emoji} `{nam}`" + "\n"
                flc += 1
        except BaseException:
            pass
    tfos, tfls, ttol = hb(fos), hb(fls), hb(fos + fls)
    if not hb(fos):
        tfos = "0 B"
    if not hb(fls):
        tfls = "0 B"
    if not hb(fos + fls):
        ttol = "0 B"
    text += f"\n\n`Folders` :  `{foc}` :   `{tfos}`\n`Files` :       `{flc}` :   `{tfls}`\n`Total` :       `{flc+foc}` :   `{ttol}`"
    try:
        if (flc + foc) > 100:
            text = text.replace("`", "")
        await e.eor(text)
    except MessageTooLongError:
        with io.BytesIO(str.encode(text)) as out_file:
            out_file.name = "output.txt"
            await e.reply(f"`{e.text}`", file=out_file, thumb=ULTConfig.thumb)
        await e.delete()


@ultroid_cmd(
    pattern="sgm(|u)(?:\\s|$)([\\s\\S]*)",
    fullsudo=True,
)
async def sangmata(event):
    "To get name/username history."
    cmd = event.pattern_match.group(1)
    user = event.pattern_match.group(2)
    reply = await event.get_reply_message()
    loading = await event.eor("`Processing...`")

    if not user and reply:
        user = str(reply.sender_id)
    if not user:
        return await loading.eor(
            "`Reply to a user's message or provide their ID/username to fetch name/username history.`",
            time=10,
        )

    try:
        if user.isdigit():
            userinfo = await ultroid_bot.get_entity(int(user))
        else:
            userinfo = await ultroid_bot.get_entity(user)
    except ValueError:
        userinfo = None

    if not isinstance(userinfo, types.User):
        return await loading.eor("`Unable to fetch user details.`", time=10)

    async with event.client.conversation("@SangMata_beta_bot") as conv:
        try:
            await conv.send_message(f"{userinfo.id}")
        except YouBlockedUserError:
            await catub(unblock("SangMata_beta_bot"))
            await conv.send_message(f"{userinfo.id}")
        
        responses = []
        while True:
            try:
                response = await conv.get_response(timeout=2)
            except asyncio.TimeoutError:
                break
            responses.append(response.text)
        await event.client.send_read_acknowledge(conv.chat_id)

    if not responses:
        return await loading.eor("`No response from the bot. Please try again later.`", time=10)

    if any("No data available" in r for r in responses):
        return await loading.eor(
            f"**No data available ({userinfo.id})**\n\n**Tips:**\n1. Add this bot to your groups as admin to increase detection.\n"
            "2. Use search by username. Simply copy a username and send `allhistory @username`.\n"
            "New data will be added if not available.",
            time=15,
        )

    if any("quota" in r.lower() for r in responses):
        return await loading.eor(
            "**Quota Exceeded**\n\n"
            "Sorry, you have used up your quota for today. Quota refreshes daily at 00:00 UTC.\n\n"
            "**To increase your daily quota:**\n"
            "- Open private chat with @SangMata_BOT or @SangMata_beta_bot.\n"
            '- Send "donate <amount>" to the bot (e.g., "donate 500").\n\n'
            "Need help? Join the support group at @sang_inc.",
            time=20,
        )
    try:
        names, usernames = sanga_seperator(responses)
    except ValueError as er:
        return await loading.eor(f"`Error processing data: {er}`", time=10)

    check = (usernames, "Username") if cmd == "u" else (names, "Name")
    user_name = (
        f"{userinfo.first_name} {userinfo.last_name}"
        if userinfo.last_name
        else userinfo.first_name
    )
    output = (
        f"**➜ User Info:** {mentionuser(user_name, userinfo.id)}\n"
        f"**➜ {check[1]} History:**\n{check[0]}"
    )
    await loading.eor(output)

@ultroid_cmd(pattern="webst( (.*)|$)")
async def webss(event):
    xx = await event.eor(get_string("com_1"))
    xurl = event.pattern_match.group(1).strip()
    if xurl:
        x = get(f"https://mini.s-shot.ru/1920x1080/JpE6/1024/7100/?{xurl}")
        y = "shot.jpg"
        with open(y, "wb") as f:
            f.write(x.content)
        if (await ultroid_bot.get_me()).premium:
            await ultroid_bot.send_file(
                event.chat_id,
                y,
                caption=f"[📷](emoji/5258205968025525531)**WebShot Generated**\n[🔗](emoji/5983262173474853675)**URL** : {xurl}",
                force_document=False,
            )
        else:
            await ultroid_bot.send_file(
                event.chat_id,
                y,
                caption=f"📷**WebShot Generated**\n🔗**URL** : {xurl}",
                force_document=False,
            )
        os.remove(y)
    else:
        await eod(xx, f"Please provide me a URL...", time=5)
    await xx.delete()


@ultroid_cmd(pattern="shrturl ?(.*)")
async def short_url(event):
    input_url = event.pattern_match.group(1)

    if not input_url:
        reply_msg = await event.get_reply_message()
        if reply_msg:
            input_url = reply_msg.text
        else:
            return await eor(event, "`Please provide a URL to shorten.`")

    try:
        s = pyshorteners.Shortener()
        if input_url.lower().startswith("https://tinyurl.com/"):
            response = get(input_url)
            soup = BeautifulSoup(response.text, "html.parser")
            original_url = soup.find("a", {"target": "_blank"}).get("href")
            output_message = (
                f"**Expanded URL**\n"
                f"**Given Link** ➠ **{input_url}**\n"
                f"**Expanded Link** ➠ **{original_url}**"
            )
        else:
            shortened_url = s.tinyurl.short(input_url)
            output_message = (
                f"**Shortened URL**\n"
                f"**Given Link** ➠ **{input_url}**\n"
                f"**Shortened Link** ➠ **{shortened_url}**"
            )

        if event.reply_to_msg_id:
            await event.delete()
            await event.reply(output_message)
        else:
            await eor(event, output_message)

    except Exception as e:
        await eor(event, f"An error occurred: {e}")
