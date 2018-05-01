import logging
import sqlite3
from time import sleep
from datetime import timedelta, datetime

from telethon.errors import ChatIdInvalidError, ChatAdminRequiredError, ChannelPrivateError
from telethon.tl.functions.channels import InviteToChannelRequest, GetParticipantsRequest, EditBannedRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import PeerUser, PeerChannel, InputPeerEmpty, ChannelParticipantsSearch, InputChannel, InputPeerChat, InputPeerChannel, InputPeerUser, Channel, ChannelBannedRights

log = logging.getLogger("tmessage.*")
log.setLevel(False)


q = ['`','~','!','@','#','$','%','^','&','*','(',')','-','_','+','=','[','{','}',']','|',':',';','"',',','<','.','>','/','?','0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']



DEFAULT_CHANNEL=1375066736


def addUser(client, username, channel_id=DEFAULT_CHANNEL):
    try:
        user = client.invoke(ResolveUsernameRequest(username))
        return add_user_by_id(client, user_id=user.users[0].id, channel_id=channel_id)
    except Exception as err:
        msg = "Add User @{} attempt to channel ({}) failed. Confirm the username is valid".format(username, channel_id)
        print(msg)
        print(err)
        return msg


def add_user_by_id(client, user_id, channel_id=DEFAULT_CHANNEL):
    try:
        user_entity = client.get_input_entity(PeerUser(user_id))
        channel_entity = client.get_entity(PeerChannel(channel_id=int(channel_id)))
        client.invoke(InviteToChannelRequest(channel_entity, [user_entity]))
        print("Added User: {} to Channel: {}".format(user_id, channel_id))
        return "User added successfully"
    except Exception as err:
        reason = err.args[1] if len(err.args) > 1 else err.message
        msg = "Add User {} attempt to channel ({}) failed [{}]".format(user_id, channel_id, reason)
        print(msg)
        print(err)
    return msg


def removeUser(client, username, channel_id=DEFAULT_CHANNEL):
    try:
        msg = removeUser_by_user(client, user=client(ResolveUsernameRequest(username)).users[0], channel_id=channel_id)
    except Exception as err:
        msg = "Attempt to kicked user @{}  from channel ({}) failed. Confirm the username is valid".format(username, channel_id)
        print(msg)
        print(err)
    return msg


def removeUser_by_user(client, user, channel_id=DEFAULT_CHANNEL):
    msg = ""
    try:
        until = datetime(2040, 12, 25)
        rights = ChannelBannedRights(until, view_messages=True, send_messages=True, send_media=True, send_stickers=True, send_gifs=True, send_games=True, send_inline=True, embed_links=True)

        channel_entity = client.get_input_entity(PeerChannel(channel_id=int(channel_id)))
        client(EditBannedRequest(channel_entity, client.get_input_entity(PeerUser(user_id=user.id)), banned_rights=rights))
        msg = 'Kicked User: {} from Channel ({})'.format(user.first_name, channel_id)
        log.warning(msg)
    except Exception as err:
        reason = err.args[1] if len(err.args) > 1 else err.message
        msg = "Attempt to kick User: {} from Channle ({}) failed [{}]".format(user.first_name, channel_id, reason)
        print(msg)
        print(err)
    return msg


def sendMsg(client, msg, channel_id=DEFAULT_CHANNEL):
    channel_entity = client.get_entity(PeerChannel(channel_id=int(channel_id)))
    client.send_message(entity=channel_entity, message=msg, reply_to=None, parse_mode=None, link_preview=True)


