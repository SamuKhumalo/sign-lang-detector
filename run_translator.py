#run_translator.py
import os
import subprocess
import sys

MODEL_FILE = 'sign_model.pkl'
ENCODER_FILE = 'label_encoder.pkl'

def check_model():
    return os.path.exists(MODEL_FILE) and os.path.exists(ENCODER_FILE)

def run_script(script_path):
    """Run a Python script."""
    result = subprocess.run([sys.executable, script_path])
    if result.returncode != 0:
        print(f"Error running {script_path}")
        sys.exit(1)

def main():
    if not check_model():
        print("Model not found! Starting data collection and training...")
        # Step 1: Collect data
        run_script(os.path.join('models', 'data_collect.py'))
        # Step 2: Train model
        run_script(os.path.join('models', 'train_model.py'))
    else:
        print("Model found. Skipping training.")

    # Step 3: Run live detection
    run_script(os.path.join('models', 'live_detect.py'))

if __name__ == "__main__":
    main()
