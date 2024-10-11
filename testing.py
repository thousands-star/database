from flask import Flask, send_file

app = Flask(__name__)

@app.route('/get-image', methods=['GET'])
def get_image():
    # Replace 'path/to/image.png' with the actual path of your image file
    return send_file('storagetank_fullness.png', mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
