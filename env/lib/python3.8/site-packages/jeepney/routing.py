from warnings import warn

from .low_level import MessageType, HeaderFields
from .wrappers import DBusErrorResponse

class Router:
    """Routing for messages coming back to a client application.
    
    :param handle_factory: Constructor for an object like asyncio.Future,
        with methods *set_result* and *set_exception*. Outgoing method call
        messages will get a handle associated with them.
    :param on_unhandled: Callback for messages not otherwise dispatched.
    """
    def __init__(self, handle_factory, on_unhandled=None):
        self.handle_factory = handle_factory
        self._on_unhandled = on_unhandled
        self.outgoing_serial = 0
        self.awaiting_reply = {}
        self.signal_callbacks = {}

    @property
    def on_unhandled(self):
        return self._on_unhandled

    @on_unhandled.setter
    def on_unhandled(self, value):
        warn("Setting on_unhandled is deprecated. Please use the filter() "
             "method or simple receive() calls instead.", stacklevel=2)
        self._on_unhandled = value

    def outgoing(self, msg):
        """Set the serial number in the message & make a handle if a method call
        """
        self.outgoing_serial += 1
        msg.header.serial = self.outgoing_serial

        if msg.header.message_type is MessageType.method_call:
            self.awaiting_reply[msg.header.serial] = handle = self.handle_factory()
            return handle

    def subscribe_signal(self, callback, path, interface, member):
        """Add a callback for a signal.
        """
        warn("The subscribe_signal() method is deprecated. "
             "Please use the filter() API instead.", stacklevel=2)
        self.signal_callbacks[(path, interface, member)] = callback

    def incoming(self, msg):
        """Route an incoming message.
        """
        hdr = msg.header

        # Signals:
        if hdr.message_type is MessageType.signal:
            key = (hdr.fields.get(HeaderFields.path, None),
                   hdr.fields.get(HeaderFields.interface, None),
                   hdr.fields.get(HeaderFields.member, None)
                  )
            cb = self.signal_callbacks.get(key, None)
            if cb is not None:
                cb(msg.body)
                return

        # Method returns & errors
        reply_serial = hdr.fields.get(HeaderFields.reply_serial, -1)
        reply_handle = self.awaiting_reply.pop(reply_serial, None)
        if reply_handle is not None:
            if hdr.message_type is MessageType.method_return:
                reply_handle.set_result(msg.body)
                return
            elif hdr.message_type is MessageType.error:
                reply_handle.set_exception(DBusErrorResponse(msg))
                return

        if self.on_unhandled:
            self.on_unhandled(msg)
