import logging

from datetime import datetime

from telethon import TelegramClient
from telethon.tl.types import PeerChannel,UpdateNewChannelMessage

log = logging.getLogger("tmessage.*")
log.setLevel(False)

api_id = 104445
api_hash = 'eef836d8dd021c12e9cc15f6ed15b5a7'
phone = '+31620118076'
client = TelegramClient(session=phone, api_id=api_id, api_hash=api_hash, update_workers=1, spawn_read_thread=False)


def push_2_mail_db(update):
    if isinstance(update, UpdateNewChannelMessage):
        ch_id = update.message.to_id.channel_id
        ch = client.get_entity(PeerChannel(ch_id))
        log.warning("%s ::: %s --------Channel Message (%s)---------" % (datetime.now(), ch_id, ch.title))
        oper = {'1141512431': [1375066736], '1108566031': [1192038456]}
        TARGET_CHANNELS = [1141512431, 1108566031]
        FORWARD_TO = [1375066736]
        if ch_id not in TARGET_CHANNELS:
            log.warning("-------Ignore Channel (%s) Message ", ch_id)
            return

        for fo in oper[str(ch_id)]:
            client.send_message(entity=client.get_entity(PeerChannel(fo)), message=update.message.message)

try:
    is_con = client.connect()
except Exception as err:
    # TODO: send mail Notification about socekt timeout
    log.warning(err)

log.warning("Connected --------- %s " %is_con)
if is_con:
    is_auth = client.is_user_authorized()
    log.warning("Authorised --------- %s " %is_auth)
if is_auth:
    log.warning("*****Starting Client........ %s :::::  %s " % (phone, datetime.now()))
    client.add_update_handler(push_2_mail_db)
    client.idle()
    client.disconnect()
else:
    client.send_code_request(phone[1:])
    code = input('Enter the auth code: ')
    me = client.sign_in(code=code)
