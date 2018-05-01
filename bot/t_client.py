import json
import logging

import re

from datetime import timedelta, datetime

import MySQLdb
import requests
import unicodedata
from requests import ReadTimeout
from telethon import TelegramClient
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import UpdateShortMessage,UpdateShortChatMessage, PeerUser, PeerChat, PeerChannel, UpdateUserStatus, UpdateUserTyping, UpdateNewChannelMessage, MessageActionChatDeleteUser, ChannelBannedRights
from unidecode import unidecode


log = logging.getLogger("tmessage.*")
log.setLevel(False)

PRIMARY_PHONE = True

if PRIMARY_PHONE:
    api_id = 187136
    api_hash = 'aa09410fbbccf046acf7ef14fb60efb6'
    phone = '+00212661422956'
else:
    api_id = 158307
    api_hash = 'bd3bddc4898d26147545d81260672725'
    phone = '+00212661235950'

client = TelegramClient(session=phone, api_id=api_id, api_hash=api_hash, update_workers=1, spawn_read_thread=False)
# client.get_message_history()

def get_seconds(n, time):
    n = int(n)
    if time in ['sec', 'secs']:
        return n
    elif time in ['min', 'mins']:
        return n * 60
    elif time in ['hour', 'hours']:
        return n * 60 * 60
    elif time in ['day', 'days']:
        return n * 24 * 60 * 60


def deEmojify(inputString):
    returnString = ""
    for character in inputString:
        try:
            character.encode("ascii")
            returnString += character
        except UnicodeEncodeError:
            replaced = unidecode(str(character))
            if replaced != '':
                returnString += replaced
            else:
                try:
                     returnString += "[" + unicodedata.name(character) + "]"
                except ValueError:
                     returnString += "[x]"
    return returnString


# def create_connection(db_file="tbot_message.db"):
    # conn = None
    # try:
    #     conn = sqlite3.connect(os.path.abspath(db_file))
    # except Error as e:
    #     log.warning(e)
    # return conn


class Database:

    def __init__(self, local=True):
        if local:
            self.host = '127.0.0.1'
            self.user = 'root'
            self.password = 'pw2014'
            self.db = 'tmessage_db'
            self.connection = MySQLdb.connect(self.host, self.user, self.password, self.db)
        else:
            self.host = '217.23.8.58'
            self.user = 'cryptomo_u2017'
            self.password = 'pw2017@@'
            self.db = 'cryptomo_db2017'
            self.connection = MySQLdb.connect(self.host, self.user, self.password, self.db)
        self.cursor = self.connection.cursor()


    def update(self, query):
        counter = 0
        try:
            counter = self.cursor.execute(query)
            self.connection.commit()
        except Exception as err:
            log.error("Database Update Error.... %s " %query)
            log.error(err)
            self.connection.rollback()
        return counter

    def insert(self, query):
        # log.warning(query)
        try:
            self.cursor.execute(query)
            self.connection.commit()
            return self.cursor.lastrowid
        except Exception as err:
            log.error("Database Insert Error.... %s " %query)
            log.error(err)
            self.connection.rollback()

    def query(self, query):
        cursor = self.connection.cursor(MySQLdb.cursors.DictCursor )
        cursor.execute(query)

        return cursor.fetchall()

    def __del__(self):
        try:
            self.connection.close()
        except AttributeError as err:
            log.warning(err)


ALLOWED_CHANNELS = []

# def replier(update):
#     client(GetBotCallbackAnswerRequest(
#    update.message.to_id,
#    update.message.id,
#    data=update.message.reply_markup.rows[0].buttons[0].data
# ))


