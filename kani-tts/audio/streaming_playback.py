"""Streaming audio writer with real-time playback"""

import threading
import queue
import numpy as np
from scipy.io.wavfile import write
import sounddevice as sd

from config import SAMPLE_RATE, CHUNK_SIZE, LOOKBACK_FRAMES


class StreamingAudioPlayerWriter:
    def __init__(self, player, output_file, sample_rate=SAMPLE_RATE,
                 chunk_size=CHUNK_SIZE, lookback_frames=LOOKBACK_FRAMES,
                 enable_playback=True):
        """
        Sliding window decoder with lookback context and real-time playback.

        Args:
            player: LLMAudioPlayer instance
            output_file: Output WAV file path
            sample_rate: Audio sample rate (22050 Hz for nanocodec)
            chunk_size: Number of NEW frames to output per iteration
            lookback_frames: Number of frames to include from previous context for continuity
            enable_playback: Enable real-time audio playback (default: True)
        """
        self.player = player
        self.output_file = output_file
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.lookback_frames = lookback_frames
        self.enable_playback = enable_playback

        self.token_queue = queue.Queue()
        self.playback_queue = queue.Queue()
        self.audio_chunks = []
        self.running = True
        self.inside_speech = False
        self.audio_token_buffer = []
        self.all_tokens = []
        self.frames_decoded = 0

        # Audio playback stream
        self.stream = None
        if self.enable_playback:
            self._setup_audio_stream()

    def _setup_audio_stream(self):
        """Setup audio output stream for real-time playback"""
        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                callback=self._audio_callback,
                blocksize=0  # Use optimal block size
            )
            self.stream.start()
            print(f"[PLAYBACK] Audio stream initialized (sample rate: {self.sample_rate} Hz)")
        except Exception as e:
            print(f"[PLAYBACK] Warning: Failed to initialize audio stream: {e}")
            print(f"[PLAYBACK] Continuing without real-time playback")
            self.enable_playback = False
            self.stream = None

    def _audio_callback(self, outdata, frames, time, status):
        """Audio stream callback for real-time playback"""
        if status:
            print(f"[PLAYBACK] Status: {status}")

        try:
            # Get audio chunk from playback queue (non-blocking)
            chunk = self.playback_queue.get_nowait()

            # Fill output buffer
            if len(chunk) <= frames:
                outdata[:len(chunk)] = chunk.reshape(-1, 1)
                outdata[len(chunk):] = 0  # Silence for remaining
            else:
                outdata[:] = chunk[:frames].reshape(-1, 1)
                # Put remaining back in queue
                remaining = chunk[frames:]
                self.playback_queue.put(remaining)

        except queue.Empty:
            # No audio available, output silence
            outdata[:] = 0

    def decoder_worker(self):
        """Background thread that decodes audio chunks as they arrive"""
        speech_ended = False

        while self.running or not self.token_queue.empty():
            try:
                token_id = self.token_queue.get(timeout=0.1)

                # Check for start/end of speech markers
                if token_id == self.player.start_of_speech:
                    print(f"[DECODER] START_OF_SPEECH detected")
                    self.inside_speech = True
                    speech_ended = False
                    self.audio_token_buffer = []
                    continue

                if token_id == self.player.end_of_speech:
                    if speech_ended:
                        print(f"[DECODER] Warning: Duplicate END_OF_SPEECH detected, ignoring")
                        continue

                    print(f"[DECODER] END_OF_SPEECH detected")

                    # Decode any remaining frames with sliding window
                    total_frames = len(self.all_tokens) // 4
                    remaining_frames = total_frames - self.frames_decoded

                    if remaining_frames >= 1:
                        # Decode from lookback point to end
                        start_frame = max(0, self.frames_decoded - self.lookback_frames)
                        start_token = start_frame * 4

                        tokens_to_decode = self.all_tokens[start_token:]
                        num_frames = len(tokens_to_decode) // 4

                        if num_frames > 0:
                            codes = np.array(tokens_to_decode[:num_frames * 4]).reshape(-1, 4)
                            audio_chunk = self.player.decode_audio_chunk(codes)

                            if audio_chunk is not None:
                                samples_per_frame = len(audio_chunk) // num_frames

                                # Skip lookback portion, only save new frames
                                lookback_skip = min(self.frames_decoded, self.lookback_frames)
                                skip_samples = lookback_skip * samples_per_frame
                                new_audio = audio_chunk[skip_samples:]

                                self.audio_chunks.append(new_audio)

                                # Add to playback queue for real-time playback
                                if self.enable_playback and self.stream:
                                    self.playback_queue.put(new_audio.copy())

                                print(f"[DECODER] Final chunk: {remaining_frames} frames ({remaining_frames/12.5:.2f}s audio)")

                    self.inside_speech = False
                    speech_ended = True
                    self.audio_token_buffer = []
                    continue

                # Accumulate audio tokens (only if speech hasn't ended)
                if self.inside_speech and not speech_ended:
                    self.audio_token_buffer.append(token_id)
                    self.all_tokens.append(token_id)

                    # Decode when we have enough NEW frames to process
                    total_frames = len(self.all_tokens) // 4
                    new_frames = total_frames - self.frames_decoded

                    if new_frames >= self.chunk_size:
                        # Calculate sliding window: include lookback_frames from previous context
                        start_frame = max(0, self.frames_decoded - self.lookback_frames)
                        start_token = start_frame * 4

                        # Decode from start_frame to current end
                        tokens_to_decode = self.all_tokens[start_token:]
                        num_frames = len(tokens_to_decode) // 4

                        codes = np.array(tokens_to_decode[:num_frames * 4]).reshape(-1, 4)
                        audio_chunk = self.player.decode_audio_chunk(codes)

                        if audio_chunk is not None:
                            samples_per_frame = len(audio_chunk) // num_frames

                            # Skip the lookback portion - only save the NEW frames
                            lookback_skip = min(self.frames_decoded, self.lookback_frames)
                            skip_samples = lookback_skip * samples_per_frame

                            # Extract only the new chunk_size frames worth of audio
                            new_samples = self.chunk_size * samples_per_frame
                            new_audio = audio_chunk[skip_samples:skip_samples + new_samples]

                            self.audio_chunks.append(new_audio)
                            self.frames_decoded += self.chunk_size

                            # Add to playback queue for real-time playback
                            if self.enable_playback and self.stream:
                                self.playback_queue.put(new_audio.copy())
                                print(f"[PLAYBACK] Queued {self.chunk_size} frames ({self.chunk_size/12.5:.2f}s audio) for playback")

                            print(f"[DECODER] Decoded {self.chunk_size} frames ({self.chunk_size/12.5:.2f}s audio) with {self.lookback_frames}-frame lookback context")

                        # Clear buffer (we've stored everything in all_tokens)
                        self.audio_token_buffer = []

            except queue.Empty:
                continue

    def add_token(self, token_id):
        """Add a token to the processing queue"""
        self.token_queue.put(token_id)

    def finalize(self):
        """Stop the decoder thread and write final audio file"""
        self.running = False
        self.decoder_thread.join()

        # Wait for playback to finish
        if self.enable_playback and self.stream:
            print("[PLAYBACK] Waiting for audio playback to finish...")
            # Wait until playback queue is empty
            while not self.playback_queue.empty():
                import time
                time.sleep(0.1)

            # Stop and close stream
            self.stream.stop()
            self.stream.close()
            print("[PLAYBACK] Audio playback finished")

        if self.audio_chunks:
            # Concatenate all audio chunks
            full_audio = np.concatenate(self.audio_chunks)

            # Only write to file if output_file is specified
            if self.output_file:
                write(self.output_file, self.sample_rate, full_audio)
                print(f"[WRITER] Wrote {len(full_audio)/self.sample_rate:.2f}s of audio to {self.output_file}")

            return full_audio
        return None

    def start(self):
        """Start the decoder thread"""
        self.decoder_thread = threading.Thread(target=self.decoder_worker)
        self.decoder_thread.start()
