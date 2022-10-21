from asyncio import Future
import pytest

from jeepney.routing import Router
from jeepney.wrappers import new_method_return, new_error, DBusErrorResponse
from jeepney.bus_messages import message_bus

def test_message_reply():
    router = Router(Future)
    call = message_bus.Hello()
    future = router.outgoing(call)
    router.incoming(new_method_return(call, 's', ('test',)))
    assert future.result() == ('test',)

def test_error():
    router = Router(Future)
    call = message_bus.Hello()
    future = router.outgoing(call)
    router.incoming(new_error(call, 'TestError', 'u', (31,)))
    with pytest.raises(DBusErrorResponse) as e:
        future.result()
    assert e.value.name == 'TestError'
    assert e.value.data == (31,)

def test_unhandled():
    unhandled = []
    router = Router(Future, on_unhandled=unhandled.append)
    msg = message_bus.Hello()
    router.incoming(msg)
    assert len(unhandled) == 1
    assert unhandled[0] == msg

