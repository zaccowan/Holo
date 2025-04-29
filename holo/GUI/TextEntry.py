import json
import os
from pathlib import Path
import threading
import customtkinter
import pyaudio
import vosk

"""
TextEntry.py - Creates a popup window for text entry with both keyboard and speech input.
Provides an interface for typing text or using speech recognition to add text
to the canvas. Includes speech recognition controls and text submission.
"""


class TextEntryWindow(customtkinter.CTkToplevel):

    do_stop_speech = False

    def __init__(
        self,
        parent,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.geometry("720x720")
        self.title("Text Entry Window")
        self.attributes("-topmost", True)
        self.attributes("-toolwindow", "True")

        self.label = customtkinter.CTkLabel(
            self,
            text="Type to enter text or use Speech Recognition",
            font=customtkinter.CTkFont(size=32),
        )
        self.text_entry = customtkinter.CTkTextbox(self)

        self.start_speech_rec_button = customtkinter.CTkButton(
            self,
            text="Start Speech Recognition",
            fg_color="#FF0000",
            hover_color="#770000",
            cursor="star",
            command=self.start_speech_rec,
        )
        self.submit_button = customtkinter.CTkButton(
            self, text="Submit Text", command=self.set_text_from_entry
        )

        self.label.pack(padx=20, pady=20)
        self.text_entry.pack(padx=20, pady=20, expand=True, fill="both")
        self.start_speech_rec_button.pack(padx=20, pady=20, expand=True, fill="both")
        self.submit_button.pack(padx=20, pady=20, expand=False, fill="x")
        self.text_entry.focus()

        self.text_entry.bind("<Return>", command=self.submit_text)

    def start_speech_rec(self):
        self.label.destroy()
        self.text_entry.destroy()
        self.start_speech_rec_button.destroy()
        self.submit_button.destroy()
        self.speech_rec_state_label = customtkinter.CTkLabel(
            self,
            text="Speech Recognition Active",
            text_color="#0000FF",
            font=customtkinter.CTkFont(size=32),
        )
        self.stop_speech_rec_button = customtkinter.CTkButton(
            self,
            text="Stop Speech Recognition",
            fg_color="#FF0000",
            hover_color="#770000",
            cursor="star",
            command=self.stop_speech_rec,
        )
        self.speech_rec_state_label.pack(padx=20, pady=20)
        self.stop_speech_rec_button.pack(padx=20, pady=20, expand=True, fill="x")

        speech_recognition_thread = threading.Thread(target=self.recognize_speech)
        speech_recognition_thread.start()

    def stop_speech_rec(self):
        self.do_stop_speech = True
        self.stop_speech_rec_button.destroy()

    def recognize_speech(self):

        model_base = Path(__file__).parent.parent / "assets/vosk-model-small-en-us-0.15"

        if not model_base.exists():
            print(f"Speech model not found at {model_base}")
            print("Please download from https://alphacephei.com/vosk/models")
            return

        speech_model = vosk.Model(str(model_base))
        rec = vosk.KaldiRecognizer(speech_model, 16000)

        # Open the microphone stream
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8192,
        )

        # Specify the path for the output text file
        output_file_path = "recognized_text.txt"

        # Open a text file in write mode using a 'with' block
        with open(output_file_path, "w") as output_file:
            # print("Listening for speech. Say 'Terminate' to stop.")
            # Start streaming and recognize speech
            while True:
                data = stream.read(4096)  # read in chunks of 4096 bytes
                if rec.AcceptWaveform(data):  # accept waveform of input voice
                    # Parse the JSON result and get the recognized text
                    result = json.loads(rec.Result())
                    recognized_text = result["text"]
                    # Check for the termination keyword
                    if (
                        "terminate" in recognized_text.lower()
                        or self.do_stop_speech
                        or not self.winfo_exists()
                    ):
                        # print("Termination keyword detected. Stopping...")
                        break

                    # Write recognized text to the file
                    output_file.write(recognized_text + "\n")
                    # print(recognized_text)

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        # Terminate the PyAudio object
        p.terminate()

        with open(output_file_path, "r") as output_file:
            self.set_text_from_speech(output_file.read())

        if os.path.exists(output_file_path):
            os.remove(output_file_path)

    def set_text_from_entry(self):
        self.text = self.text_entry.get("0.0", "end")
        self.parent.set_canvas_text(self.text)
        self.destroy()

    def submit_text(self, event):
        self.set_text_from_entry()

    def set_text_from_speech(self, recognized_text):
        self.text = recognized_text
        self.parent.set_canvas_text(self.text)
        self.destroy()

    def get_text(self):
        return self.text
