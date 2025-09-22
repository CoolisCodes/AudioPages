import os
import io
import tempfile
import subprocess
import sys
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading

# Simplified package installation without playsound (which has build issues)
def install_packages():
    """Install required packages if they're not available"""
    packages = {
        'elevenlabs': 'elevenlabs',
        'pygame': 'pygame',
        'requests': 'requests',
        'PyPDF2': 'PyPDF2'  # Add PyPDF2 for PDF reading
    }
    
    for package_name, pip_name in packages.items():
        try:
            __import__(package_name)
            print(f"✅ {package_name} already installed")
        except ImportError:
            print(f"📦 Installing {package_name}...")
            try:
                # Try without --user first, then with --user if that fails
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], 
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "--user"],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"✅ {package_name} installed successfully!")
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Could not install {package_name}")

# Install packages first
print("🔧 Checking required packages...")
install_packages()

# Import pygame
PYGAME_AVAILABLE = False
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
    print("✅ pygame loaded successfully")
except ImportError:
    print("⚠️  pygame not available")
except Exception as e:
    print(f"⚠️  pygame error: {e}")

# Import elevenlabs more carefully
ELEVENLABS_AVAILABLE = False
try:
    # Import individual components to avoid recursion
    import elevenlabs
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
    print("✅ elevenlabs loaded successfully")
except ImportError as e:
    print(f"❌ elevenlabs not available: {e}")
except RecursionError:
    print("❌ elevenlabs has import issues. Please reinstall:")
    print("pip uninstall elevenlabs")
    print("pip install elevenlabs")
except Exception as e:
    print(f"❌ elevenlabs error: {e}")

# Import PyPDF2 for PDF reading
PDF_AVAILABLE = False
try:
    import PyPDF2
    PDF_AVAILABLE = True
    print("✅ PyPDF2 loaded successfully")
except ImportError:
    print("⚠️  PyPDF2 not available - PDF import disabled")
except Exception as e:
    print(f"⚠️  PyPDF2 error: {e}")

