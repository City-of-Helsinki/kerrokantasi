import base64
import mimetypes
from typing import IO


def file_to_base64(file: IO[bytes]) -> str:
    return f"data:{mimetypes.guess_type(file.name)[0]};base64,{base64.b64encode(file.read()).decode('ascii')}"  # noqa: E501
