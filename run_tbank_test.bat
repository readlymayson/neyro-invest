@echo off
chcp 65001 >nul
set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
python examples/tbank_sandbox_test.py
pause


