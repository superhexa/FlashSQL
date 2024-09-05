import msgpack
from typing import Any, Union

def encode_value(value: Any) -> bytes:
    return (b'\x01' + value) if isinstance(value, bytes) else (b'\x02' + msgpack.packb(value))

def decode_value(buffer: bytes) -> Union[Any, None]:
    return buffer[1:] if buffer[0:1] == b'\x01' else msgpack.unpackb(buffer[1:], raw=False) if buffer[0:1] == b'\x02' else None
