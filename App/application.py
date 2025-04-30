from flask import Flask, request, jsonify, send_from_directory
import boto3
from botocore.exceptions import NoCredentialsError
from datetime import datetime
import os

app = Flask(__name__, static_folder='static')

# AWS Configuration
S3_BUCKET = 'my-file-share-app-2025'  # Replace with your bucket name
S3_REGION = 'eu-central-1'       # Replace with your region (e.g., 'us-east-1')

# Initialize S3 client
s3 = boto3.client('s3', region_name=S3_REGION)

@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    try:
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_filename = f"{timestamp}-{file.filename}"
        
        s3.upload_fileobj(file, S3_BUCKET, unique_filename)
        
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': unique_filename},
            ExpiresIn=3600  # 1 hour expiry
        )
        return jsonify({
            'url': url,
            'filename': unique_filename,
            'message': 'Upload successful'
        })
    except NoCredentialsError:
        return jsonify({'error': 'AWS credentials missing'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/list-files')
def list_files():
    try:
        objects = s3.list_objects_v2(Bucket=S3_BUCKET)
        files = []
        
        if 'Contents' in objects:
            for obj in objects['Contents']:
                url = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': S3_BUCKET, 'Key': obj['Key']},
                    ExpiresIn=3600
                )
                files.append({
                    'key': obj['Key'],
                    'url': url,
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })
        
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    app.run(host='0.0.0.0', port=5000, debug=True)