# [('#kingcryptosignal [[TOP WITH UPWARDS ARROW ABOVE]9] (+722%) \nWin/Loses/Open: 42/21/4\nWinRate: 66% Average signal ~8hours 42min\n\n[LARGE BLUE CIRCLE] #KMD [LARGE BLUE CIRCLE]\nSell 0.00070000 6.06% \nBuy  0.00066000\nNow  0.00066361 0.55% (@ Bittrex)\nStop 0.00059400 10.00%', '#kingcryptosignal', '\n', '', '[LARGE BLUE CIRCLE]', '#KMD', '[LARGE BLUE CIRCLE]', 'Sell 0.00070000 6.06%', 'Buy  0.00066000', 'Now  0.00066361 0.55%', '(@ Bittrex)', 'Stop 0.00059400 10.00%', '')]
def analyse(channel_id, message, client_id):
    TARGET_REGEX = r"((\[(?:\w+\s+){1,6}\w+\])\s*?(#\w+)\s*?(\[\[(?:\w+\s+){1,6}\w+\]\d+\])\s*?(#\w+)\s*?(\[(?:\w+\s+){1,6}\w+\])\s*?(#?\w+)?\s*?((?:\w+\s+){1,2})\s*?([-|'+'\d.]+%)\s*?(in)\s*?(~)((\d+(?:months|month|days|day|hours|hour|mins|min|secs|sec)\s*){1,6}))"
    # SELL_REGEX_ = r"((\[(?:\w+\s+){1,6}\w+\])\s*?(#\w+)\s*?(\[(?:\w+\s+){1,6}\w+\])\s*?((?:\w+\s+[-|'+'\d.]+\s*?[-|'+'\d.]+%))\s*?((?:\w+\s+[-|'+'\d.]+\s*?))\s*?((?:\w+\s+[-|'+'\d.]+\s*?[-|'+'\d.]+%))\s*?(\(@\s*?\w+\))\s*?((?:\w+\s+[-|'+'\d.]+\s*?[-|'+'\d.]+%))\s*?((?:\w+\s+){1,6}\w+\:\s*?[-|'+'\d.]+))"
    SELL_REGEX = r"((#\w+)\s*((.*)\s)*?(\[(?:\w+\s+){1,6}\w+\])\s*?(#\w+)\s*?(\[(?:\w+\s+){1,6}\w+\])\s*?(#\w+)?\s*?((?:\w+\s+[-|'+'\d.]+\s*?[-|'+'\d.]+%))\s*?((?:\w+\s+[-|'+'\d.]+\s*?))\s*?((?:\w+\s+[-|'+'\d.]+\s*?[-|'+'\d.]+%))\s*?(\(@\s*?\w+\))\s*?((?:\w+\s+[-|'+'\d.]+\s*?[-|'+'\d.]+%))\s*?((?:\w+\s+){1,6}\w+\:\s*?[-|'+'\d.]+)?)"
    # log.warning(message)
    m = re.findall(SELL_REGEX, message)
    # log.warning(message)
    # log.warn(m)
        
    if m is None or len(m) == 0:
        log.warning("****** SELL_REGEX Failed (COIN)  ******")
        m = re.findall(TARGET_REGEX, message)
        if m is not None and len(m) > 0:
            log.warning("****** TARGET_REGEX Successful (RESULT)******")
            m = m[0]
            seconds = 0
            # log.warning(m)
            times = re.findall(r"(\d+(?:days|day|hours|hour|mins|min|secs|sec))", m[11])
            for t in times:
                xx = re.findall(r"(\d+)((?:days|day|hours|hour|mins|min|secs|sec))", t)
                seconds += int(get_seconds(xx[0][0], xx[0][1]))
            sql = "insert into bot_result ( `client_id`,  `channel_id`, `source`, `coin_name`, `type`, `percent`, `time`, `entry`) values "
            sql += "( '{}', '{}', '{}', '{}', '{}', {}, {}, '{}');".format(client_id, channel_id, m[2][1:], m[4][1:], m[7], m[8][:-1], seconds, datetime.now())

            db = Database()
            id = db.insert(sql)

            sql = "insert into bot_result (id,  `client_id`,  `channel_id`, `source`, `coin_name`, `type`, `percent`, `time`, `entry`) values "
            sql += "({}, '{}', '{}', '{}', '{}', '{}', {}, {}, '{}');".format(id, client_id, channel_id, m[2][1:], m[4][1:], m[7], m[8][:-1], seconds, datetime.now())

            db = Database(local=False)
            db.insert(sql)
        else:
            log.warning("****** TARGET_REGEX Failed (RESULT) ******")
    else:
        log.warning("****** SELL_REGEX Successful  (COIN) ******")
        m = m[0]
        three_regrex = r"(\w+)\s*?([-|'+'\d.]+)\s*?([\d.]+)"
        two_regrex = r"(\w+)\s*?([-|'+'\d.]+)"
        sell = re.findall(three_regrex, m[8])[0]
        buy = re.findall(two_regrex, m[9])[0]
        now = re.findall(three_regrex, m[10])[0]
        stop = re.findall(three_regrex, m[12])[0]
        reward = re.findall("((?:\w+\s+){1,6}\w+\:)\s*?([-|'+'\d.]+)", m[13])
        log.warning(m)
        if len(reward) > 1:
            reward = reward[1]
        else:
            reward = 0

        early = datetime.now() - timedelta(minutes=5)

        sql = "SELECT * FROM bot_coin WHERE name='{}' and entry > '{}'".format(m[5][1:], early)

        db = Database()
        coins = db.query(sql)

        if len(coins) > 0:
            log.warning("***********Prevented Duplicate**********")
            return

        # client = Client.objects.get(pk=client_id)
        # coin = Coin.objects.create(client=client, channel=channel, source=m[1][1:], name=m[5][1:], sell_value=sell[1], sell_percent=sell[2], buy_value=buy[1], now_value=now[1], now_percent=now[2], stop_value=stop[1], stop_percent=stop[2], reward=reward)
        attempts = 1

        sql = "insert into bot_coin ( client_id, channel_id, source, `name`, sell_value, sell_percent, buy_value, buy_percent, now_value, now_percent, stop_value, stop_percent, reward, entry, done) values "
        sql += "({}, {}, '{}', '{}', {}, {}, {}, {}, {}, {}, {}, {}, {}, '{}', '{}');".format(client_id, channel_id, m[1][1:], m[5][1:], sell[1], sell[2], buy[1], 0, now[1], now[2], stop[1], stop[2], reward, datetime.now(), 'Not Treated')

        id = db.insert(sql)
        # db.__del__()

        sql = "insert into bot_coin (id, client_id, channel_id, source, `name`, sell_value, sell_percent, buy_value, buy_percent, now_value, now_percent, stop_value, stop_percent, reward, entry, done) values "
        sql += "({}, {}, {}, '{}', '{}', {}, {}, {}, {}, {}, {}, {}, {}, {}, '{}', '{}');".format(id, client_id, channel_id, m[1][1:], m[5][1:], sell[1], sell[2], buy[1], 0, now[1], now[2], stop[1], stop[2], reward, datetime.now(), 'Not Treated')

        db_remote = Database(local=False)
        db_remote.insert(sql)

        payload = json.dumps({"buy_value": str(buy[1]), "stop_value": str(stop[1]), "sell_value": str(sell[1]), "name": m[5][1:], "source": m[1][1:]})
        url = "http://127.0.0.1:8083/trade/" + payload
        log.warning(url)

        # db = Database()
        db_remote = Database(local=False)
        while attempts < 4:
            response = "failed"
            try:
                response = requests.get(url, timeout=10)
                log.warning(response)
                if response.json()['success'] == True:
                    response = "ok"
                elif response.json()['success'] == False:
                    log.error(response.json()['description'])
            except (ConnectionError, ReadTimeout) as e:
                log.error(e)

            if response == "ok":
                sql = "UPDATE bot_coin SET done = 'Treated' WHERE id = '{}'".format(id)
                db.update(sql)
                db_remote.update(sql)

                return
            else:
                attempts += 1

        if attempts > 3:
            sql = "UPDATE bot_coin SET done = 'Failed Attempt' WHERE id = '{}'".format(id)
            db.update(sql)
            db_remote.update(sql)


