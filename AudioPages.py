import os
import io
import tempfile
import subprocess
import sys
import time

# Simplified package installation without playsound (which has build issues)
def install_packages():
    """Install required packages if they're not available"""
    packages = {
        'elevenlabs': 'elevenlabs',
        'pygame': 'pygame',
        'requests': 'requests'  # Add requests as backup
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
    
    # Check audio playback options
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

