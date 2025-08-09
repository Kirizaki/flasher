# Mic Beat Flash

A real-time microphone beat detector that flashes the screen on detected beats.  
Includes adjustable microphone **Gain** (UP/DOWN arrows) and **Sensitivity** (LEFT/RIGHT arrows) with on-screen bars and numeric values.  
Optimized for loud environments (e.g., rehearsal studios, live rooms) using logarithmic gain control.

## Features
- Real-time audio input from your microphone
- Simple RMS-based beat detection
- Adjustable microphone **Gain** in dB
- Adjustable beat detection **Sensitivity** multiplier
- On-screen bars and numeric readouts for gain and sensitivity
- Bars auto-hide after 2 seconds of no changes
- Low-latency flashing using `pygame`

## Controls
| Key           | Action                              |
|---------------|-------------------------------------|
| **↑ Up**      | Increase gain (dB)                  |
| **↓ Down**    | Decrease gain (dB)                  |
| **→ Right**   | Increase sensitivity multiplier     |
| **← Left**    | Decrease sensitivity multiplier     |
| **ESC**       | Quit the app                        |

## Requirements
- Python 3.8+
- A working microphone input
- Installed dependencies from `requirements.txt`

## Installation
```bash
git clone https://github.com/yourusername/flasher.git
cd flasher
pip install -r requirements.txt