class TextToSpeechApp:
    def __init__(self):
        """Initialize the Text-to-Speech application"""
        if not ELEVENLABS_AVAILABLE:
            print("❌ ElevenLabs library is required but not available.")
            print("Please install it with: pip install elevenlabs")
            sys.exit(1)
            
        self.api_key = None
        self.client = None
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice (Rachel)
        
    def setup_api_key(self, api_key=None):
        """Set up ElevenLabs API key"""
        if api_key:
            self.api_key = api_key
        else:
            # Try to get from environment variable
            self.api_key = os.getenv('ELEVENLABS_API_KEY')
            
        if not self.api_key:
            print("\n" + "="*50)
            print("🔑 ElevenLabs API Key Required")
            print("="*50)
            print("To use this app, you need an API key from ElevenLabs:")
            print("1. Go to https://elevenlabs.io/")
            print("2. Sign up for an account")
            print("3. Go to your profile settings")
            print("4. Copy your API key")
            print("="*50)
            self.api_key = input("Please enter your ElevenLabs API Key: ").strip()
            
        if not self.api_key:
            print("❌ No API key provided. Exiting.")
            sys.exit(1)
            
        try:
            self.client = ElevenLabs(api_key=self.api_key)
            print("✅ API key configured successfully!")
        except Exception as e:
            print(f"❌ Error setting API key: {e}")
            sys.exit(1)
        
    def list_available_voices(self):
        """List available voices from ElevenLabs"""
        try:
            response = self.client.voices.get_all()
            available_voices = response.voices
            
            print("\n🎤 Available Voices:")
            print("-" * 40)
            for i, voice in enumerate(available_voices, 1):
                print(f"{i}. {voice.name} (ID: {voice.voice_id})")
                if hasattr(voice, 'labels') and voice.labels:
                    print(f"   Labels: {', '.join(voice.labels.values())}")
                print()
                
            return available_voices
        except Exception as e:
            print(f"❌ Error fetching voices: {e}")
            print("This might be due to:")
            print("- Invalid API key")
            print("- Network connection issues")
            print("- ElevenLabs service unavailable")
            return []
            
    def select_voice(self):
        """Allow user to select a voice"""
        voices = self.list_available_voices()
        if not voices:
            print("Using default voice...")
            return
            
        try:
            choice = input("Select a voice number (or press Enter for default): ").strip()
            if choice and choice.isdigit():
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(voices):
                    self.voice_id = voices[choice_idx].voice_id
                    print(f"✅ Selected voice: {voices[choice_idx].name}")
                else:
                    print("Invalid choice. Using default voice.")
            else:
                print("Using default voice...")
        except Exception as e:
            print(f"❌ Error selecting voice: {e}")
            print("Using default voice...")
            
    def generate_speech(self, text, stability=0.5, similarity_boost=0.8, style=0.0, use_speaker_boost=True):
        """Generate speech from text using ElevenLabs"""
        try:
            print("🔄 Generating speech...")
            
            # Use the correct client API method
            audio = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                voice_settings={
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": use_speaker_boost
                }
            )
            
            # Convert generator to bytes
            audio_bytes = b''.join(audio)
            
            print("✅ Speech generated successfully!")
            return audio_bytes
            
        except Exception as e:
            print(f"❌ Error generating speech: {e}")
            # Try alternative API method
            try:
                print("🔄 Trying alternative API method...")
                
                # Alternative method using direct API call
                import requests
                
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": self.api_key
                }
                
                data = {
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": stability,
                        "similarity_boost": similarity_boost,
                        "style": style,
                        "use_speaker_boost": use_speaker_boost
                    }
                }
                
                response = requests.post(url, json=data, headers=headers)
                
                if response.status_code == 200:
                    print("✅ Speech generated successfully!")
                    return response.content
                else:
                    print(f"❌ API Error: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
            except Exception as e2:
                print(f"❌ Alternative method failed: {e2}")
                return None

    def play_audio(self, audio_data):
        """Play the generated audio using available methods"""
        try:
            # Create a temporary file to store audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
                
            print("🔊 Playing audio...")
            
            # Try different playback methods
            if PYGAME_AVAILABLE:
                self._play_with_pygame(temp_file_path)
            else:
                self._play_with_system(temp_file_path)
                
            # Clean up temporary file after a short delay
            time.sleep(1)
            try:
                os.unlink(temp_file_path)
            except:
                pass  # File might still be in use
                
            print("✅ Audio playback completed!")
            
        except Exception as e:
            print(f"❌ Error playing audio: {e}")
            
    def _play_with_pygame(self, file_path):
        """Play audio using pygame"""
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        # Wait for audio to finish playing
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
            
    def _play_with_system(self, file_path):
        """Play audio using system commands"""
        import platform
        system = platform.system()
        
        try:
            if system == "Windows":
                os.system(f'start "" "{file_path}"')
                time.sleep(3)  # Give time for playback
            elif system == "Darwin":  # macOS
                subprocess.run(['afplay', file_path])
            elif system == "Linux":
                # Try different Linux audio players
                players = ['mpg123', 'mpv', 'vlc', 'mplayer', 'aplay']
                for player in players:
                    try:
                        if subprocess.run(['which', player], capture_output=True).returncode == 0:
                            subprocess.run([player, file_path])
                            return
                    except:
                        continue
                # If no player found, try xdg-open
                try:
                    subprocess.run(['xdg-open', file_path])
                    time.sleep(3)  # Give time for playback
                except:
                    print(f"💾 Audio saved to: {file_path} (no audio player found)")
            else:
                print(f"❌ Unsupported system: {system}")
                print(f"💾 Audio saved to: {file_path}")
        except Exception as e:
            print(f"❌ System playback failed: {e}")
            print(f"💾 Audio saved to: {file_path}")

    def save_audio(self, audio_data, filename=None):
        """Save the generated audio to a file"""
        try:
            if not filename:
                import time
                timestamp = int(time.time())
                filename = f"generated_speech_{timestamp}.mp3"
                
            with open(filename, 'wb') as f:
                f.write(audio_data)
                
            print(f"💾 Audio saved as: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error saving audio: {e}")
            return None
            
    def adjust_voice_settings(self):
        """Allow user to adjust voice settings"""
        print("\n🎛️  Voice Settings (press Enter to keep current value):")
        
        try:
            stability = input("Stability (0.0-1.0, default 0.5): ").strip()
            stability = float(stability) if stability else 0.5
            
            similarity = input("Similarity Boost (0.0-1.0, default 0.8): ").strip()
            similarity = float(similarity) if similarity else 0.8
            
            style = input("Style (0.0-1.0, default 0.0): ").strip()
            style = float(style) if style else 0.0
            
            speaker_boost = input("Use Speaker Boost? (y/n, default y): ").strip().lower()
            speaker_boost = speaker_boost != 'n'
            
            return stability, similarity, style, speaker_boost
            
        except ValueError:
            print("❌ Invalid input. Using default settings.")
            return 0.5, 0.8, 0.0, True
            
    def run(self):
        """Main application loop"""
        print("=" * 50)
        print("🎤 ElevenLabs Text-to-Speech Application")
        print("=" * 50)
        
        # Setup API key
        self.setup_api_key()
        
        # Select voice
        self.select_voice()
        
        # Main loop
        while True:
            print("\n" + "=" * 50)
            print("📝 Text-to-Speech Menu")
            print("=" * 50)
            print("1. Convert text to speech")
            print("2. Change voice")
            print("3. Adjust voice settings")
            print("4. List available voices")
            print("5. Exit")
            
            choice = input("\nSelect an option (1-5): ").strip()
            
            if choice == '1':
                text = input("\n📝 Enter the text to convert to speech:\n> ").strip()
                
                if not text:
                    print("❌ No text provided!")
                    continue
                    
                # Get voice settings
                print("\nUse custom settings? (y/n, default n): ", end="")
                use_custom = input().strip().lower() == 'y'
                
                if use_custom:
                    stability, similarity, style, speaker_boost = self.adjust_voice_settings()
                else:
                    stability, similarity, style, speaker_boost = 0.5, 0.8, 0.0, True
                
                # Generate speech
                audio_data = self.generate_speech(text, stability, similarity, style, speaker_boost)
                
                if audio_data:
                    # Ask what to do with the audio
                    print("\nWhat would you like to do with the generated audio?")
                    print("1. Play audio")
                    print("2. Save audio to file")
                    print("3. Play and save audio")
                    
                    audio_choice = input("Select option (1-3): ").strip()
                    
                    if audio_choice in ['1', '3']:
                        self.play_audio(audio_data)
                        
                    if audio_choice in ['2', '3']:
                        filename = input("Enter filename (or press Enter for auto-generated): ").strip()
                        filename = filename if filename else None
                        self.save_audio(audio_data, filename)
                        
            elif choice == '2':
                self.select_voice()
                
            elif choice == '3':
                print("\n🎛️  Current voice settings will be used for next generation.")
                
            elif choice == '4':
                self.list_available_voices()
                
            elif choice == '5':
                print("👋 Thank you for using ElevenLabs Text-to-Speech!")
                break
                
            else:
                print("❌ Invalid option. Please try again.")

class TextToSpeechGUI:
    def __init__(self, root):
        """Initialize the GUI application"""
        self.root = root
        self.root.title("🎤 ElevenLabs Text-to-Speech")
        self.root.geometry("800x700")
        self.root.configure(bg="#2c3e50")
        
        # Initialize the backend app
        if not ELEVENLABS_AVAILABLE:
            messagebox.showerror("Error", "ElevenLabs library is not available!\nPlease install it with: pip install elevenlabs")
            sys.exit(1)
            
        self.app = TextToSpeechApp()
        self.current_audio = None
        
        # Create GUI components
        self.create_widgets()
        self.setup_api_key()
        
    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Main frame
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="🎤 ElevenLabs Text-to-Speech", 
                              font=("Arial", 24, "bold"), fg="#ecf0f1", bg="#2c3e50")
        title_label.pack(pady=(0, 20))
        
        # API Key Frame
        api_frame = tk.LabelFrame(main_frame, text="API Configuration", 
                                 font=("Arial", 12, "bold"), fg="#ecf0f1", bg="#34495e")
        api_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(api_frame, text="API Key:", font=("Arial", 10), 
                fg="#ecf0f1", bg="#34495e").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.api_key_var = tk.StringVar()
        self.api_entry = tk.Entry(api_frame, textvariable=self.api_key_var, show="*", 
                                 font=("Arial", 10), width=40)
        self.api_entry.grid(row=0, column=1, padx=10, pady=5)
        
        self.api_button = tk.Button(api_frame, text="Set API Key", command=self.set_api_key,
                                   bg="#3498db", fg="white", font=("Arial", 10, "bold"))
        self.api_button.grid(row=0, column=2, padx=10, pady=5)
        
        # Voice Selection Frame
        voice_frame = tk.LabelFrame(main_frame, text="Voice Selection", 
                                   font=("Arial", 12, "bold"), fg="#ecf0f1", bg="#34495e")
        voice_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(voice_frame, text="Voice:", font=("Arial", 10), 
                fg="#ecf0f1", bg="#34495e").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.voice_var = tk.StringVar()
        self.voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var, 
                                       font=("Arial", 10), width=30, state="readonly")
        self.voice_combo.grid(row=0, column=1, padx=10, pady=5)
        
        self.refresh_voices_btn = tk.Button(voice_frame, text="Refresh Voices", 
                                           command=self.refresh_voices,
                                           bg="#27ae60", fg="white", font=("Arial", 10, "bold"))
        self.refresh_voices_btn.grid(row=0, column=2, padx=10, pady=5)
        
        # Voice Settings Frame
        settings_frame = tk.LabelFrame(main_frame, text="Voice Settings", 
                                      font=("Arial", 12, "bold"), fg="#ecf0f1", bg="#34495e")
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Stability
        tk.Label(settings_frame, text="Stability:", font=("Arial", 10), 
                fg="#ecf0f1", bg="#34495e").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.stability_var = tk.DoubleVar(value=0.5)
        self.stability_scale = tk.Scale(settings_frame, from_=0.0, to=1.0, resolution=0.1,
                                       orient=tk.HORIZONTAL, variable=self.stability_var,
                                       bg="#34495e", fg="#ecf0f1", length=150)
        self.stability_scale.grid(row=0, column=1, padx=10, pady=5)
        
        # Similarity Boost
        tk.Label(settings_frame, text="Similarity:", font=("Arial", 10), 
                fg="#ecf0f1", bg="#34495e").grid(row=0, column=2, sticky="w", padx=10, pady=5)
        self.similarity_var = tk.DoubleVar(value=0.8)
        self.similarity_scale = tk.Scale(settings_frame, from_=0.0, to=1.0, resolution=0.1,
                                        orient=tk.HORIZONTAL, variable=self.similarity_var,
                                        bg="#34495e", fg="#ecf0f1", length=150)
        self.similarity_scale.grid(row=0, column=3, padx=10, pady=5)
        
        # Style
        tk.Label(settings_frame, text="Style:", font=("Arial", 10), 
                fg="#ecf0f1", bg="#34495e").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.style_var = tk.DoubleVar(value=0.0)
        self.style_scale = tk.Scale(settings_frame, from_=0.0, to=1.0, resolution=0.1,
                                   orient=tk.HORIZONTAL, variable=self.style_var,
                                   bg="#34495e", fg="#ecf0f1", length=150)
        self.style_scale.grid(row=1, column=1, padx=10, pady=5)
        
        # Speaker Boost
        self.speaker_boost_var = tk.BooleanVar(value=True)
        self.speaker_boost_check = tk.Checkbutton(settings_frame, text="Speaker Boost",
                                                 variable=self.speaker_boost_var,
                                                 font=("Arial", 10), fg="#ecf0f1", bg="#34495e",
                                                 selectcolor="#34495e")
        self.speaker_boost_check.grid(row=1, column=2, padx=10, pady=5, sticky="w")
        
        # Text Input Frame
        text_frame = tk.LabelFrame(main_frame, text="Text Input", 
                                  font=("Arial", 12, "bold"), fg="#ecf0f1", bg="#34495e")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # File import buttons frame
        import_frame = tk.Frame(text_frame, bg="#34495e")
        import_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        self.import_pdf_btn = tk.Button(import_frame, text="📄 Import PDF", 
                                       command=self.import_pdf,
                                       bg="#16a085", fg="white", font=("Arial", 10, "bold"),
                                       state=tk.NORMAL if PDF_AVAILABLE else tk.DISABLED)
        self.import_pdf_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.import_txt_btn = tk.Button(import_frame, text="📝 Import Text File", 
                                       command=self.import_text_file,
                                       bg="#2980b9", fg="white", font=("Arial", 10, "bold"))
        self.import_txt_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_text_btn = tk.Button(import_frame, text="🗑️ Clear Text", 
                                       command=self.clear_text,
                                       bg="#c0392b", fg="white", font=("Arial", 10, "bold"))
        self.clear_text_btn.pack(side=tk.LEFT)
        
        # Character count label
        self.char_count_var = tk.StringVar(value="Characters: 0")
        self.char_count_label = tk.Label(import_frame, textvariable=self.char_count_var,
                                        font=("Arial", 9), fg="#95a5a6", bg="#34495e")
        self.char_count_label.pack(side=tk.RIGHT)
        
        self.text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, 
                                                  font=("Arial", 11), height=8,
                                                  bg="#ecf0f1", fg="#2c3e50")
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # Bind text change event for character count
        self.text_area.bind('<KeyRelease>', self.update_char_count)
        self.text_area.bind('<Button-1>', self.update_char_count)
        
        # Control Buttons Frame
        control_frame = tk.Frame(main_frame, bg="#2c3e50")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.generate_btn = tk.Button(control_frame, text="🎵 Generate Speech", 
                                     command=self.generate_speech_threaded,
                                     bg="#e74c3c", fg="white", font=("Arial", 12, "bold"),
                                     height=2, width=15)
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.play_btn = tk.Button(control_frame, text="▶️ Play Audio", 
                                 command=self.play_audio,
                                 bg="#9b59b6", fg="white", font=("Arial", 12, "bold"),
                                 height=2, width=15, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_btn = tk.Button(control_frame, text="💾 Save Audio", 
                                 command=self.save_audio,
                                 bg="#f39c12", fg="white", font=("Arial", 12, "bold"),
                                 height=2, width=15, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Add Read PDF button
        self.read_pdf_btn = tk.Button(control_frame, text="📖 Read PDF Aloud", 
                                     command=self.read_pdf_aloud,
                                     bg="#8e44ad", fg="white", font=("Arial", 12, "bold"),
                                     height=2, width=15, state=tk.DISABLED)
        self.read_pdf_btn.pack(side=tk.LEFT)
        
        # Status Frame
        status_frame = tk.Frame(main_frame, bg="#2c3e50")
        status_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready to generate speech...")
        self.status_label = tk.Label(status_frame, textvariable=self.status_var,
                                    font=("Arial", 10), fg="#95a5a6", bg="#2c3e50",
                                    anchor="w")
        self.status_label.pack(fill=tk.X)
        
        # Progress Bar
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(5, 0))
        
    def setup_api_key(self):
        """Setup API key from environment or prompt user"""
        env_key = os.getenv('ELEVENLABS_API_KEY')
        if env_key:
            self.api_key_var.set(env_key)
            self.set_api_key()
    
    def set_api_key(self):
        """Set the API key and initialize client"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter your ElevenLabs API key")
            return
            
        try:
            self.app.setup_api_key(api_key)
            self.status_var.set("✅ API key configured successfully!")
            self.refresh_voices()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set API key: {e}")
            self.status_var.set("❌ Failed to configure API key")
    
    def refresh_voices(self):
        """Refresh the voice list"""
        def refresh_thread():
            try:
                self.status_var.set("🔄 Loading voices...")
                self.progress.start()
                
                voices = self.app.list_available_voices()
                
                self.root.after(0, lambda: self.update_voice_list(voices))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load voices: {e}"))
            finally:
                self.root.after(0, lambda: self.progress.stop())
        
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def update_voice_list(self, voices):
        """Update the voice combobox with available voices"""
        if voices:
            voice_names = [f"{voice.name} ({voice.voice_id[:8]}...)" for voice in voices]
            self.voice_combo['values'] = voice_names
            self.voice_combo.current(0)
            
            # Store voice mapping
            self.voice_mapping = {voice_names[i]: voices[i].voice_id for i in range(len(voices))}
            
            self.status_var.set(f"✅ Loaded {len(voices)} voices")
        else:
            self.status_var.set("❌ No voices available")
    
    def generate_speech_threaded(self):
        """Generate speech in a separate thread"""
        text = self.text_area.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter some text to convert to speech")
            return
        
        if not hasattr(self.app, 'client') or not self.app.client:
            messagebox.showerror("Error", "Please set your API key first")
            return
        
        def generate_thread():
            try:
                self.root.after(0, lambda: self.progress.start())
                self.root.after(0, lambda: self.status_var.set("🔄 Generating speech..."))
                self.root.after(0, lambda: self.generate_btn.config(state=tk.DISABLED))
                
                # Get selected voice ID
                selected_voice = self.voice_var.get()
                if selected_voice and hasattr(self, 'voice_mapping'):
                    self.app.voice_id = self.voice_mapping[selected_voice]
                
                # Generate speech
                audio_data = self.app.generate_speech(
                    text,
                    stability=self.stability_var.get(),
                    similarity_boost=self.similarity_var.get(),
                    style=self.style_var.get(),
                    use_speaker_boost=self.speaker_boost_var.get()
                )
                
                if audio_data:
                    self.current_audio = audio_data
                    self.root.after(0, lambda: self.status_var.set("✅ Speech generated successfully!"))
                    self.root.after(0, lambda: self.play_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.save_btn.config(state=tk.NORMAL))
                else:
                    self.root.after(0, lambda: self.status_var.set("❌ Failed to generate speech"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to generate speech: {e}"))
                self.root.after(0, lambda: self.status_var.set("❌ Generation failed"))
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))
        
        threading.Thread(target=generate_thread, daemon=True).start()
    
    def play_audio(self):
        """Play the generated audio"""
        if not self.current_audio:
            messagebox.showwarning("Warning", "No audio to play. Generate speech first.")
            return
        
        def play_thread():
            try:
                self.root.after(0, lambda: self.status_var.set("🔊 Playing audio..."))
                self.app.play_audio(self.current_audio)
                self.root.after(0, lambda: self.status_var.set("✅ Audio playback completed!"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to play audio: {e}"))
                self.root.after(0, lambda: self.status_var.set("❌ Playback failed"))
        
        threading.Thread(target=play_thread, daemon=True).start()
    
    def save_audio(self):
        """Save the generated audio to a file"""
        if not self.current_audio:
            messagebox.showwarning("Warning", "No audio to save. Generate speech first.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")],
            title="Save Audio File"
        )
        
        if filename:
            try:
                self.app.save_audio(self.current_audio, filename)
                self.status_var.set(f"💾 Audio saved as: {filename}")
                messagebox.showinfo("Success", f"Audio saved successfully!\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save audio: {e}")
                self.status_var.set("❌ Save failed")
    
    def update_char_count(self, event=None):
        """Update character count display"""
        text = self.text_area.get("1.0", tk.END).strip()
        char_count = len(text)
        self.char_count_var.set(f"Characters: {char_count}")
        
        # Enable/disable Read PDF button based on text content
        if char_count > 0:
            self.read_pdf_btn.config(state=tk.NORMAL)
        else:
            self.read_pdf_btn.config(state=tk.DISABLED)
    
    def import_pdf(self):
        """Import and extract text from PDF file"""
        if not PDF_AVAILABLE:
            messagebox.showerror("Error", "PyPDF2 is not available.\nPlease install it with: pip install PyPDF2")
            return
        
        filename = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            def import_thread():
                try:
                    self.root.after(0, lambda: self.progress.start())
                    self.root.after(0, lambda: self.status_var.set("📄 Reading PDF file..."))
                    self.root.after(0, lambda: self.import_pdf_btn.config(state=tk.DISABLED))
                    
                    # Extract text from PDF
                    text = self.app.extract_text_from_pdf(filename)
                    
                    # Update text area in main thread
                    self.root.after(0, lambda: self.text_area.delete("1.0", tk.END))
                    self.root.after(0, lambda: self.text_area.insert("1.0", text))
                    self.root.after(0, lambda: self.update_char_count())
                    self.root.after(0, lambda: self.status_var.set(f"✅ PDF imported successfully! ({len(text)} characters)"))
                    
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to import PDF:\n{e}"))
                    self.root.after(0, lambda: self.status_var.set("❌ PDF import failed"))
                finally:
                    self.root.after(0, lambda: self.progress.stop())
                    self.root.after(0, lambda: self.import_pdf_btn.config(state=tk.NORMAL))
            
            threading.Thread(target=import_thread, daemon=True).start()
    
    def import_text_file(self):
        """Import text from a plain text file"""
        filename = filedialog.askopenfilename(
            title="Select Text File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    text = file.read()
                    self.text_area.delete("1.0", tk.END)
                    self.text_area.insert("1.0", text)
                    self.update_char_count()
                    self.status_var.set(f"✅ Text file imported successfully! ({len(text)} characters)")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import text file:\n{e}")
                self.status_var.set("❌ Text file import failed")
    
    def clear_text(self):
        """Clear the text area"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all text?"):
            self.text_area.delete("1.0", tk.END)
            self.update_char_count()
            self.status_var.set("🗑️ Text cleared")
    
    def read_pdf_aloud(self):
        """Generate speech and play immediately for PDF content"""
        text = self.text_area.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "No text to read. Import a PDF first.")
            return
        
        if not hasattr(self.app, 'client') or not self.app.client:
            messagebox.showerror("Error", "Please set your API key first")
            return
        
        # Ask user if they want to read the entire document or just a portion
        if len(text) > 5000:  # If text is long
            choice = messagebox.askyesnocancel(
                "Long Document", 
                f"This document has {len(text)} characters.\n\n"
                "Yes: Read entire document\n"
                "No: Read first 5000 characters\n"
                "Cancel: Don't read"
            )
            if choice is None:  # Cancel
                return
            elif choice is False:  # Read first 5000 chars
                text = text[:5000] + "... [Document truncated for audio generation]"
        
        def read_thread():
            try:
                self.root.after(0, lambda: self.progress.start())
                self.root.after(0, lambda: self.status_var.set("🔄 Generating speech from document..."))
                self.root.after(0, lambda: self.read_pdf_btn.config(state=tk.DISABLED))
                self.root.after(0, lambda: self.generate_btn.config(state=tk.DISABLED))
                
                # Get selected voice ID
                selected_voice = self.voice_var.get()
                if selected_voice and hasattr(self, 'voice_mapping'):
                    self.app.voice_id = self.voice_mapping[selected_voice]
                
                # Generate speech
                audio_data = self.app.generate_speech(
                    text,
                    stability=self.stability_var.get(),
                    similarity_boost=self.similarity_var.get(),
                    style=self.style_var.get(),
                    use_speaker_boost=self.speaker_boost_var.get()
                )
                
                if audio_data:
                    self.current_audio = audio_data
                    self.root.after(0, lambda: self.status_var.set("🔊 Playing document audio..."))
                    self.root.after(0, lambda: self.play_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.save_btn.config(state=tk.NORMAL))
                    
                    # Auto-play the generated audio
                    self.app.play_audio(audio_data)
                    self.root.after(0, lambda: self.status_var.set("✅ Document reading completed!"))
                else:
                    self.root.after(0, lambda: self.status_var.set("❌ Failed to generate speech"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to read document: {e}"))
                self.root.after(0, lambda: self.status_var.set("❌ Document reading failed"))
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.read_pdf_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))
        
        threading.Thread(target=read_thread, daemon=True).start()

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file"""
        if not PDF_AVAILABLE:
            raise Exception("PyPDF2 not available. Cannot read PDF files.")
        
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                print(f"📄 Reading PDF with {len(pdf_reader.pages)} pages...")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text += f"\n--- Page {page_num} ---\n"
                            text += page_text + "\n"
                        print(f"✅ Extracted page {page_num}")
                    except Exception as e:
                        print(f"⚠️  Error reading page {page_num}: {e}")
                        continue
                
            if not text.strip():
                raise Exception("No text could be extracted from the PDF")
                
            print(f"✅ Successfully extracted {len(text)} characters from PDF")
            return text.strip()
            
        except Exception as e:
            raise Exception(f"Error reading PDF: {e}")

def main():
    """Main function to run the application"""
    if not ELEVENLABS_AVAILABLE:
        print("❌ Cannot start application: ElevenLabs library not available")
        print("\nTo fix this:")
        print("1. pip uninstall elevenlabs")
        print("2. pip install elevenlabs")
        print("3. Restart your terminal/IDE")
        return
        
    try:
        app = TextToSpeechApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        print("Please check your internet connection and API key.")

def run_gui():
    """Run the GUI application"""
    root = tk.Tk()
    app_gui = TextToSpeechGUI(root)
    root.mainloop()

if __name__ == "__main__":
    print("🎤 ElevenLabs Text-to-Speech Application")
    print("=" * 50)
    
    if not ELEVENLABS_AVAILABLE:
        print("❌ ElevenLabs library not found or has issues!")
        print("\nTo fix this:")
        print("pip uninstall elevenlabs")
        print("pip install elevenlabs")
        print("\nThen restart this application.")
        sys.exit(1)
    
    # Ask user to choose interface
    print("Choose interface:")
    print("1. GUI (Graphical User Interface)")
    print("2. CLI (Command Line Interface)")
    
    choice = input("\nSelect interface (1 or 2, default 1): ").strip()
    
    if choice == '2':
        # Run CLI version
        if PYGAME_AVAILABLE:
            print("✅ pygame available for audio playback")
        else:
            print("⚠️  Using system audio player")
        
        print("\nMake sure to:")
        print("1. Sign up at https://elevenlabs.io/")
        print("2. Get your API key from the dashboard")
        print("3. Set it as environment variable: ELEVENLABS_API_KEY")
        print("\n" + "="*50)
        
        main()
    else:
        # Run GUI version
        print("🖥️  Starting GUI interface...")
        run_gui()