class DatabaseSQLite:
    def __init__(self, name=None):
        self.conn = None
        self.cursor = None
        if name:
            self.open(name)

    def open(self, name):
        try:
            self.conn = sqlite3.connect(name);
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print("Error connecting to database!")
            print(e)

    def close(self):
        if self.conn:
            self.conn.commit()
            self.cursor.close()
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        self.close()

    def get(self, table, columns, limit=None):
        query = "SELECT {0} from {1};".format(columns, table)
        self.cursor.execute(query)

        # fetch data
        rows = self.cursor.fetchall()
        return rows[len(rows) - limit if limit else 0:]

    def getLast(self, table, columns):
        return self.get(table, columns, limit=1)[0]

    def createEntityTable(self):
        sql = 'CREATE TABLE if not exists "entity" ("id" INTEGER NOT NULL, "access_hash" TEXT NOT NULL, "title" TEXT, "phone" TEXT, "first_name" TEXT, "last_name" TEXT, "username" TEXT, "type" TEXT, "last_seen" TEXT, "last_update" TEXT NOT NULL, PRIMARY KEY("id"));'
        c = self.cursor.execute(sql)
        self.conn.commit()

    def exists(self, table, column, value):
        query = "SELECT `{}` from `{}` WHERE `{}` = '{}';".format(column, table, column, value)
        return len(self.cursor.execute(query).fetchall()) > 0

    @staticmethod
    def toCSV(data, fname="output.csv"):
        with open(fname, 'a') as file:
            file.write(",".join([str(j) for i in data for j in i]))

    def write(self, table, columns, data):
        self.cursor.execute("INSERT INTO {0} ({1}) VALUES ({2});".format(table, columns, data))

    def write_sql(self, sql, params):
        try:
            self.cursor.execute(sql, params)
            self.conn.commit()
        except sqlite3.IntegrityError as err:
            sql = "UPDATE entity SET access_hash=?, first_name=?, last_name=?, username=?, `type`=?, last_seen=?, last_update=? WHERE id=?"
            id = params[0]
            params = list(params)
            del params[0]
            params.append(id)
            self.cursor.execute(sql, params)
            self.conn.commit()


    def query(self, sql):
        return self.cursor.execute(sql).fetchall()


def addUser(client, username, channel_id):
    try:
        user = client.invoke(ResolveUsernameRequest(username))
        return add_user_by_id(client, user_id=user.users[0].id, channel_id=channel_id)
    except Exception as err:
        msg = "Add User @{} attempt to channel ({}) failed. Confirm the username is valid".format(username, channel_id)
        print(msg)
        print(err)
        return msg


def add_user_by_id(client, user_id, channel_id):
    try:
        user_entity = client.get_input_entity(PeerUser(user_id))
        channel_entity = client.get_entity(PeerChannel(channel_id=int(channel_id)))
        client.invoke(InviteToChannelRequest(channel_entity, [user_entity]))

        log.warning("Added User: {} to Channel: {}".format(user_id, channel_id))
        return "User added successfully"
    except Exception as err:
        reason = err.args[1] if len(err.args) > 1 else err.message
        msg = "Add User {} attempt to channel ({}) failed [{}]".format(user_id, channel_id, reason)
        print(msg)
        print(err)
    return msg


class Member():
    id = None
    username = None
    phone = None
    access_hash = None
    first_name = None
    last_name = None
    title = None
    type = None
    last_seen = None
    last_update = datetime.now()
    def __init__(self, dictionary=None, type="User", *args, **kwargs):
        if dictionary:
            self.__dict__.update(dictionary)
            try:
                self.last_seen = dictionary['status'].was_online
            except AttributeError as err:
                try:
                    self.last_seen = dictionary['status'].expires
                except AttributeError as err:
                    self.last_seen = None
            self.type = type
        else:
            super(Member, self).__init__(*args, **kwargs)
    def __hash__(self):
        return hash(self.id)
    def __eq__(self, other):
        return self.id == other.id
    def __ne__(self, other):
        return (not self.__eq__(other))
    def __str__(self):
        return "{}, {}".format(self.id, self.access_hash)


def all_dialog(client):
    dialogs = []
    users = []
    chats = []
    last_date = None
    chunk_size = 100
    block = 1
    while True:
        from telethon.tl.custom.dialog import Dialog
        # client.get_dialogs(limit=None)
        result = client(GetDialogsRequest(offset_date=last_date, offset_id=0, offset_peer=InputPeerEmpty(), limit=chunk_size))
        dialogs.extend(result.dialogs)
        users.extend(result.users)
        chats.extend(result.chats)
        print("Block: {},    Count: {},   Users: {},  Dialog: {},  Chat: {}".format(block, len(result.messages), len(result.users), len(result.dialogs), len(result.chats)))
        block += 1
        if not result.messages:
            break
        last_date = min(msg.date for msg in result.messages)
        sleep(2)
    return {"dialogs": dialogs, "users": users, "chats": chats}



