import os
import sys
import shutil
import re
import tempfile
import subprocess
from pathlib import Path
from django.conf import settings


def to_short_path(path: Path | str) -> str:
    """Безопасный 8.3 короткий DOS-путь без кириллицы и пробелов для Windows C++ бинарников (whisper.cpp)"""
    p_str = str(Path(path).resolve())
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            buf = ctypes.create_unicode_buffer(512)
            res = ctypes.windll.kernel32.GetShortPathNameW(p_str, buf, 512)
            if 0 < res < 512 and buf.value:
                return buf.value
        except Exception:
            pass
    return p_str


class WhisperVulkanService:
    """
    Аппаратно-ускоренный движок локального распознавания речи Whisper (ggml / whisper.cpp)
    для интерактивного симулятора завода «Очаково».
    - Windows: поддержка Vulkan GPU (NVIDIA RTX/GTX, AMD, Intel Arc).
    - Linux / Docker / macOS: автоматический поиск бинарников в PATH или системных директориях.
    - Оптимизирован под лексику брожения, квасоварения и регламентов комбината «Очаково».
    """

    _BASE_DIR = Path(settings.BASE_DIR)

    @classmethod
    def get_bin_path(cls) -> Path | None:
        """
        Универсальный поиск исполняемого бинарника whisper-cli для текущей ОС (Windows, Linux, Docker).
        """
        # 1. Проверяем явную переменную окружения
        env_bin = os.environ.get("WHISPER_BIN_PATH")
        if env_bin:
            p = Path(env_bin)
            if p.exists() and (sys.platform == "win32" or os.access(p, os.X_OK)):
                return p

        # 2. Локальный Windows-бандл с Vulkan-ускорением (только для платформы Windows)
        if sys.platform == "win32":
            candidate_paths = [
                cls._BASE_DIR / "bin" / "whisper_vulkan" / "whisper-cli.exe",
                cls._BASE_DIR / "bin" / "whisper-cli.exe",
                cls._BASE_DIR / "whisper_vulkan" / "whisper-cli.exe",
            ]
            for p in candidate_paths:
                if p.exists():
                    return p

        # 3. Поиск системной утилиты в PATH (Linux, macOS, Docker)
        for cmd in ["whisper-cli", "whisper.cpp", "whisper"]:
            found = shutil.which(cmd)
            if found:
                return Path(found)

        # 4. Стандартные пути Linux и Docker контейнеров
        for cand in [
            "/usr/local/bin/whisper-cli",
            "/usr/bin/whisper-cli",
            cls._BASE_DIR / "bin" / "whisper_linux" / "whisper-cli",
            cls._BASE_DIR / "bin" / "whisper-cli",
        ]:
            cand_p = Path(cand)
            if cand_p.exists() and os.access(cand_p, os.X_OK):
                return cand_p

        return None

    @classmethod
    def get_ffmpeg_bin(cls) -> str:
        """Поиск бинарника FFmpeg для транскодирования аудио (Windows, Linux, Docker)"""
        found = shutil.which("ffmpeg")
        if found:
            return found
        if sys.platform == "win32":
            for cand in [
                cls._BASE_DIR / "bin" / "ffmpeg.exe",
                cls._BASE_DIR / "bin" / "whisper_vulkan" / "ffmpeg.exe",
            ]:
                if cand.exists():
                    return to_short_path(cand)
        return "ffmpeg"

    @classmethod
    def get_model_path(cls) -> Path | None:
        """Поиск ggml-моделей (приоритет: small -> base -> любая bin) под Windows и Linux/Docker"""
        env_model = os.environ.get("WHISPER_MODEL_PATH")
        if env_model:
            p = Path(env_model)
            if p.exists() and p.stat().st_size > 10 * 1024 * 1024:
                return p

        search_dirs = [
            cls._BASE_DIR / "bin" / "whisper_vulkan" / "models",
            cls._BASE_DIR / "models",
            cls._BASE_DIR / "careers" / "models",
            Path("/opt/whisper/models"),
            Path("/usr/local/share/whisper/models"),
            Path("/app/models"),
            Path.home() / ".cache" / "whisper",
        ]

        # 1. Модель small (высокая точность русской речи)
        for s_dir in search_dirs:
            if s_dir.exists():
                small_model = s_dir / "ggml-small.bin"
                if small_model.exists() and small_model.stat().st_size > 100 * 1024 * 1024:
                    return small_model

        # 2. Модель base (высокая скорость)
        for s_dir in search_dirs:
            if s_dir.exists():
                base_model = s_dir / "ggml-base.bin"
                if base_model.exists() and base_model.stat().st_size > 20 * 1024 * 1024:
                    return base_model

        # 3. Любая ggml модель
        for s_dir in search_dirs:
            if s_dir.exists():
                for bin_file in s_dir.glob("ggml-*.bin"):
                    if bin_file.stat().st_size > 10 * 1024 * 1024:
                        return bin_file

        return None

    @classmethod
    def is_available(cls) -> bool:
        """Проверяет доступность бинарника и модели Whisper"""
        return bool(cls.get_bin_path() and cls.get_model_path())

    @classmethod
    def get_acceleration_config(cls) -> tuple[str, bool]:
        """
        Возвращает кортеж (mode, fallback_enabled):
        mode: 'vulkan', 'cpu', 'auto'
        fallback_enabled: bool (True по умолчанию)
        """
        mode = getattr(settings, 'GGML_ACCELERATION', os.getenv('GGML_ACCELERATION', 'auto')).strip().lower()
        if mode not in ('vulkan', 'cpu', 'auto'):
            mode = 'auto'
        fallback = getattr(settings, 'GGML_VULKAN_FALLBACK_CPU', None)
        if fallback is None:
            fallback = os.getenv('GGML_VULKAN_FALLBACK_CPU', 'True').strip().lower() in ('true', '1', 'yes')
        return mode, fallback

    @classmethod
    def check_vulkan_device(cls) -> dict:
        """Диагностика доступности Vulkan GPU для whisper-cli (Windows и Linux/Docker)"""
        bin_path = cls.get_bin_path()
        if not bin_path:
            return {"available": False, "reason": "Бинарник whisper-cli не найден"}
        if sys.platform == "win32":
            has_vulkan_dll = (bin_path.parent / "ggml-vulkan.dll").exists()
            return {"available": has_vulkan_dll, "vulkan_dll": has_vulkan_dll}

        # Среда Linux / Docker контейнер
        has_vulkan_info = bool(shutil.which("vulkaninfo"))
        has_libvulkan = any(
            Path(p).exists() for p in [
                "/usr/lib/x86_64-linux-gnu/libvulkan.so.1",
                "/usr/local/lib/libvulkan.so.1",
                "/usr/lib/libvulkan.so.1",
                "/usr/lib64/libvulkan.so.1",
            ]
        )
        return {"available": has_vulkan_info or has_libvulkan, "vulkan_linux": True}


    @classmethod
    def is_audio_silent(cls, wav_path: Path, min_rms: float = 160.0, min_peak: int = 400) -> bool:
        """
        Проверяет, содержит ли аудиозапись реальный слышимый сигнал/голос,
        или это цифровая тишина / тихий фоновый шум микрофона.
        Предотвращает галлюцинации Whisper (например, «Что происходит?» на тишине).
        """
        try:
            import wave
            import struct
            import math
            with wave.open(str(wav_path), 'rb') as wf:
                n_frames = wf.getnframes()
                if n_frames == 0:
                    return True
                # Считываем до 15 секунд аудио (16kHz 16-bit)
                max_read = min(n_frames, 16000 * 15)
                frames = wf.readframes(max_read)
                sample_count = len(frames) // 2
                if sample_count == 0:
                    return True
                samples = struct.unpack(f"<{sample_count}h", frames)
                peak = max(abs(s) for s in samples)
                if peak < min_peak:
                    return True
                sum_sq = sum(s * s for s in samples)
                rms = math.sqrt(sum_sq / sample_count)
                return rms < min_rms
        except Exception:
            return False

    @classmethod
    def transcribe(cls, audio_bytes: bytes, language: str = "ru") -> dict:
        """
        Транскрибирует аудиозапись речи стажёра в цеху в русский текст.
        Поддерживает форматы webm, ogg, wav, mp3.
        Режимы ускорения ggml:
          - 'auto': приоритет Vulkan GPU с авто-fallback на CPU
          - 'vulkan': приоритет Vulkan GPU (fallback на CPU если разрешено)
          - 'cpu': только CPU AVX2 (без запуска Vulkan GPU)
        """
        if not audio_bytes:
            return {"ok": False, "error": "Аудиоданные не получены", "text": ""}

        bin_path = cls.get_bin_path()
        model_path = cls.get_model_path()
        if not bin_path or not model_path:
            return {
                "ok": False,
                "error": "Локальный модуль Whisper ggml не обнаружен на сервере",
                "text": ""
            }

        model_tag = "whisper_small" if "small" in model_path.name.lower() else "whisper_base"

        # Временная папка для декодирования аудио (Windows или Linux/Docker)
        temp_dir = cls._BASE_DIR / "bin" / "whisper_vulkan" / "tmp"
        if sys.platform != "win32" or not temp_dir.parent.exists():
            temp_dir = cls._BASE_DIR / "tmp"
        try:
            temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            temp_dir = Path(tempfile.gettempdir())

        import uuid
        uid = uuid.uuid4().hex[:10]
        wav_path = temp_dir / f"och_rec_{uid}.wav"

        exec_cwd = str(bin_path.parent) if sys.platform == "win32" else str(cls._BASE_DIR)
        sub_env = os.environ.copy()
        if sys.platform != "win32":
            current_ld = sub_env.get("LD_LIBRARY_PATH", "")
            sub_env["LD_LIBRARY_PATH"] = f"/usr/local/lib:{current_ld}" if current_ld else "/usr/local/lib"

        # Безопасные пути для устранения сбоев на путях с кириллицей в Windows C++ (в Linux - стандартные)
        if sys.platform == "win32":
            try:
                model_safe = os.path.relpath(model_path, exec_cwd)
            except Exception:
                model_safe = to_short_path(model_path)
            try:
                wav_safe = os.path.relpath(wav_path, exec_cwd)
            except Exception:
                wav_safe = to_short_path(wav_path)
            bin_safe = str(bin_path.resolve())
            ffmpeg_raw = cls.get_ffmpeg_bin()
            ffmpeg_bin = str(Path(ffmpeg_raw).resolve()) if Path(ffmpeg_raw).exists() else ffmpeg_raw
        else:
            bin_safe = to_short_path(bin_path)
            model_safe = to_short_path(model_path)
            wav_safe = to_short_path(wav_path)
            ffmpeg_bin = cls.get_ffmpeg_bin()

        try:
            # 1. Конвертация в 16kHz mono WAV через FFmpeg
            ffmpeg_cmd = [
                ffmpeg_bin, "-hide_banner", "-loglevel", "error",
                "-i", "pipe:0",
                "-ar", "16000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
                wav_safe,
                "-y"
            ]
            proc_ff = subprocess.Popen(
                ffmpeg_cmd,
                cwd=exec_cwd,
                env=sub_env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            _, ff_err = proc_ff.communicate(input=audio_bytes, timeout=10)
            if proc_ff.returncode != 0 or not wav_path.exists() or wav_path.stat().st_size < 100:
                # Если ffmpeg не смог распарсить или отсутствует, проверяем не передан ли уже WAV
                if audio_bytes[:4] == b"RIFF":
                    with open(wav_path, "wb") as f:
                        f.write(audio_bytes)
                else:
                    return {
                        "ok": False,
                        "error": f"Ошибка транскодирования аудио: {ff_err.decode('utf-8', errors='ignore')[:150]}",
                        "text": ""
                    }

            # 2. Выбор режима GGML (Vulkan GPU vs CPU) на основе конфигурации .env
            mode, fallback_enabled = cls.get_acceleration_config()
            cpu_threads = min(os.cpu_count() or 4, 8)
            ochakovo_prompt = "Очаково, квас, брожение, сусло, наставник, Михалыч, ЦКТ, температура, закваска, гликоль, Krones, конвейер, робот, лаборатория, кислотность, pH-метр, паллета."
            run_mode = "vulkan" if mode in ("vulkan", "auto") else "cpu"
            executed_engine = f"whisper_{run_mode}_{model_tag}"

            # 3. Проверка уровня звука (VAD) для мгновенного отсечения тишины без галлюцинаций
            if cls.is_audio_silent(wav_path):
                return {
                    "ok": True,
                    "text": "",
                    "silence": True,
                    "engine": executed_engine,
                    "model": model_tag
                }
            if run_mode == "cpu":
                # Принудительный режим CPU без обращения к Vulkan GPU
                whisper_cmd = [
                    bin_safe,
                    "-m", model_safe,
                    "-l", language,
                    "-nt",
                    "-ng",
                    "-f", wav_safe,
                    "--prompt", ochakovo_prompt,
                    "-bs", "2",
                    "-bo", "2",
                    "-sns",
                    "-nth", "0.65",
                    "-t", str(cpu_threads)
                ]
                proc_w = subprocess.Popen(
                    whisper_cmd,
                    cwd=exec_cwd,
                    env=sub_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout_data, stderr_data = proc_w.communicate(timeout=30)
                if proc_w.returncode != 0:
                    err_msg = stderr_data.decode('utf-8', errors='ignore')[:200]
                    return {
                        "ok": False,
                        "error": f"Сбой Whisper CPU (код {proc_w.returncode}): {err_msg}",
                        "text": ""
                    }
            else:
                # В приоритете Vulkan GPU ускорение
                whisper_cmd = [
                    bin_safe,
                    "-m", model_safe,
                    "-l", language,
                    "-nt",
                    "-f", wav_safe,
                    "--prompt", ochakovo_prompt,
                    "-bs", "2",
                    "-bo", "2",
                    "-sns",
                    "-nth", "0.65",
                    "-t", str(cpu_threads)
                ]
                proc_w = subprocess.Popen(
                    whisper_cmd,
                    cwd=exec_cwd,
                    env=sub_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout_data, stderr_data = proc_w.communicate(timeout=25)

                # Если Vulkan выдал сбой, безопасно запускаем с -ng (CPU AVX2 fallback)
                if proc_w.returncode != 0:
                    if fallback_enabled:
                        executed_engine = f"whisper_cpu_fallback_{model_tag}"
                        cpu_whisper_cmd = [
                            bin_safe,
                            "-m", model_safe,
                            "-l", language,
                            "-nt",
                            "-ng",
                            "-f", wav_safe,
                            "-t", str(cpu_threads)
                        ]
                        proc_cpu = subprocess.Popen(
                            cpu_whisper_cmd,
                            cwd=exec_cwd,
                            env=sub_env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        c_out, c_err = proc_cpu.communicate(timeout=25)
                        if proc_cpu.returncode == 0 and c_out:
                            stdout_data = c_out
                            stderr_data = c_err
                        else:
                            err_msg = (c_err or stderr_data).decode('utf-8', errors='ignore')[:200]
                            return {
                                "ok": False,
                                "error": f"Сбой Whisper Vulkan (код {proc_w.returncode}) и CPU Fallback (код {proc_cpu.returncode}): {err_msg}",
                                "text": ""
                            }
                    else:
                        err_msg = stderr_data.decode('utf-8', errors='ignore')[:200]
                        return {
                            "ok": False,
                            "error": f"Сбой Whisper Vulkan GPU (код {proc_w.returncode}, CPU fallback отключен): {err_msg}",
                            "text": ""
                        }

            # 3. Извлечение распознанного текста
            raw_text = stdout_data.decode('utf-8', errors='ignore').strip()
            if not raw_text:
                lines = []
                for line in stderr_data.decode('utf-8', errors='ignore').splitlines():
                    clean_l = line.strip()
                    if clean_l and not any(clean_l.startswith(p) for p in [
                        "ggml", "whisper", "system_info", "main:", "load time", "fallbacks",
                        "mel time", "sample time", "encode time", "decode time", "batchd time",
                        "prompt time", "total time"
                    ]):
                        lines.append(clean_l)
                raw_text = " ".join(lines).strip()

            cleaned = re.sub(r'\[.*?\]', '', raw_text)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            # Очищаем галлюцинации Whisper при тишине (эмодзи, спецсимволы, ноты, известные ложные фразы)
            norm_check = re.sub(r'[^\w\s]', '', cleaned).strip().lower()
            silence_hallucinations = {
                "что происходит", "что происхожит", "что это", "что тут происходит",
                "субтитры", "субтитры сделал", "субтитры создавал", "редактор субтитров",
                "продолжение следует", "спасибо за просмотр", "подписывайтесь на канал",
                "ставьте лайки", "до скорой встречи", "переведено и озвучено", "всем пока"
            }
            if norm_check in silence_hallucinations or not re.search(r'[\w\dа-яА-ЯёЁa-zA-Z]', cleaned):
                cleaned = ""

            return {
                "ok": True,
                "text": cleaned,
                "engine": executed_engine,
                "model": model_tag
            }

        except Exception as exc:
            return {
                "ok": False,
                "error": f"Ошибка Whisper: {exc}",
                "text": ""
            }
        finally:
            if wav_path.exists():
                try:
                    wav_path.unlink()
                except Exception:
                    pass