def push_2_mail_db(update):
    if isinstance(update, UpdateNewChannelMessage):
        ch_id = update.message.to_id.channel_id
        ch = client.get_entity(PeerChannel(ch_id))
        log.warning("%s ::: %s --------Channel Message (%s)---------" % (datetime.now(), ch_id, ch.title))
        TARGET_CHANNELS = [1228129346, 1131704561, 1350457716]
        FORWARD_TO = []
        # TARGET_CHANNELS = [1141512431]
        # FORWARD_TO = [1375066736]
        ANALYSE = True
        if ch_id not in TARGET_CHANNELS:
            log.warning("-------Ignore Channel (%s) Message ", ch_id)
            return

        for fo in FORWARD_TO:
            client.send_message(entity=client.get_entity(PeerChannel(fo)), message=update.message.message)

        if ANALYSE:
            analyse(channel_id=ch_id, message=deEmojify(update.message.message), client_id=api_id)

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
# else:
    # client.send_code_request(phone[1:])
    # code = input('Enter the auth code: ')
    # me = client.sign_in(code=code)


#
# EMAILS = "email-1@email.com, email-2@email.com";
# ZIP_CODE = "12345"
# URL = "https://partnership.grubhub.com/equity-residential/"
#
# email_list = EMAILS.split(",")
# import requests
# from time import sleep
# for email in email_list:
#     print("Posting {}".format(email.strip()))
#     response = requests.post(URL, data={"Email": email.strip(), "ZipCode": ZIP_CODE})
#     print(response.status_code)
#     sleep(2)
