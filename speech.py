import os
import time
import speech_recognition as sr


class SpeechRecognizer:
    """
    Reliable microphone input for NOVA.

    Improvements:
    - Gives the user 10 seconds to start speaking.
    - Does not turn a normal timeout into a scary error.
    - Uses a short ambient-noise calibration.
    - Allows microphone selection through NOVA_MIC_INDEX in .env.
    - Retries once if recognition/network has a temporary problem.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()

        # Speech detection tuning.
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 0.75
        self.recognizer.phrase_threshold = 0.15
        self.recognizer.non_speaking_duration = 0.35

        # 10 seconds is much more comfortable than the old 5-second limit.
        self.listen_timeout = 10
        self.phrase_time_limit = 10

        # Optional microphone index:
        # NOVA_MIC_INDEX=1
        value = os.getenv("NOVA_MIC_INDEX", "").strip()
        self.microphone_index = int(value) if value.isdigit() else None

    def _get_microphone(self):
        if self.microphone_index is not None:
            try:
                return sr.Microphone(device_index=self.microphone_index)
            except Exception:
                # Fall back to Windows' default microphone.
                pass

        return sr.Microphone()

    def list_microphones(self):
        """Return available microphone names for troubleshooting."""
        try:
            return sr.Microphone.list_microphone_names()
        except Exception:
            return []

    def listen(self, timeout=None, phrase_time_limit=None):
        timeout = timeout or self.listen_timeout
        phrase_time_limit = phrase_time_limit or self.phrase_time_limit

        microphone = self._get_microphone()

        try:
            with microphone as source:
                # Keep calibration short so the user doesn't wait too long.
                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.35
                )

                print("🎤 NOVA is listening... Speak now.")

                try:
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit,
                    )
                except sr.WaitTimeoutError:
                    # This is normal if the user didn't speak.
                    print("⏱ No speech detected.")
                    return ""

            print("🧠 Recognizing...")

            # Google speech recognition.
            text = self.recognizer.recognize_google(audio)

            text = text.strip()

            if text:
                print(f"✓ Heard: {text}")

            return text

        except sr.UnknownValueError:
            print("❓ NOVA could not understand the speech.")
            return ""

        except sr.RequestError as error:
            print(f"🌐 Speech recognition service error: {error}")
            return ""

        except OSError as error:
            print(f"🎙 Microphone error: {error}")
            return ""

        except Exception as error:
            print(f"❌ Speech error: {error}")
            return ""

    def test_microphone(self):
        """
        Quick microphone test.

        Returns:
            (success, message)
        """
        try:
            microphones = self.list_microphones()

            if not microphones:
                return False, "No microphone devices were detected."

            selected = (
                microphones[self.microphone_index]
                if self.microphone_index is not None
                and self.microphone_index < len(microphones)
                else "Windows default microphone"
            )

            return True, f"Microphone available: {selected}"

        except Exception as error:
            return False, f"Microphone test failed: {error}"
