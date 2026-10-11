"""
Netran AI — Code Card Generator & Screenshot Automator
WHITE / LIGHT THEME — Serene Learning Design System (DESIGN.md)
Features pure white card surfaces, soft lavender borders, crisp syntax highlighting,
and full-width layout with the right pane removed.
"""

import os
import subprocess
import time
from pathlib import Path

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = Path(r"c:\kali\product\netran ai\doc\img_screenshort")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SNIPPETS = [
    {
        "id": "01_stage3_turn_manager",
        "title": "TurnManager — Level 2 State Machine & Echo Guard",
        "subtitle": "backend/model/voice_to_voice_model/model/turn_manager.py",
        "badge": "STAGE 3: VOICE LOOP",
        "code_lines": [
            ('class <span class="cls">ConversationState</span>(str, Enum):', False),
            ('    READY = <span class="str">"READY"</span>', False),
            ('    EVA_SPEAKING = <span class="str">"EVA_SPEAKING"</span>       <span class="cmt"># TTS streaming audio</span>', False),
            ('    PLAYBACK_ACTIVE = <span class="str">"PLAYBACK_ACTIVE"</span> <span class="cmt"># Browser playing audio</span>', False),
            ('    ECHO_GUARD = <span class="str">"ECHO_GUARD"</span>           <span class="cmt"># Post-playback window</span>', False),
            ('    LISTENING = <span class="str">"LISTENING"</span>             <span class="cmt"># VAD mic active</span>', False),
            ('    CANDIDATE_SPEAKING = <span class="str">"CANDIDATE_SPEAKING"</span>', False),
            ('', False),
            ('<span class="kwd">def</span> <span class="fn">on_playback_finished</span>(self, turn_id: <span class="typ">int</span>):', False),
            ('    <span class="kwd">with</span> self._lock:', False),
            ('        self.playback_finished_event.set()', False),
            ('        self.state = ConversationState.ECHO_GUARD', True),
            ('        self.turn_timestamps[turn_id][<span class="str">"finish"</span>] = time.monotonic()', False),
            ('', False),
            ('    <span class="kwd">def</span> <span class="fn">_clear_echo_guard</span>():', False),
            ('        time.sleep(self.echo_guard_sec)  <span class="cmt"># 150ms guard</span>', False),
            ('        <span class="kwd">with</span> self._lock:', False),
            ('            <span class="kwd">if</span> self.state == ConversationState.ECHO_GUARD:', False),
            ('                self.state = ConversationState.LISTENING', True),
            ('                self.listening_enabled_event.set()', False),
            ('    threading.Thread(target=_clear_echo_guard, daemon=<span class="kwd">True</span>).start()', False),
        ]
    },
    {
        "id": "02_stage3_silero_vad_filter",
        "title": "Audio DSP — Streaming IIR Filter & Silero VAD ONNX",
        "subtitle": "backend/model/voice_to_voice_model/model/listener.py",
        "badge": "STAGE 3: VAD & DSP",
        "code_lines": [
            ('<span class="cmt"># 1. Anti-aliased integer boxcar decimation (48kHz -> 16kHz)</span>', False),
            ('<span class="kwd">if</span> native_rate == 48000 <span class="kwd">and</span> RATE == 16000:', False),
            ('    original_frame = original_frame.reshape(-1, 3).mean(axis=1)', True),
            ('', False),
            ('<span class="cmt"># 2. Streaming IIR High-Pass DC Blocker (y[n] = α*(y[n-1] + x[n] - x[n-1]))</span>', False),
            ('<span class="cmt"># Prevents DC drift (+0.005) from saturating Silero RNN hidden state</span>', False),
            ('_dc_alpha = 0.995', False),
            ('<span class="kwd">for</span> _s <span class="kwd">in</span> range(len(vad_frame)):', False),
            ('    _in_val = float(vad_frame[_s])', False),
            ('    _dc_prev_out = _dc_alpha * (_dc_prev_out + _in_val - _dc_prev_in)', True),
            ('    _dc_prev_in = _in_val', False),
            ('    vad_frame[_s] = _dc_prev_out', False),
            ('', False),
            ('<span class="cmt"># 3. Silero VAD v3 Recurrent ONNX Inference</span>', False),
            ('audio_input = np.expand_dims(np.clip(vad_frame, -1.0, 1.0), axis=0)', False),
            ('ort_inputs = {<span class="str">"input"</span>: audio_input, <span class="str">"state"</span>: vad_state, <span class="str">"sr"</span>: 16000}', False),
            ('ort_outputs = vad_session.run(<span class="kwd">None</span>, ort_inputs)', False),
            ('out, vad_state = ort_outputs[0], ort_outputs[1]', True),
            ('speech_prob = out[0, 0]', False),
        ]
    },
    {
        "id": "03_stage3_brain_llm_stream",
        "title": "Brain — Ollama Qwen 2.5 Stream with Barge-In Guard",
        "subtitle": "backend/model/voice_to_voice_model/model/brain.py",
        "badge": "STAGE 3: LLM REASONING",
        "code_lines": [
            ('stream = ollama.chat(', False),
            ('    model=MODEL_NAME, messages=full_messages, stream=<span class="kwd">True</span>', False),
            (')', False),
            ('<span class="kwd">for</span> chunk <span class="kwd">in</span> stream:', False),
            ('    token = chunk.get(<span class="str">"message"</span>, {}).get(<span class="str">"content"</span>, <span class="str">""</span>)', False),
            ('    <span class="kwd">if</span> token:', False),
            ('        <span class="kwd">if not</span> first_token_received:', False),
            ('            ttft_ms = Benchmark.end(<span class="str">"ttft"</span>)', True),
            ('            first_token_received = <span class="kwd">True</span>', False),
            ('', False),
            ('        <span class="cmt"># Full-Duplex Barge-In: immediately abort on interrupt signal</span>', False),
            ('        <span class="kwd">if</span> session_state <span class="kwd">and</span> session_state.interrupt_event.is_set():', True),
            ('            logger.info(<span class="str">"⛔ Aborted LLM stream — candidate barge-in"</span>)', True),
            ('            <span class="kwd">break</span>', True),
            ('', False),
            ('        line_buffer += token', False),
            ('        <span class="kwd">if</span> <span class="str">"SPEAK:"</span> <span class="kwd">in</span> line_buffer.upper():', False),
            ('            tone = re.search(<span class="str">r"TONE:\s*(\w+)"</span>, line_buffer)', False),
            ('            session_state.tts_speed = get_speed_for_tone(tone.group(1))', False),
        ]
    },
    {
        "id": "04_stage3_speaker_flush",
        "title": "Speaker — Kokoro-82M Sub-Chunk Stream & Driver Flush",
        "subtitle": "backend/model/voice_to_voice_model/model/speaker.py",
        "badge": "STAGE 3: NEURAL TTS",
        "code_lines": [
            ('SUB_CHUNK_SAMPLES = 1024  <span class="cmt"># ~42ms check granularity</span>', False),
            ('', False),
            ('<span class="kwd">for</span> i <span class="kwd">in</span> range(0, len(chunk_bytes), step):', False),
            ('    <span class="kwd">if</span> self.interrupt_event.is_set() <span class="kwd">or not</span> self.is_running:', True),
            ('        <span class="kwd">break</span>', True),
            ('    sub = chunk_bytes[i:i + step]', False),
            ('    <span class="kwd">if</span> sub <span class="kwd">and</span> self.ws_audio_out_queue <span class="kwd">is not None</span>:', False),
            ('        float_arr = np.frombuffer(sub, dtype=np.float32)', False),
            ('        int16_arr = (float_arr * 32767.0).astype(np.int16)', False),
            ('        self.ws_audio_out_queue.put(int16_arr.tobytes())', True),
            ('', False),
            ('<span class="kwd">def</span> <span class="fn">stop_immediately</span>(self, state: SessionState):', False),
            ('    <span class="cmt">"""Full-duplex hardware audio driver buffer flush."""</span>', False),
            ('    self.interrupt_event.set()', True),
            ('    self._drain_queue()', False),
            ('    <span class="kwd">if</span> self.stream <span class="kwd">is not None</span>:', False),
            ('        self.stream.stop_stream()   <span class="cmt"># Hard-flush OS WASAPI</span>', True),
            ('        self.stream.start_stream()  <span class="cmt"># Reset driver state</span>', True),
        ]
    },
    {
        "id": "05_stage2_planner_analyst",
        "title": "Question Model — Dual Gemini & STT Conditioning",
        "subtitle": "backend/model/question_model/model/pipeline.py",
        "badge": "STAGE 2: QUESTION ENGINE",
        "code_lines": [
            ('<span class="cmt"># Parallel Execution: 15-Question Tree Planner & Resume Analyst</span>', False),
            ('<span class="kwd">with</span> ThreadPoolExecutor(max_workers=2) <span class="kwd">as</span> executor:', True),
            ('    future_planner = executor.submit(_call_planner)', True),
            ('    future_analyst = executor.submit(_call_analyst)', True),
            ('    planner_res = future_planner.result()', False),
            ('    analyst_res = future_analyst.result()', False),
            ('', False),
            ('<span class="cmt"># Whisper Domain Vocabulary Conditioning (Dynamic Prompt Injection)</span>', False),
            ('segments, _ = whisper_model.transcribe(', False),
            ('    audio_array,', False),
            ('    language=<span class="str">"en"</span>,', False),
            ('    initial_prompt=behavior[<span class="str">"whisper_domain_vocabulary"</span>],', True),
            ('    beam_size=1,            <span class="cmt"># Greedy decoding for lowest latency</span>', True),
            ('    temperature=0.0,', False),
            ('    condition_on_previous_text=<span class="kwd">False</span>,', False),
            ('    no_speech_threshold=0.6,', False),
            ('    hallucination_silence_threshold=0.5', False),
            (')', False),
        ]
    },
    {
        "id": "06_stage4_gemini_multimodal",
        "title": "Stage 4 — Multimodal Evaluation with Exponential Retry",
        "subtitle": "backend/model/reports_model/model/gemini_evaluator.py",
        "badge": "STAGE 4: MULTIMODAL REPORTS",
        "code_lines": [
            ('<span class="kwd">def</span> <span class="fn">_create_interaction_with_retry</span>(self, **kwargs):', False),
            ('    <span class="kwd">for</span> attempt <span class="kwd">in</span> range(1, 6):', False),
            ('        <span class="kwd">try</span>:', False),
            ('            <span class="kwd">return</span> self.client.interactions.create(**kwargs)', False),
            ('        <span class="kwd">except</span> Exception <span class="kwd">as</span> e:', False),
            ('            <span class="kwd">if</span> <span class="str">"429"</span> <span class="kwd">in</span> str(e) <span class="kwd">or</span> <span class="str">"quota"</span> <span class="kwd">in</span> str(e).lower():', True),
            ('                sleep_time = 6 * (2 ** (attempt - 1))  <span class="cmt"># 6s, 12s, 24s</span>', True),
            ('                time.sleep(sleep_time)', True),
            ('', False),
            ('<span class="kwd">def</span> <span class="fn">evaluate_audio_branch</span>(self, turn_id: <span class="typ">int</span>, clip_path: Path):', False),
            ('    uploaded = self.client.files.upload(file=str(clip_path))', True),
            ('    res = self._create_interaction_with_retry(', False),
            ('        model=<span class="str">"gemini-3.6-flash"</span>,', False),
            ('        input=[', False),
            ('            {<span class="str">"type"</span>: <span class="str">"text"</span>, <span class="str">"text"</span>: f<span class="str">"Score acoustic delivery"</span>},', False),
            ('            {<span class="str">"type"</span>: <span class="str">"audio"</span>, <span class="str">"uri"</span>: uploaded.uri, <span class="str">"mime_type"</span>: <span class="str">"audio/wav"</span>}', True),
            ('        ],', False),
            ('        response_format={<span class="str">"type"</span>: <span class="str">"text"</span>, <span class="str">"mime_type"</span>: <span class="str">"application/json"</span>}', False),
            ('    )', False),
        ]
    },
    {
        "id": "07_api_websocket_gateway",
        "title": "API Gateway — WebSocket Full-Duplex Streaming Router",
        "subtitle": "backend/api/routers/voice.py",
        "badge": "GATEWAY: FASTAPI WS",
        "code_lines": [
            ('<span class="kwd">async def</span> <span class="fn">recv_worker</span>():', False),
            ('    <span class="kwd">while True</span>:', False),
            ('        message = <span class="kwd">await</span> websocket.receive()', False),
            ('        <span class="kwd">if</span> <span class="str">"bytes"</span> <span class="kwd">in</span> message:', True),
            ('            <span class="cmt"># Raw 16kHz PCM audio chunk from browser Worklet</span>', False),
            ('            audio_queue.put(message[<span class="str">"bytes"</span>])', True),
            ('        <span class="kwd">elif</span> <span class="str">"text"</span> <span class="kwd">in</span> message:', False),
            ('            data = json.loads(message[<span class="str">"text"</span>])', False),
            ('            <span class="kwd">if</span> data.get(<span class="str">"action"</span>) == <span class="str">"playback_event"</span>:', True),
            ('                evt = data.get(<span class="str">"type"</span>)', False),
            ('                turn = data.get(<span class="str">"turn_id"</span>, 0)', False),
            ('                <span class="kwd">if</span> evt == <span class="str">"playback_started"</span>:', False),
            ('                    turn_manager.on_playback_started(turn)', True),
            ('                <span class="kwd">elif</span> evt == <span class="str">"playback_finished"</span>:', False),
            ('                    turn_manager.on_playback_finished(turn)', True),
            ('            <span class="kwd">elif</span> data.get(<span class="str">"action"</span>) == <span class="str">"pause"</span>:', False),
            ('                engine.pause()', False),
        ]
    },
    {
        "id": "08_frontend_pcm_worklet",
        "title": "Web AudioWorklet — Native Decimation & Zero-Copy Transfer",
        "subtitle": "frontend/public/pcm-processor.js",
        "badge": "FRONTEND: AUDIO WORKLET",
        "code_lines": [
            ('<span class="cmt">// Native OS rate integer decimation (48000 / 16000 = 3x boxcar)</span>', False),
            ('<span class="kwd">const</span> factor = Math.round(<span class="kwd">this</span>._decimationFactor);', True),
            ('<span class="kwd">const</span> outputLength = Math.floor(inputChannel.length / factor);', False),
            ('<span class="kwd">const</span> downsampled = <span class="kwd">new</span> Float32Array(outputLength);', False),
            ('', False),
            ('<span class="kwd">for</span> (<span class="kwd">let</span> i = 0; i &lt; outputLength; i++) {', False),
            ('  <span class="kwd">let</span> sum = 0;', False),
            ('  <span class="kwd">for</span> (<span class="kwd">let</span> j = 0; j &lt; factor; j++) sum += inputChannel[i * factor + j];', False),
            ('  downsampled[i] = sum / factor;  <span class="cmt">// Clean box-car average</span>', True),
            ('}', False),
            ('', False),
            ('<span class="cmt">// Convert Float32 [-1.0, +1.0] to Int16 signed PCM</span>', False),
            ('<span class="kwd">const</span> pcm16 = <span class="kwd">new</span> Int16Array(downsampled.length);', False),
            ('<span class="kwd">for</span> (<span class="kwd">let</span> i = 0; i &lt; downsampled.length; i++) {', False),
            ('  <span class="kwd">let</span> s = Math.max(-1, Math.min(1, downsampled[i]));', False),
            ('  pcm16[i] = s &lt; 0 ? s * 0x8000 : s * 0x7FFF;', True),
            ('}', False),
            ('<span class="cmt">// Zero-copy transfer ArrayBuffer to main WebSocket thread</span>', False),
            ('<span class="kwd">this</span>.port.postMessage(pcm16.buffer, [pcm16.buffer]);', True),
        ]
    }
]


