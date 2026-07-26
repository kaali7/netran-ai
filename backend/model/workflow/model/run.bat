@echo off
title Netran AI - Unified Workflow Orchestrator
cd /d %~dp0
set PYTHONPATH=..\..\..\..\backend
python front.py
pause
