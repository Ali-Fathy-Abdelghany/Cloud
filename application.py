from flask import Flask, request, jsonify, send_from_directory
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from datetime import datetime
import os
from dotenv import load_dotenv

app = Flask(__name__, static_folder='static')
load_dotenv('.env')
S3_BUCKET = os.getenv('S3_BUCKET')
S3_REGION = os.getenv('S3_REGION')
S3_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
S3_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

# Initialize S3 client
s3 = boto3.client('s3', region_name=S3_REGION, 
                    aws_access_key_id=S3_ACCESS_KEY,
                    aws_secret_access_key=S3_SECRET_KEY)

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
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)
    
    if file_length > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large'}), 400

    try:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_filename = f"{timestamp}-{file.filename}"
        
        s3.upload_fileobj(file, S3_BUCKET, unique_filename)
        
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': unique_filename},
            ExpiresIn=3600
        )
        return jsonify({
            'url': url,
            'filename': unique_filename,
            'message': 'Upload successful'
        })
    except NoCredentialsError:
        return jsonify({'error': 'AWS credentials missing'}), 500
    except ClientError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

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
        
        files.sort(key=lambda x: x['last_modified'], reverse=True)
        return jsonify(files)
    except ClientError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)