def get_all_channel_members(client, channel):
    all_participants = []

    offset = 0
    limit = 100
    block = 1
    # channel = InputChannel(202303173, )
    # channel = InputChannel(1088416958, -1922815699197487658)
    while True:
        try:
            participants = client(GetParticipantsRequest(channel, ChannelParticipantsSearch(''), offset, limit, 0))
            print("Block: {},    Count: {},   All: {}, Offset: {}".format(block, len(participants.users), len(all_participants), offset))
            block += 1
            # participants = client(GetParticipantsRequest("channel username', ChannelParticipantsSearch(''), offset, limit, hash=0)) # will work with ≥0.16.2
            if not participants.users:
                break
            all_participants.extend(participants.users)
            offset += len(participants.users)
        except ChatAdminRequiredError as err:
            offset += 1
            print(err)
            print(channel.stringify())
            print("\n")
        sleep(1)

    if len(all_participants) >= 10000:  # if this is upto 10k, it is Most likely the group is more than 10k
        for x in q:
            offset = 0
            limit = 100
            block = 1
            # channel = InputChannel(202303173, )
            # channel = InputChannel(1088416958, -1922815699197487658)
            while True:
                try:
                    participants = client(GetParticipantsRequest(channel, ChannelParticipantsSearch(x), offset, limit, 0))
                    print("{}:  Block: {},    Count: {},   All: {}, Offset: {}".format(x, block, len(participants.users), len(all_participants), offset))
                    block += 1
                    # participants = client(GetParticipantsRequest("channel username', ChannelParticipantsSearch(''), offset, limit, hash=0)) # will work with ≥0.16.2
                    if not participants.users:
                        break
                    all_participants.extend(participants.users)
                    offset += len(participants.users)
                except ChatAdminRequiredError as err:
                    offset += 1
                    print(err)
                    print(channel.stringify())
                    print("\n")
                sleep(1)
    return all_participants


total_users = []
def run(client):
    dialog = all_dialog(client)
    total_users.extend(dialog['users'])
    print("****Started with {} users".format(len(dialog['users'])))
    for c in dialog['chats']:
        if isinstance(c, Channel) and c.megagroup:
            try:
                all_participants = get_all_channel_members(client=client, channel=c)
                print("Channel: {} has {} users".format(c.title, len(all_participants)))
                print("\n")
                total_users.extend(all_participants)
            except ChannelPrivateError as err:
                print("Unable to pull users from {} ({})\n{}".format(c.title, c.id, err))
    print("All: {}".format(len(total_users)))
    members = set()
    db = DatabaseSQLite("test.db")
    for u in total_users:
        members.add(Member(u.__dict__))
    for m in members:
        sql = 'INSERT INTO entity (id, access_hash, first_name, last_name, username, `type`, last_seen, last_update) VALUES (?, ?, ?, ?, ?, ?, ?, ?);'
        param = (m.id, m.access_hash, m.first_name, m.last_name, m.username, m.type, m.last_seen, m.last_update)
        db.write_sql(sql, param)




# all_participants = []
# # client.get_message_history(entity, limit = 20, offset_date = None, offset_id = 0, max_id = 0, min_id = 0, add_offset = 0)

def get_all(client, chat_id, access_hash):
    offset = 0
    limit = 100
    offset_date = None
    chat = InputPeerChat(chat_id)
    try:
        messages = client.get_message_history(chat, limit=limit)
    except ChatIdInvalidError as err:
        print(err)
        channel = InputPeerChannel(chat_id, access_hash)
        messages = client.get_message_history(channel, limit=limit)
    for msg in reversed(messages):
        # Format the message content
        if getattr(msg, 'media', None):
            content = '<{}> {}'.format(msg.media.__class__.__name__, getattr(msg.media, 'caption', '')) # The media may or may not have a caption
            print("{}  ::: {}".format(msg.from_id))
            print("\n")
        # elif hasattr(msg, 'message'):
        #     content = msg.message
        # elif hasattr(msg, 'action'):
        #     content = str(msg.action)
        # else:
        #     # Unknown message, simply print its class name
        #     content = msg.__class__.__name__
        # text = '[{}:{}] (ID={}) {}: type: {}'.format(msg.date.hour, msg.date.minute, msg.id, "no name", content)
        # print(text)


    all_messages = []
    date = None
    block = 1
    while True:
        print(block)
        block += 1
        messages = client.get_message_history(InputPeerChannel(1124199950, 2927488848944236242), limit=100, offset_date=date)
        date = messages[len(messages)-1].date
        all_messages.extend(messages)
        if len(messages) < 100:
            break
        print(date)
        sleep(1)


    get_all(client, int(chats[4].id), int(chats[4].access_hash))