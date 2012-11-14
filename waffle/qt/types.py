"""
Qt type structures.

@see: U{http://doc.qt.nokia.com/4.7/datastreamformat.html}
"""
from construct import (
    Struct, SBInt8, UBInt8, SBInt16, UBInt16, SBInt32, UBInt32, SBInt64,
    UBInt64, BFloat32, BFloat64, PascalString, Enum, Switch, Flag, Rename,
    PrefixedArray, Adapter, CStringAdapter)



class NullLengthAdapter(Adapter):
    """
    An adapter that turns a maximum value into 0.

    Some Qt types use a size of C{0xFFFFFFFF} to indicate the value is null, it
    is difficult to map these to None without rewriting all the underlying
    Construct types along the way.
    """
    def __init__(self, subcon):
        Adapter.__init__(self, subcon)
        self.MAX = 2 ** (subcon.length * 8) - 1


    def _encode(self, obj, context):
        return obj


    def _decode(self, obj, context):
        if obj == self.MAX:
            return 0
        return obj



def Map(keyType, valueType):
    """
    Map type.
    """
    itemType = Struct(
        'MapItem',
        keyType,
        valueType)

    return Struct(
        'Map',
        Rename('items', PrefixedArray(itemType, length_field=UBInt32('size'))))



def List(valueType):
    """
    List type.
    """
    return PrefixedArray(valueType, length_field=UBInt32('size'))



Bool = Flag('Bool')
Int = SBInt32('Int')
UInt = UBInt32('UInt')
LongLong = SBInt64('LongLong')
ULongLong = UBInt64('ULongLong')
Double = BFloat64('Double')
QChar = UBInt16('QChar')
String = PascalString(
    'String',
    length_field=NullLengthAdapter(UBInt32('length')),
    encoding='utf-16be')
StringList = List(Rename('items', String))
ByteArray = PascalString(
    'ByteArray', length_field=NullLengthAdapter(UBInt32('length')))
Date = UBInt32('Date')
Time = UBInt32('Time')
DateTime = Struct(
    'DateTime',
    Rename('date', Date),
    Rename('time', Time),
    Flag('isUTC'))
Long = SBInt32('Long')
Short = SBInt16('Short')
Char = SBInt8('Char')
ULong = UBInt32('ULong')
UShort = UBInt16('UShort')
UChar = UBInt8('UChar')
Float = BFloat32('Float')



def _UserTypeSwitchFunc(ctx):
    #print '*** Switching UserType on %r' % (ctx.type,)
    return ctx.type

_userTypeTypes = dict()

UserType = Struct(
    'UserType',
    CStringAdapter(
        PascalString('type', length_field=UBInt32('length'))),
    Switch(
        'data',
        _UserTypeSwitchFunc,
        _userTypeTypes))


def registerUserType(name, type):
    """
    Register a UserType.
    """
    _userTypeTypes[name] = type



QVariantTypeEnum = Enum(
    UBInt32('type'),
    Void=0,
    Bool=1,
    Int=2,
    UInt=3,
    LongLong=4,
    ULongLong=5,
    Double=6,
    QChar=7,
    QVariantMap=8,
    QVariantList=9,
    QString=10,
    QStringList=11,
    QByteArray=12,
    QBitArray=13,
    QDate=14,
    QTime=15,
    QDateTime=16,
    UserType=127,
    Long=129,
    Short=130,
    Char=131,
    ULong=132,
    UShort=133,
    UChar=134,
    Float=135,
    QVariant=138)

def _QVariantSwitchFunc(ctx):
    #print '*** Switching QVariant on %r' % (ctx.type,)
    return ctx.type

_QVariantTypes = dict(
    Bool=Bool,
    Int=Int,
    UInt=UInt,
    LongLong=LongLong,
    ULongLong=ULongLong,
    Double=Double,
    QChar=QChar,
    QString=String,
    QStringList=StringList,
    QByteArray=ByteArray,
    QDate=Date,
    QTime=Time,
    QDateTime=DateTime,
    UserType=UserType,
    Long=Long,
    Short=Short,
    Char=Char,
    ULong=ULong,
    UShort=UShort,
    UChar=UChar,
    Float=Float,
)

QVariant = Struct(
    'QVariant',
    QVariantTypeEnum,
    Flag('isNull'),
    Switch(
        'data',
        _QVariantSwitchFunc,
        _QVariantTypes))

QVariantMap = Map(Rename('key', String), Rename('value', QVariant))
_QVariantTypes['QVariantMap'] = QVariantMap
QVariantList = List(Rename('value', QVariant))
_QVariantTypes['QVariantList'] = QVariantList


# XXX: Side effects.
import waffle.qt.quassel; waffle


__all__ = [
    'Map', 'List', 'Bool', 'Short', 'Int', 'UInt', 'LongLong', 'ULongLong',
    'Double', 'Char', 'String', 'StringList', 'ByteArray', 'Date', 'Time',
    'DateTime', 'QVariant', 'UserType', 'Long', 'Short', 'Char', 'ULong',
    'UShort', 'UChar', 'Float', 'registerUserType']
