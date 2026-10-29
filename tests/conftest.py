"""O pytest não envia trace, mesmo que o terminal tenha as chaves."""

import os

os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
os.environ.pop("LANGFUSE_SECRET_KEY", None)
