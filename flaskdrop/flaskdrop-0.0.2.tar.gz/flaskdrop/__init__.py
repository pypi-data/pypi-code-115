import os
import socket

from flask import Flask, render_template_string, request
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "."

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://unpkg.com/dropzone@5/dist/min/dropzone.min.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/dropzone@5/dist/min/dropzone.min.css" type="text/css" />
    <title>Document</title>
  </head>
  <style>
  body {
    text-align: center;
    background-color: #B0BEC5;
    font-family: sans-serif;
  }

  h1 {
    color: #263238;
  }

  .dropzone {
    text-align: center;
    padding: 20px;
    border: 3px dashed #eeeeee;
    background-color: #fafafa50;
    border-radius: 1em;
    color: #bdbdbd;
    margin: 1em;
    min-height: 40em;
  }
  
  .dropzone .dz-preview.dz-image-preview {
    background: none !important;
  }

  .dz-button {
    font-size: 2em !important;
    color: #263238 !important;
  }

  .accept {
    border-color: #107c10 !important;
  }

  .reject {
    border-color: #d83b01 !important;
  }
  </style>
  <body>
  <h1>Upload server</h1>
  <h2>{{ host }}:{{ request.environ["SERVER_PORT"]}}</h2>
  <form action="/upload" class="dropzone" id="flask-dropzone"></form>
  <script>
  Dropzone.options.flaskDropzone = {
    
  };
  </script>

  </body>
</html>
"""


def get_ip():
    """get local IP address"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


@app.route("/")
def upload_file():
    host = get_ip()
    return render_template_string(PAGE, host=host)


@app.route("/upload", methods=["POST"])
def upload():
    if request.method == "POST":
        f = request.files["file"]
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        print(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return render_template_string("OK")


def main():
    app.run(host="0.0.0.0", port=5000, debug=True)
