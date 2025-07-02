from flask import Flask, render_template, Response
import subprocess
import time
import os

app = Flask(__name__)

# Route to render the main page
@app.route("/")
def index():
    return render_template("index.html")

# Route to run main1.py and stream logs
@app.route("/run_script")
def run_script():
    def generate():
        # Set the path to Python and make the output unbuffered for real-time logs
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        # Run main1.py as a subprocess using the full Python path
        process = subprocess.Popen(
            ["python", "main1.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env
        )

        # Stream the output line by line
        for line in iter(process.stdout.readline, ''):
            yield f"data:{line.strip()}\n\n"
            time.sleep(0.1)  # Slight delay for smoother streaming

        process.stdout.close()
        process.wait()

    return Response(generate(), mimetype="text/event-stream")



