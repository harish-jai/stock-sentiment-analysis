import subprocess

# Run wrapper.py
subprocess.run(["python3", "wrapper.py"])

# Run preprocess_reddit.py
subprocess.run(["python3", "preprocess_reddit.py"])

# Run sentiment_analyzer.py
subprocess.run(["python3", "sentiment_analyzer.py"])
