# CreativeAct Ollama Mobile - Termux Quickstart Guide

Get **CreativeAct Ollama Mobile** running on your Android device via Termux in under 5 minutes.

---

## Step 1: Install Termux
1. Download and install **Termux** from [F-Droid](https://f-droid.org/packages/com.termux/) (recommended) rather than the Google Play Store.
2. Open Termux and update package lists:
   ```bash
   pkg update && pkg upgrade -y
   ```

---

## Step 2: Install Python & Git
Install Python 3, Git, and build essentials:
```bash
pkg install -y python git clang make libffi openssl
```

---

## Step 3: Install Dependencies
Navigate to the project directory and install required Python packages:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
*(Or run `bash termux_setup.sh`)*

---

## Step 4: Start Ollama
In a separate Termux session, start your local Ollama server:
```bash
ollama serve
```

---

## Step 5: Run the App
```bash
python creative_act_ollama.py
```