def render_card_html(snippet):
    """
    Renders standalone card HTML with Serene Learning WHITE THEME design tokens (DESIGN.md).
    Right pane removed; full width crisp code window.
    """
    lines_html = ""
    for idx, (line_content, is_highlight) in enumerate(snippet["code_lines"], 1):
        num_str = f"{idx:02d}"
        hl_class = " hl" if is_highlight else ""
        lines_html += f"""
        <div class="line{hl_class}">
          <span class="num">{num_str}</span>
          <span class="code">{line_content}</span>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{snippet['title']}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Manrope:wght@500;600;700;800&display=swap" rel="stylesheet">
<style>
  /* Serene Learning White Theme Design Tokens (DESIGN.md) */
  :root {{
    --surface: #ffffff;
    --background: #f8f9fa;
    --on-surface: #191c1d;
    --on-surface-variant: #49454d;
    --outline: #7a757e;
    --outline-variant: #cbc4ce;
    --primary: #65597b;           /* Lavender */
    --primary-container: #e6d6ff; /* Soft Light Lavender */
    --on-primary-container: #4d4162;
    --secondary: #426651;         /* Sage / Mint Green */
    --secondary-container: #c3ecd2;
    --on-secondary-container: #2a4e3a;
    --tertiary: #6d5a59;          /* Warm Rose / Terracotta */
    --tertiary-container: #f1d7d5;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: radial-gradient(circle at 10% 10%, rgba(230, 214, 255, 0.4) 0%, transparent 45%),
                radial-gradient(circle at 90% 20%, rgba(195, 236, 210, 0.35) 0%, transparent 45%),
                #f8f9fa;
    font-family: 'Fira Code', Consolas, monospace;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 24px;
  }}

  /* Pure White Card Window Container */
  .card-wrap {{
    width: 920px;
    background: #ffffff;
    border: 1.5px solid rgba(101, 89, 123, 0.18);
    border-radius: 18px;
    box-shadow: 
      0 18px 45px -8px rgba(101, 89, 123, 0.10),
      0 4px 16px rgba(0, 0, 0, 0.04),
      inset 0 1px 1px 0 rgba(255, 255, 255, 1);
    overflow: hidden;
    position: relative;
  }}

  /* Top Gentle Lavender Accent Line */
  .card-wrap::after {{
    content: '';
    position: absolute;
    top: 0; left: 6%; right: 6%;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(101, 89, 123, 0.45), transparent);
  }}

  /* Window Chrome Header (Soft Frosted Gray-White) */
  .header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 13px 22px;
    border-bottom: 1px solid rgba(101, 89, 123, 0.12);
    background: #f4f5f6;
  }}

  .dots-group {{
    display: flex;
    align-items: center;
    gap: 9px;
  }}

  /* Window Dots using Serene Learning Accents */
  .dot {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }}
  .dot-1 {{ background-color: #e07a75; box-shadow: 0 0 4px rgba(224, 122, 117, 0.4); }} /* Terracotta / Rose */
  .dot-2 {{ background-color: #65597b; box-shadow: 0 0 4px rgba(101, 89, 123, 0.4); }}  /* Primary: Lavender */
  .dot-3 {{ background-color: #426651; box-shadow: 0 0 4px rgba(66, 102, 81, 0.4); }}   /* Secondary: Mint */

  .title-group {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}

  .badge {{
    font-family: 'Manrope', sans-serif;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    padding: 3px 10px;
    border-radius: 6px;
    background: #e6d6ff; /* primary-container */
    border: 1px solid rgba(101, 89, 123, 0.25);
    color: #4d4162;      /* on-primary-container */
    text-transform: uppercase;
  }}

  .file-name {{
    font-size: 12px;
    color: #49454d; /* on-surface-variant */
    font-weight: 500;
  }}

  .netran-pill {{
    font-family: 'Manrope', sans-serif;
    font-size: 11px;
    font-weight: 800;
    color: #65597b; /* primary */
    letter-spacing: 0.06em;
  }}

  /* Full-Width Code Body */
  .body {{
    padding: 20px 24px 22px 20px;
    background: #ffffff;
  }}

  .code-pane {{
    width: 100%;
    overflow: hidden;
  }}

  .line {{
    display: flex;
    align-items: center;
    font-size: 13.5px;
    line-height: 23px;
    padding: 0 8px;
    border-radius: 4px;
  }}

  .line.hl {{
    background: rgba(230, 214, 255, 0.45); /* Soft lavender highlight */
    border-left: 3px solid #65597b;
  }}

  .num {{
    color: #9a959f; /* outline neutral */
    font-size: 12px;
    width: 32px;
    flex-shrink: 0;
    user-select: none;
    text-align: right;
    margin-right: 20px;
  }}

  .code {{
    color: #191c1d; /* on-surface */
    white-space: pre;
    font-family: 'Fira Code', Consolas, monospace;
  }}

  /* Serene Learning High-Contrast Light Syntax Highlighting */
  .kwd {{ color: #5f3f9e; font-weight: 600; }} /* Deep Lavender */
  .cls {{ color: #235c3b; font-weight: 600; }} /* Forest Mint */
  .fn  {{ color: #375382; font-weight: 500; }} /* Slate Blue */
  .str {{ color: #206d44; }}                   /* Sage Mint */
  .typ {{ color: #5f3f9e; }}                   /* Lavender */
  .cmt {{ color: #7a757e; font-style: italic; }} /* Outline Slate Neutral */
</style>
</head>
<body>
<div class="card-wrap">
  <div class="header">
    <div class="dots-group">
      <div class="dot dot-1"></div>
      <div class="dot dot-2"></div>
      <div class="dot dot-3"></div>
    </div>
    <div class="title-group">
      <span class="badge">{snippet['badge']}</span>
      <span class="file-name">{snippet['subtitle']}</span>
    </div>
    <div class="netran-pill">NETRAN AI</div>
  </div>
  <div class="body">
    <div class="code-pane">
      {lines_html}
    </div>
  </div>
</div>
</body>
</html>
"""


