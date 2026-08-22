import base64
import mimetypes
from typing import IO


def file_to_base64(file: IO[bytes]) -> str:
    mime_type = mimetypes.guess_type(file.name)[0]
    encoded_file = base64.b64encode(file.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded_file}"
