# flake8: noqa

r"""
Backport of uuid7 from Python 3.14 - we highly recommend using Python 3.14 if
using uuid7. This is here as a convenience for testing.
"""

import os
import time
from enum import Enum

__author__ = "Ka-Ping Yee <ping@zesty.ca>"


RESERVED_NCS, RFC_4122, RESERVED_MICROSOFT, RESERVED_FUTURE = [
    "reserved for NCS compatibility",
    "specified in RFC 4122",
    "reserved for Microsoft compatibility",
    "reserved for future definition",
]

int_ = int  # The built-in int type
bytes_ = bytes  # The built-in bytes type


class SafeUUID(Enum):
    safe = 0
    unsafe = -1
    unknown = None


_UINT_128_MAX = (1 << 128) - 1
# 128-bit mask to clear the variant and version bits of a UUID integral value
_RFC_4122_CLEARFLAGS_MASK = ~((0xF000 << 64) | (0xC000 << 48))
# RFC 4122 variant bits and version bits to activate on a UUID integral value.
_RFC_4122_VERSION_7_FLAGS = (7 << 76) | (0x8000 << 48)


class UUID:
    """Instances of the UUID class represent UUIDs as specified in RFC 4122.
    UUID objects are immutable, hashable, and usable as dictionary keys.
    Converting a UUID to a string with str() yields something in the form
    '12345678-1234-1234-1234-123456789abc'.  The UUID constructor accepts
    five possible forms: a similar string of hexadecimal digits, or a tuple
    of six integer fields (with 32-bit, 16-bit, 16-bit, 8-bit, 8-bit, and
    48-bit values respectively) as an argument named 'fields', or a string
    of 16 bytes (with all the integer fields in big-endian order) as an
    argument named 'bytes', or a string of 16 bytes (with the first three
    fields in little-endian order) as an argument named 'bytes_le', or a
    single 128-bit integer as an argument named 'int'.

    UUIDs have these read-only attributes:

        bytes       the UUID as a 16-byte string (containing the six
                    integer fields in big-endian byte order)

        bytes_le    the UUID as a 16-byte string (with time_low, time_mid,
                    and time_hi_version in little-endian byte order)

        fields      a tuple of the six integer fields of the UUID,
                    which are also available as six individual attributes
                    and two derived attributes. Those attributes are not
                    always relevant to all UUID versions:

                        The 'time_*' attributes are only relevant to version 1.

                        The 'clock_seq*' and 'node' attributes are only relevant
                        to versions 1 and 6.

                        The 'time' attribute is only relevant to versions 1, 6
                        and 7.

            time_low                the first 32 bits of the UUID
            time_mid                the next 16 bits of the UUID
            time_hi_version         the next 16 bits of the UUID
            clock_seq_hi_variant    the next 8 bits of the UUID
            clock_seq_low           the next 8 bits of the UUID
            node                    the last 48 bits of the UUID

            time                    the 60-bit timestamp for UUIDv1/v6,
                                    or the 48-bit timestamp for UUIDv7
            clock_seq               the 14-bit sequence number

        hex         the UUID as a 32-character hexadecimal string

        int         the UUID as a 128-bit integer

        urn         the UUID as a URN as specified in RFC 4122/9562

        variant     the UUID variant (one of the constants RESERVED_NCS,
                    RFC_4122, RESERVED_MICROSOFT, or RESERVED_FUTURE)

        version     the UUID version number (1 through 8, meaningful only
                    when the variant is RFC_4122)

        is_safe     An enum indicating whether the UUID has been generated in
                    a way that is safe for multiprocessing applications, via
                    uuid_generate_time_safe(3).
    """

    __slots__ = ("int", "is_safe", "__weakref__")

    def __init__(
        self,
        hex=None,
        bytes=None,
        bytes_le=None,
        fields=None,
        int=None,
        version=None,
        *,
        is_safe=SafeUUID.unknown,
    ):
        r"""Create a UUID from either a string of 32 hexadecimal digits,
        a string of 16 bytes as the 'bytes' argument, a string of 16 bytes
        in little-endian order as the 'bytes_le' argument, a tuple of six
        integers (32-bit time_low, 16-bit time_mid, 16-bit time_hi_version,
        8-bit clock_seq_hi_variant, 8-bit clock_seq_low, 48-bit node) as
        the 'fields' argument, or a single 128-bit integer as the 'int'
        argument.  When a string of hex digits is given, curly braces,
        hyphens, and a URN prefix are all optional.  For example, these
        expressions all yield the same UUID:

        UUID('{12345678-1234-5678-1234-567812345678}')
        UUID('12345678123456781234567812345678')
        UUID('urn:uuid:12345678-1234-5678-1234-567812345678')
        UUID(bytes='\x12\x34\x56\x78'*4)
        UUID(bytes_le='\x78\x56\x34\x12\x34\x12\x78\x56' +
                      '\x12\x34\x56\x78\x12\x34\x56\x78')
        UUID(fields=(0x12345678, 0x1234, 0x5678, 0x12, 0x34, 0x567812345678))
        UUID(int=0x12345678123456781234567812345678)

        Exactly one of 'hex', 'bytes', 'bytes_le', 'fields', or 'int' must
        be given.  The 'version' argument is optional; if given, the resulting
        UUID will have its variant and version set according to RFC 4122,
        overriding the given 'hex', 'bytes', 'bytes_le', 'fields', or 'int'.

        is_safe is an enum exposed as an attribute on the instance.  It
        indicates whether the UUID has been generated in a way that is safe
        for multiprocessing applications, via uuid_generate_time_safe(3).
        """

        if [hex, bytes, bytes_le, fields, int].count(None) != 4:
            raise TypeError(
                "one of the hex, bytes, bytes_le, fields, "
                "or int arguments must be given"
            )
        if int is not None:
            pass
        elif hex is not None:
            hex = hex.replace("urn:", "").replace("uuid:", "")
            hex = hex.strip("{}").replace("-", "")
            if len(hex) != 32:
                raise ValueError("badly formed hexadecimal UUID string")
            int = int_(hex, 16)
        elif bytes_le is not None:
            if len(bytes_le) != 16:
                raise ValueError("bytes_le is not a 16-char string")
            assert isinstance(bytes_le, bytes_), repr(bytes_le)
            bytes = (
                bytes_le[4 - 1 :: -1]
                + bytes_le[6 - 1 : 4 - 1 : -1]
                + bytes_le[8 - 1 : 6 - 1 : -1]
                + bytes_le[8:]
            )
            int = int_.from_bytes(bytes)  # big endian
        elif bytes is not None:
            if len(bytes) != 16:
                raise ValueError("bytes is not a 16-char string")
            assert isinstance(bytes, bytes_), repr(bytes)
            int = int_.from_bytes(bytes)  # big endian
        elif fields is not None:
            if len(fields) != 6:
                raise ValueError("fields is not a 6-tuple")
            (
                time_low,
                time_mid,
                time_hi_version,
                clock_seq_hi_variant,
                clock_seq_low,
                node,
            ) = fields
            if not 0 <= time_low < (1 << 32):
                raise ValueError("field 1 out of range (need a 32-bit value)")
            if not 0 <= time_mid < (1 << 16):
                raise ValueError("field 2 out of range (need a 16-bit value)")
            if not 0 <= time_hi_version < (1 << 16):
                raise ValueError("field 3 out of range (need a 16-bit value)")
            if not 0 <= clock_seq_hi_variant < (1 << 8):
                raise ValueError("field 4 out of range (need an 8-bit value)")
            if not 0 <= clock_seq_low < (1 << 8):
                raise ValueError("field 5 out of range (need an 8-bit value)")
            if not 0 <= node < (1 << 48):
                raise ValueError("field 6 out of range (need a 48-bit value)")
            clock_seq = (clock_seq_hi_variant << 8) | clock_seq_low
            int = (
                (time_low << 96)
                | (time_mid << 80)
                | (time_hi_version << 64)
                | (clock_seq << 48)
                | node
            )
        if not 0 <= int <= _UINT_128_MAX:
            raise ValueError("int is out of range (need a 128-bit value)")
        if version is not None:
            if not 1 <= version <= 8:
                raise ValueError("illegal version number")
            # clear the variant and the version number bits
            int &= _RFC_4122_CLEARFLAGS_MASK
            # Set the variant to RFC 4122/9562.
            int |= 0x8000_0000_0000_0000  # (0x8000 << 48)
            # Set the version number.
            int |= version << 76
        object.__setattr__(self, "int", int)
        object.__setattr__(self, "is_safe", is_safe)

    @classmethod
    def _from_int(cls, value):
        """Create a UUID from an integer *value*. Internal use only."""
        assert 0 <= value <= _UINT_128_MAX, repr(value)
        self = object.__new__(cls)
        object.__setattr__(self, "int", value)
        object.__setattr__(self, "is_safe", SafeUUID.unknown)
        return self

    def __getstate__(self):
        d = {"int": self.int}
        if self.is_safe != SafeUUID.unknown:
            # is_safe is a SafeUUID instance.  Return just its value, so that
            # it can be un-pickled in older Python versions without SafeUUID.
            d["is_safe"] = self.is_safe.value
        return d

    def __setstate__(self, state):
        object.__setattr__(self, "int", state["int"])
        # is_safe was added in 3.7; it is also omitted when it is "unknown"
        object.__setattr__(
            self,
            "is_safe",
            (
                SafeUUID(state["is_safe"])
                if "is_safe" in state
                else SafeUUID.unknown
            ),
        )

    def __eq__(self, other):
        if isinstance(other, UUID):
            return self.int == other.int
        return NotImplemented

    # Q. What's the value of being able to sort UUIDs?
    # A. Use them as keys in a B-Tree or similar mapping.

    def __lt__(self, other):
        if isinstance(other, UUID):
            return self.int < other.int
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, UUID):
            return self.int > other.int
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, UUID):
            return self.int <= other.int
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, UUID):
            return self.int >= other.int
        return NotImplemented

    def __hash__(self):
        return hash(self.int)

    def __int__(self):
        return self.int

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, str(self))

    def __setattr__(self, name, value):
        raise TypeError("UUID objects are immutable")

    def __str__(self):
        x = self.hex
        return f"{x[:8]}-{x[8:12]}-{x[12:16]}-{x[16:20]}-{x[20:]}"

    @property
    def bytes(self):
        return self.int.to_bytes(16, byteorder="big")  # big endian

    @property
    def bytes_le(self):
        bytes = self.bytes
        return (
            bytes[4 - 1 :: -1]
            + bytes[6 - 1 : 4 - 1 : -1]
            + bytes[8 - 1 : 6 - 1 : -1]
            + bytes[8:]
        )

    @property
    def fields(self):
        return (
            self.time_low,
            self.time_mid,
            self.time_hi_version,
            self.clock_seq_hi_variant,
            self.clock_seq_low,
            self.node,
        )

    @property
    def time_low(self):
        return self.int >> 96

    @property
    def time_mid(self):
        return (self.int >> 80) & 0xFFFF

    @property
    def time_hi_version(self):
        return (self.int >> 64) & 0xFFFF

    @property
    def clock_seq_hi_variant(self):
        return (self.int >> 56) & 0xFF

    @property
    def clock_seq_low(self):
        return (self.int >> 48) & 0xFF

    @property
    def time(self):
        if self.version == 6:
            # time_hi (32) | time_mid (16) | ver (4) | time_lo (12) | ... (64)
            time_hi = self.int >> 96
            time_lo = (self.int >> 64) & 0x0FFF
            return time_hi << 28 | (self.time_mid << 12) | time_lo
        elif self.version == 7:
            # unix_ts_ms (48) | ... (80)
            return self.int >> 80
        else:
            # time_lo (32) | time_mid (16) | ver (4) | time_hi (12) | ... (64)
            #
            # For compatibility purposes, we do not warn or raise when the
            # version is not 1 (timestamp is irrelevant to other versions).
            time_hi = (self.int >> 64) & 0x0FFF
            time_lo = self.int >> 96
            return time_hi << 48 | (self.time_mid << 32) | time_lo

    @property
    def clock_seq(self):
        return ((self.clock_seq_hi_variant & 0x3F) << 8) | self.clock_seq_low

    @property
    def node(self):
        return self.int & 0xFFFFFFFFFFFF

    @property
    def hex(self):
        return self.bytes.hex()

    @property
    def urn(self):
        return "urn:uuid:" + str(self)

    @property
    def variant(self):
        if not self.int & (0x8000 << 48):
            return RESERVED_NCS
        elif not self.int & (0x4000 << 48):
            return RFC_4122
        elif not self.int & (0x2000 << 48):
            return RESERVED_MICROSOFT
        else:
            return RESERVED_FUTURE

    @property
    def version(self):
        # The version bits are only meaningful for RFC 4122/9562 UUIDs.
        if self.variant == RFC_4122:
            return int((self.int >> 76) & 0xF)


