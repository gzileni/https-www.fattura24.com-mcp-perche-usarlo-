"""Run synthetic OAuth + single-endpoint federation inside the runtime image.

No pytest, host Python, credentials or network required.
"""
from contextlib import ExitStack
import importlib.util
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, '/app')
spec = importlib.util.spec_from_file_location('official_demo', Path(__file__).with_name('test_official_gateway.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Patches:
    def __init__(self, stack):
        self.stack = stack
    def setenv(self, key, value):
        self.stack.enter_context(patch.dict('os.environ', {key: value}))
    def delenv(self, key, raising=False):
        import os
        if key in os.environ:
            self.stack.enter_context(patch.dict('os.environ', {k: v for k, v in os.environ.items() if k != key}, clear=True))
    def setattr(self, obj, key, value):
        self.stack.enter_context(patch.object(obj, key, value))


with tempfile.TemporaryDirectory() as path, ExitStack() as stack:
    module.test_oauth_and_wrapper_share_one_mcp_endpoint(Path(path), Patches(stack))
with tempfile.TemporaryDirectory() as path:
    module.test_disconnected_does_not_contact_provider(Path(path))
print('[OK] Chat OAuth tool + native URL request/link fallback + PKCE + report_bilancino on SAME /mcp; no real network')
