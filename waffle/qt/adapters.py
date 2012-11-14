"""
Adapt parsed Construct values to more useful Python values.
"""
import time
from collections import namedtuple
from datetime import date, datetime, timedelta

from construct import Container



class _WrappedValue(object):
    def __init__(self, value):
        self._value = value


    def __hash__(self):
        return hash(self._value)


    def __cmp__(self, other):
        if isinstance(other, _WrappedValue):
            return cmp(self._value, other._value)
        else:
            return NotImplemented


    @property
    def value(self):
        return self._value


    def serialize(self):
        return self._value



class QVariant(_WrappedValue):
    @classmethod
    def parse(cls, container):
        realType = types[container.type]
        # XXX: What is this for if we can receive QVariants with this flag set
        # to True but still contain data?
        #if container.isNull:
        #    return None
        return realType.parse(container.data)


    def serialize(self):
        return Container(
            isNull=self.value is None,
            type=self.value.typeName,
            data=self.value.serialize())



class QMap(_WrappedValue):
    @classmethod
    def of(cls, keyType, valueType):
        def _parse(container):
            #assert len(container.items) == container.size
            result = {}
            for item in container.items:
                key = keyType.parse(item.key)
                value = valueType.parse(item.value)
                result[key] = value
            return result
        return _parse


    def serialize(self):
        items = [
            Container(
                key=key.serialize(),
                value=value.serialize())
            for key, value in self.value.iteritems()]
        return Container(items=items, size=len(items))



class QList(_WrappedValue):
    @classmethod
    def of(cls, valueType):
        def _parse(container):
            #assert len(container.items) == container.size
            return [valueType.parse(item) for item in container]
        return _parse


    def serialize(self):
        items = [value.serialize() for value in self.value]
        return items



class QString(_WrappedValue):
    typeName = 'QString'

    @classmethod
    def parse(cls, s):
        return s



class QChar(_WrappedValue):
    typeName = 'QChar'

    @classmethod
    def parse(cls, s):
        return unichr(s)



class UShort(_WrappedValue):
    typeName = 'UShort'

    @classmethod
    def parse(cls, v):
        return v



class Int(_WrappedValue):
    typeName = 'Int'

    @classmethod
    def parse(cls, v):
        return v



class UInt(_WrappedValue):
    typeName = 'UInt'

    @classmethod
    def parse(cls, v):
        return v



class Bool(_WrappedValue):
    typeName = 'Bool'

    @classmethod
    def parse(cls, v):
        return v



class QVariantMap(QMap):
    typeName = 'QVariantMap'

    def __init__(self, value):
        super(QVariantMap, self).__init__(
            dict(
                (QString(key), QVariant(value))
                for key, value in value.iteritems()))


    @classmethod
    def parse(cls, container):
        return QMap.of(QString, QVariant)(container)



class QVariantList(QList):
    typeName = 'QVariantList'

    def __init__(self, value):
        super(QVariantList, self).__init__(
            [QVariant(v) for v in value])


    @classmethod
    def parse(cls, container):
        return QList.of(QVariant)(container)



class QStringList(QList):
    typeName = 'QStringList'

    def __init__(self, value):
        super(QStringList, self).__init__(
            [QString(v) for v in value])


    @classmethod
    def parse(cls, container):
        return QList.of(QString)(container)



class QByteArray(_WrappedValue):
    typeName = 'QByteArray'

    @classmethod
    def parse(cls, value):
        return value



class QTime(_WrappedValue):
    typeName = 'QTime'

    @classmethod
    def parse(cls, value):
        return (datetime.min + timedelta(0, 0, 0, value)).time()


    def serialize(self):
        v = self._value
        return (
            (v.hour * 60 * 60) +
            (v.minute * 60) +
            v.second) * 1000 + v.microsecond / 1000