_last_timestamp_v7 = None
_last_counter_v7 = 0  # 42-bit counter


def _uuid7_get_counter_and_tail():
    rand = int.from_bytes(os.urandom(10), byteorder="big")
    # 42-bit counter with MSB set to 0
    counter = (rand >> 32) & 0x1FF_FFFF_FFFF
    # 32-bit random data
    tail = rand & 0xFFFF_FFFF
    return counter, tail


def uuid7():
    """Generate a UUID from a Unix timestamp in milliseconds and random bits.

    UUIDv7 objects feature monotonicity within a millisecond.
    """
    # --- 48 ---   -- 4 --   --- 12 ---   -- 2 --   --- 30 ---   - 32 -
    # unix_ts_ms | version | counter_hi | variant | counter_lo | random
    #
    # 'counter = counter_hi | counter_lo' is a 42-bit counter constructed
    # with Method 1 of RFC 9562, §6.2, and its MSB is set to 0.
    #
    # 'random' is a 32-bit random value regenerated for every new UUID.
    #
    # If multiple UUIDs are generated within the same millisecond, the LSB
    # of 'counter' is incremented by 1. When overflowing, the timestamp is
    # advanced and the counter is reset to a random 42-bit integer with MSB
    # set to 0.

    global _last_timestamp_v7
    global _last_counter_v7

    nanoseconds = time.time_ns()
    timestamp_ms = nanoseconds // 1_000_000

    if _last_timestamp_v7 is None or timestamp_ms > _last_timestamp_v7:
        counter, tail = _uuid7_get_counter_and_tail()
    else:
        if timestamp_ms < _last_timestamp_v7:
            timestamp_ms = _last_timestamp_v7 + 1
        # advance the 42-bit counter
        counter = _last_counter_v7 + 1
        if counter > 0x3FF_FFFF_FFFF:
            # advance the 48-bit timestamp
            timestamp_ms += 1
            counter, tail = _uuid7_get_counter_and_tail()
        else:
            # 32-bit random data
            tail = int.from_bytes(os.urandom(4))

    unix_ts_ms = timestamp_ms & 0xFFFF_FFFF_FFFF
    counter_msbs = counter >> 30
    # keep 12 counter's MSBs and clear variant bits
    counter_hi = counter_msbs & 0x0FFF
    # keep 30 counter's LSBs and clear version bits
    counter_lo = counter & 0x3FFF_FFFF
    # ensure that the tail is always a 32-bit integer (by construction,
    # it is already the case, but future interfaces may allow the user
    # to specify the random tail)
    tail &= 0xFFFF_FFFF

    int_uuid_7 = unix_ts_ms << 80
    int_uuid_7 |= counter_hi << 64
    int_uuid_7 |= counter_lo << 32
    int_uuid_7 |= tail
    # by construction, the variant and version bits are already cleared
    int_uuid_7 |= _RFC_4122_VERSION_7_FLAGS
    res = UUID._from_int(int_uuid_7)

    # defer global update until all computations are done
    _last_timestamp_v7 = timestamp_ms
    _last_counter_v7 = counter
    return res