def build_interactive_index_html():
    """Builds a master index.html showcasing all 8 cards in Serene Learning White Theme."""
    cards_html = ""
    for s in SNIPPETS:
        lines_html = ""
        for idx, (line_content, is_highlight) in enumerate(s["code_lines"], 1):
            num_str = f"{idx:02d}"
            hl_class = " hl" if is_highlight else ""
            lines_html += f"""
            <div class="line{hl_class}">
              <span class="num">{num_str}</span>
              <span class="code">{line_content}</span>
            </div>"""

        cards_html += f"""
        <section class="snippet-section" id="{s['id']}">
          <div class="section-title">
            <h3>{s['title']}</h3>
            <a class="img-link" href="{s['id']}.png" target="_blank">📥 View PNG Image</a>
          </div>
          <div class="card-wrap">
            <div class="header">
              <div class="dots-group">
                <div class="dot dot-1"></div>
                <div class="dot dot-2"></div>
                <div class="dot dot-3"></div>
              </div>
              <div class="title-group">
                <span class="badge">{s['badge']}</span>
                <span class="file-name">{s['subtitle']}</span>
              </div>
              <div class="netran-pill">NETRAN AI</div>
            </div>
            <div class="body">
              <div class="code-pane">
                {lines_html}
              </div>
            </div>
          </div>
        </section>
        """

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Netran AI — White Theme Code Listings (Serene Learning)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Manrope:wght@500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {{
    --surface: #ffffff;
    --background: #f8f9fa;
    --on-surface: #191c1d;
    --on-surface-variant: #49454d;
    --outline: #7a757e;
    --primary: #65597b;
    --primary-container: #e6d6ff;
    --on-primary-container: #4d4162;
    --secondary: #426651;
    --secondary-container: #c3ecd2;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: radial-gradient(circle at 10% 10%, rgba(230, 214, 255, 0.4) 0%, transparent 45%),
                radial-gradient(circle at 90% 20%, rgba(195, 236, 210, 0.35) 0%, transparent 45%),
                #f8f9fa;
    color: #191c1d;
    font-family: 'Manrope', sans-serif;
    padding: 30px 20px 80px;
  }}

  .container {{
    max-width: 960px;
    margin: 0 auto;
  }}

  header.masthead {{
    text-align: center;
    margin-bottom: 36px;
    padding-bottom: 22px;
    border-bottom: 1px solid rgba(101, 89, 123, 0.15);
  }}

  .masthead h1 {{
    font-size: 26px;
    font-weight: 800;
    color: #191c1d;
    letter-spacing: -0.02em;
    margin-bottom: 8px;
  }}

  .masthead h1 span {{
    color: #65597b;
  }}

  .masthead p {{
    color: #49454d;
    font-size: 13.5px;
  }}

  .nav-pills {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    margin-top: 18px;
  }}

  .nav-pills a {{
    font-size: 11.5px;
    font-weight: 600;
    text-decoration: none;
    color: #4d4162;
    background: #e6d6ff;
    border: 1px solid rgba(101, 89, 123, 0.25);
    padding: 5px 12px;
    border-radius: 8px;
    transition: all 0.2s;
  }}

  .nav-pills a:hover {{
    background: #cfc0e8;
    color: #191c1d;
  }}

  .snippet-section {{
    margin-bottom: 40px;
  }}

  .section-title {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }}

  .section-title h3 {{
    font-size: 15px;
    font-weight: 700;
    color: #191c1d;
  }}

  .img-link {{
    font-size: 11.5px;
    color: #2a4e3a;
    text-decoration: none;
    font-weight: 600;
    background: #c3ecd2;
    border: 1px solid rgba(66, 102, 81, 0.3);
    padding: 4px 10px;
    border-radius: 6px;
  }}

  .img-link:hover {{
    background: #a8d0b6;
  }}

  /* Card Component */
  .card-wrap {{
    background: #ffffff;
    border: 1.5px solid rgba(101, 89, 123, 0.18);
    border-radius: 18px;
    box-shadow: 
      0 18px 45px -8px rgba(101, 89, 123, 0.10),
      0 4px 16px rgba(0, 0, 0, 0.04),
      inset 0 1px 1px 0 rgba(255, 255, 255, 1);
    overflow: hidden;
    position: relative;
  }}

  .card-wrap::after {{
    content: '';
    position: absolute;
    top: 0; left: 6%; right: 6%;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(101, 89, 123, 0.45), transparent);
  }}

  .header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 13px 22px;
    border-bottom: 1px solid rgba(101, 89, 123, 0.12);
    background: #f4f5f6;
  }}

  .dots-group {{ display: flex; align-items: center; gap: 9px; }}
  .dot {{ width: 12px; height: 12px; border-radius: 50%; }}
  .dot-1 {{ background-color: #e07a75; box-shadow: 0 0 4px rgba(224, 122, 117, 0.4); }}
  .dot-2 {{ background-color: #65597b; box-shadow: 0 0 4px rgba(101, 89, 123, 0.4); }}
  .dot-3 {{ background-color: #426651; box-shadow: 0 0 4px rgba(66, 102, 81, 0.4); }}

  .title-group {{ display: flex; align-items: center; gap: 12px; }}

  .badge {{
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    padding: 3px 10px;
    border-radius: 6px;
    background: #e6d6ff;
    border: 1px solid rgba(101, 89, 123, 0.25);
    color: #4d4162;
    text-transform: uppercase;
  }}

  .file-name {{
    font-size: 12px;
    color: #49454d;
    font-family: 'Fira Code', monospace;
    font-weight: 500;
  }}

  .netran-pill {{
    font-size: 11px;
    font-weight: 800;
    color: #65597b;
    letter-spacing: 0.06em;
  }}

  .body {{
    padding: 20px 24px 22px 20px;
    background: #ffffff;
    font-family: 'Fira Code', Consolas, monospace;
  }}

  .code-pane {{
    width: 100%;
    overflow-x: auto;
  }}

  .line {{
    display: flex;
    align-items: center;
    font-size: 13.5px;
    line-height: 23px;
    padding: 0 8px;
    border-radius: 4px;
  }}

  .line.hl {{
    background: rgba(230, 214, 255, 0.45);
    border-left: 3px solid #65597b;
  }}

  .num {{
    color: #9a959f;
    font-size: 12px;
    width: 32px;
    flex-shrink: 0;
    user-select: none;
    text-align: right;
    margin-right: 20px;
  }}

  .code {{
    color: #191c1d;
    white-space: pre;
    font-family: 'Fira Code', Consolas, monospace;
  }}

  .kwd {{ color: #5f3f9e; font-weight: 600; }}
  .cls {{ color: #235c3b; font-weight: 600; }}
  .fn  {{ color: #375382; font-weight: 500; }}
  .str {{ color: #206d44; }}
  .typ {{ color: #5f3f9e; }}
  .cmt {{ color: #7a757e; font-style: italic; }}
</style>
</head>
<body>
<div class="container">
  <header class="masthead">
    <h1>Netran AI — <span>Key Implementation Code Cards (White Theme)</span></h1>
    <p>Serene Learning Design System | Academic Year 2025–26 | Final Year Project Report Book</p>
    <div class="nav-pills">
      <a href="#01_stage3_turn_manager">01. TurnManager State Machine</a>
      <a href="#02_stage3_silero_vad_filter">02. IIR Filter & Silero VAD</a>
      <a href="#03_stage3_brain_llm_stream">03. Brain LLM Stream</a>
      <a href="#04_stage3_speaker_flush">04. Speaker Playback & Flush</a>
      <a href="#05_stage2_planner_analyst">05. Dual Question Engine</a>
      <a href="#06_stage4_gemini_multimodal">06. Multimodal Evaluator</a>
      <a href="#07_api_websocket_gateway">07. WebSocket API Gateway</a>
      <a href="#08_frontend_pcm_worklet">08. AudioWorklet Decimation</a>
    </div>
  </header>

  {cards_html}
</div>
</body>
</html>
"""
    return index_html


def main():
    print("[1/3] Generating updated WHITE THEME HTML cards and master index.html...")
    # 1. Master index.html
    master_html = build_interactive_index_html()
    master_path = OUTPUT_DIR / "index.html"
    master_path.write_text(master_html, encoding="utf-8")
    print(f"  -> Saved master HTML: {master_path}")

    # 2. Individual card HTML files
    card_paths = []
    for snippet in SNIPPETS:
        card_html = render_card_html(snippet)
        card_path = OUTPUT_DIR / f"{snippet['id']}.html"
        card_path.write_text(card_html, encoding="utf-8")
        card_paths.append((snippet['id'], card_path))
        print(f"  -> Generated card: {card_path.name}")

    print("\n[2/3] Capturing high-resolution WHITE THEME PNG screenshots via Headless Chrome...")
    for snippet_id, html_path in card_paths:
        png_path = OUTPUT_DIR / f"{snippet_id}.png"
        file_url = html_path.as_uri()

        # Run headless chrome to take screenshot with Serene White dimensions
        cmd = [
            CHROME_PATH,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=2",  # 2x Retina resolution
            "--window-size=980,560",
            f"--screenshot={png_path}",
            file_url
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if png_path.exists() and png_path.stat().st_size > 5000:
                print(f"  [OK] Screenshot captured: {png_path.name} ({png_path.stat().st_size // 1024} KB)")
            else:
                print(f"  [FAIL] Failed for {snippet_id}: {res.stderr}")
        except Exception as e:
            print(f"  [FAIL] Exception capturing {snippet_id}: {e}")

    print("\n[3/3] Done! All Serene Learning WHITE THEME code cards and PNG screenshots regenerated successfully.")


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    main()