# Ported from qdatetime.cpp.
def getDateFromJulianDay(julianDay):
    if julianDay >= 2299161:
        # Gregorian calendar starting from October 15, 1582
        # This algorithm is from Henry F. Fliegel and Thomas C. Van Flandern
        ell = julianDay + 68569
        n = (4 * ell) / 146097
        ell = ell - (146097 * n + 3) / 4
        i = (4000 * (ell + 1)) / 1461001
        ell = ell - (1461 * i) / 4 + 31
        j = (80 * ell) / 2447
        d = ell - (2447 * j) / 80
        ell = j / 11
        m = j + 2 - (12 * ell)
        y = 100 * (n - 49) + i + ell
    else:
        # Julian calendar until October 4, 1582
        # Algorithm from Frequently Asked Questions about Calendars by Claus Toendering
        julianDay += 32082
        dd = (4 * julianDay + 3) / 1461
        ee = julianDay - (1461 * dd) / 4
        mm = ((5 * ee) + 2) / 153
        d = ee - (153 * mm + 2) / 5 + 1
        m = mm + 3 - 12 * (mm / 10)
        y = dd - 4800 + (mm / 10)
        if y <= 0:
            y = y - 1

    if y < 0:
        return None
    return y, m, d



class QDate(_WrappedValue):
    typeName = 'QDate'

    @classmethod
    def parse(cls, value):
        info = getDateFromJulianDay(value)
        if info is None:
            return None
        return date(*info)



class QDateTime(_WrappedValue):
    _QDateTime = namedtuple(
        '_QDateTime', ['date', 'time', 'isUTC'])


    def __init__(self, value):
        self._value = value


    def __repr__(self):
        fields = (
            '%s=%r' % (key, getattr(self._value, key))
            for key in self._value._fields)
        return '<%s %s>' % (type(self).__name__, ' '.join(fields))


    @classmethod
    def parse(cls, value):
        #value = cls._QDateTime(
        #    time=QTime.parse(value['time']),
        #    date=QDate.parse(value['date']),
        #    isUTC=Bool.parse(value['isUTC']))
        #return cls(value)
        t = QTime.parse(value['time'])
        d = QDate.parse(value['date'])
        # XXX: what the hell does this mean?
        if d is None:
            d = datetime.now().date()
        return time.mktime(
            # XXX: utctimetuple?
            datetime.combine(d, t).timetuple()) * 1000



    def serialize(self):
        raise NotImplementedError()



class BufferInfo(_WrappedValue):
    _fields = [
        'id', 'networkId', 'type', 'groupId', 'name']


    @classmethod
    def parse(cls, value):
        return dict((key, value[key]) for key in cls._fields)


    def serialize(self):
        return Container(**self._value)


class FlagsContainer(_WrappedValue):
    @classmethod
    def parse(self, value):
        value = dict(value)
        value.pop('__recursion_lock__', None)
        return value



class MessageInfo(_WrappedValue):
    _fields = [
        'id', 'timestamp', 'type', 'flags', 'bufferInfo', 'sender', 'content']


    @classmethod
    def parse(cls, value):
        result = dict((key, value[key]) for key in cls._fields)
        result['bufferInfo'] = BufferInfo.parse(result['bufferInfo'])
        result['flags'] = FlagsContainer.parse(result['flags'])
        return result


    def serialize(self):
        raise NotImplementedError()



# XXX: These should probably not be defined here.
userTypes = {
    'NetworkId': Int,
    'Identity': QVariantMap,
    'IdentityId': Int,
    'BufferInfo': BufferInfo,
    'BufferId': Int,
    'Message': MessageInfo,
    'MsgId': Int,
    'Network::Server': QVariantMap,
}



class UserType(_WrappedValue):
    typeName = 'UserType'


    def __init__(self, type, value):
        super(UserType, self).__init__(value)
        self.type = type


    @classmethod
    def parse(cls, v):
        valueType = userTypes[v.type]
        return valueType.parse(v.data)


    def serialize(self):
        return Container(
            type=self.type,
            data=userTypes[self.type].serialize(self._value))



types = {
    'QVariantMap': QVariantMap,
    'QVariantList': QVariantList,
    'QStringList': QStringList,
    'QByteArray': QByteArray,
    'Bool': Bool,
    'Int': Int,
    'UInt': UInt,
    'QChar': QChar,
    'QString': QString,
    'QTime': QTime,
    'QDate': QDate,
    'QDateTime': QDateTime,
    'UserType': UserType,
    #'Long': Long,
    #'Short': Short,
    #'Char': Char,
    #'ULong': ULong,
    'UShort': UShort,
    #'UChar': UChar,
    #'Float': Float,
}
