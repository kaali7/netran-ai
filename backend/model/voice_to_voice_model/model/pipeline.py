"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: pipeline.py
Description: Master Stage 3 pipeline entry point re-exporting WorkflowVoiceEngine / Stage3Pipeline.
"""

try:
    from .voice_engine import WorkflowVoiceEngine
except ImportError:
    try:
        from model.voice_to_voice_model.model.voice_engine import WorkflowVoiceEngine
    except ImportError:
        try:
            from voice_engine import WorkflowVoiceEngine
        except ImportError:
            WorkflowVoiceEngine = None

Stage3Pipeline = WorkflowVoiceEngine
