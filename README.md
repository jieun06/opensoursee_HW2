# Voice Spectrum Lab

로컬 macOS에서 음성 오디오의 파형, 스펙트로그램, 기본주파수(Pitch)를 분석하는 FastAPI 웹앱입니다. 업로드한 MP3/WAV는 서버의 임시 파일로 처리되며 프로젝트에 저장되지 않습니다.

## 요구 환경

- macOS
- Python 3.10 이상 (`python3` 명령)
- 가상환경 없이도 실행 가능

## 설치

```zsh
cd upload
python3 -m pip install -r requirements.txt
```

## 실행

```zsh
python3 -m uvicorn main:app --reload
```

브라우저에서 <http://127.0.0.1:8000>을 열고 MP3 또는 WAV 파일을 선택하세요. 파일은 최대 180초까지 분석합니다. 종료하려면 터미널에서 `Ctrl+C`를 누르세요.

## 구성

- `main.py`: FastAPI API 및 librosa/matplotlib 분석 로직
- `static/`: 업로드·재생 UI와 분석 그래프 화면
- `requirements.txt`: 실행 의존성

분석 결과는 브라우저에 표시할 PNG 데이터로 반환되며, 인증정보나 개인정보를 사용하지 않습니다.
