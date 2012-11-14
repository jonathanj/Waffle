"""
Quassel Qt user type structures.
"""
from construct import (
    Struct, Rename, PascalString, Enum, FlagsEnum, UBInt8, UBInt32)

from waffle.qt.types import (
    registerUserType, Short, Int, UInt, ByteArray, Map, String, QVariant,
    QVariantMap)



BufferInfo = Struct(
    'BufferInfo',
    Rename('id', Int),
    Rename('networkId', Int),
    Enum(Rename('type', Short),
        invalid=0x00,
        status=0x01,
        channel=0x02,
        query=0x04,
        group=0x08),
    Rename('groupId', UInt),
    PascalString('name', length_field=UBInt32('length')))



MessageInfo = Struct(
    'MessageInfo',
    Rename('id', Int),
    Rename('timestamp', UInt),
    Enum(UBInt32('type'),
        plain=0x00001,
        notice=0x00002,
        action=0x00004,
        nick=0x00008,
        mode=0x00010,
        join=0x00020,
        part=0x00040,
        quit=0x00080,
        kick=0x00100,
        kill=0x00200,
        server=0x00400,
        info=0x00800,
        error=0x01000,
        daychange=0x02000,
        topic=0x04000,
        netsplitjoin=0x08000,
        netsplitquit=0x10000,
        invite=0x20000),
    FlagsEnum(UBInt8('flags'),
        empty=0x00,
        self=0x01,
        highlight=0x02,
        redirected=0x04,
        servermessage=0x08,
        backlog=0x80),
    Rename('bufferInfo', BufferInfo),
    Rename('sender', ByteArray),
    Rename('content', ByteArray))



registerUserType('NetworkId', Int)
registerUserType(
    'Identity', Map(Rename('key', String), Rename('value', QVariant)))
registerUserType('IdentityId', Int)
registerUserType('BufferInfo', BufferInfo)
registerUserType('BufferId', Int)
registerUserType('Message', MessageInfo)
registerUserType('MsgId', Int)
registerUserType('Network::Server', QVariantMap)
