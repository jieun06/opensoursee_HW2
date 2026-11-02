from pathlib import Path
import os
from tempfile import NamedTemporaryFile
import base64, io

# macOS system Python installs can make numba's package cache unwritable.
# Disabling only the persistent cache keeps librosa's JIT CPU path enabled.
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/voice-spectrum-numba-cache")
import librosa
import librosa.display
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
app = FastAPI(title="Voice Spectrum Lab")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")

def chart_png(kind, y, sr, title):
    fig, ax = plt.subplots(figsize=(10, 4), dpi=110)
    fig.patch.set_facecolor("#101522"); ax.set_facecolor("#101522")
    if kind == "spectrogram":
        spec = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=2048, hop_length=512)), ref=np.max)
        img = librosa.display.specshow(spec, sr=sr, hop_length=512, x_axis="time", y_axis="log", ax=ax, cmap="magma")
        fig.colorbar(img, ax=ax, format="%+2.0f dB", pad=.02)
        ax.set_ylabel("Frequency (Hz)")
    elif kind == "pitch":
        f0, voiced, _ = librosa.pyin(y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"), sr=sr, frame_length=2048, hop_length=512)
        times = librosa.times_like(f0, sr=sr, hop_length=512)
        ax.plot(times, f0, color="#65e6c2", linewidth=1.5)
        ax.set_ylim(50, 1100); ax.set_ylabel("Hz")
    else:
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        ax.plot(librosa.times_like(rms, sr=sr, hop_length=512), rms, color="#ffb86b")
        ax.set_ylabel("Amplitude")
    ax.set_title(title, color="white", loc="left", pad=12, fontsize=13)
    ax.set_xlabel("Time (s)"); ax.tick_params(colors="#aeb7ca");
    for spine in ax.spines.values(): spine.set_color("#2e3850")
    fig.tight_layout()
    out = io.BytesIO(); fig.savefig(out, format="png", facecolor=fig.get_facecolor()); plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode()

@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    allowed = {".mp3", ".wav"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, "MP3 또는 WAV 파일만 업로드할 수 있습니다.")
    data = await file.read()
    if not data: raise HTTPException(400, "빈 파일입니다.")
    try:
        with NamedTemporaryFile(suffix=suffix) as tmp:
            tmp.write(data); tmp.flush()
            y, sr = librosa.load(tmp.name, sr=None, mono=True, duration=180)
        if len(y) < 1024: raise ValueError("오디오가 너무 짧습니다.")
        duration = len(y) / sr
        return {"filename": file.filename, "duration": round(duration, 2), "sample_rate": sr,
                "spectrogram": chart_png("spectrogram", y, sr, "Spectrogram · Log frequency"),
                "pitch": chart_png("pitch", y, sr, "Fundamental frequency (F0)"),
                "waveform": chart_png("waveform", y, sr, "Waveform")}
    except Exception as exc:
        raise HTTPException(422, f"오디오를 분석할 수 없습니다: {exc}")

@app.exception_handler(413)
async def too_large(_, __): return JSONResponse({"detail": "파일이 너무 큽니다."}, status_code=413)
