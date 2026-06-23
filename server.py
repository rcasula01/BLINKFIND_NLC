from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
from dotenv import load_dotenv

load_dotenv()




# ====== CONFIG ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'data.sqlite')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
SESSION_SECRET = os.environ.get('SESSION_SECRET', 'change-me-in-production')




os.makedirs(UPLOAD_FOLDER, exist_ok=True)




# ====== APP SETUP ======
# Use explicit import name to avoid pkgutil/get_loader issues with some Python versions
app = Flask('server', static_folder=None)
app.secret_key = SESSION_SECRET
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# Set SESSION_COOKIE_SECURE = True in production (HTTPS only)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'

CORS(app,
     supports_credentials=True,
     origins=[
         'http://localhost:8000',
         'http://127.0.0.1:8000',
         'http://localhost:4000',
         'http://127.0.0.1:4000',
     ])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


# ====== SUPABASE CLIENT ======
_supabase_client = None

def get_supabase():
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise RuntimeError(
                'SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables.'
            )
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _supabase_client




# ====== DB HELPERS ======
def get_db():
  conn = sqlite3.connect(DB_FILE, check_same_thread=False)
  conn.row_factory = sqlite3.Row
  return conn




def init_db():
  db = get_db()
  cur = db.cursor()
  cur.execute('''
  CREATE TABLE IF NOT EXISTS items (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      category TEXT,
      location TEXT,
      date_found TEXT,
      finder_name TEXT,
      finder_email TEXT,
      description TEXT,
      image_url TEXT,
      image_filename TEXT,
      status TEXT DEFAULT 'pending',
      created_at TEXT
  );
  ''')
  cur.execute('''
  CREATE TABLE IF NOT EXISTS claims (
      id TEXT PRIMARY KEY,
      item_id TEXT NOT NULL,
      item_name TEXT,
      claimant_name TEXT,
      claimant_email TEXT,
      claimant_phone TEXT,
      description TEXT,
      status TEXT DEFAULT 'pending',
      created_at TEXT,
      FOREIGN KEY(item_id) REFERENCES items(id)
  );
  ''')
  db.commit()
  db.close()




def row_to_dict(row):
  return dict(row) if row else None




def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




# ====== ROUTES ======




@app.route('/api/health', methods=['GET'])
def health():
  return jsonify({'status': 'ok'})




# --- Items (admin) ---
@app.route('/api/items', methods=['GET'])
def get_items():
   db = get_db()
   cur = db.cursor()


   # Fetch all items including image_url
   cur.execute('SELECT * FROM items ORDER BY created_at DESC')
   rows = cur.fetchall()
   db.close()


   # Convert rows to dictionaries including image_url
   return jsonify([row_to_dict(r) for r in rows])




@app.route('/api/items/approved', methods=['GET'])
def get_approved_items():
  db = get_db()
  cur = db.cursor()
  cur.execute("SELECT * FROM items WHERE status = ? ORDER BY created_at DESC", ('approved',))
  rows = cur.fetchall()
  db.close()
  return jsonify([row_to_dict(r) for r in rows])




@app.route('/api/items/category/<category>', methods=['GET'])
def get_items_by_category(category):
  db = get_db()
  cur = db.cursor()
  cur.execute("SELECT * FROM items WHERE status = ? AND category = ? ORDER BY created_at DESC", ('approved', category))
  rows = cur.fetchall()
  db.close()
  return jsonify([row_to_dict(r) for r in rows])




@app.route('/api/items/search', methods=['GET'])
def search_items():
  q = (request.args.get('q') or '').strip().lower()
  category = (request.args.get('category') or '').strip()
  db = get_db()
  cur = db.cursor()
  like_q = f'%{q}%'
  if category:
      cur.execute("""
          SELECT * FROM items
          WHERE status = ? AND category = ?
            AND (LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(location) LIKE ?)
          ORDER BY created_at DESC
      """, ('approved', category, like_q, like_q, like_q))
  else:
      cur.execute("""
          SELECT * FROM items
          WHERE status = ?
            AND (LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(location) LIKE ?)
          ORDER BY created_at DESC
      """, ('approved', like_q, like_q, like_q))
  rows = cur.fetchall()
  db.close()
  return jsonify([row_to_dict(r) for r in rows])




@app.route('/api/items/<item_id>', methods=['GET'])
def get_item(item_id):
  db = get_db()
  cur = db.cursor()
  cur.execute('SELECT * FROM items WHERE id = ?', (item_id,))
  row = cur.fetchone()
  db.close()
  return jsonify(row_to_dict(row))




@app.route('/api/items', methods=['POST'])
def create_item():
   data = request.get_json() or {}


   # Generate unique item ID and timestamp
   item_id = str(uuid.uuid4())
   created_at = datetime.utcnow().isoformat()


   # Ensure the image_url exists in the data
   fields = (
       item_id,
       data.get('name', ''),
       data.get('category', ''),
       data.get('location', ''),
       data.get('date_found', ''),
       data.get('finder_name', ''),
       data.get('finder_email', ''),
       data.get('description', ''),
       data.get('image_url', ''),
       data.get('image_filename', ''),  # Optional: filename if required
       data.get('status', 'pending'),
       created_at
   )


   db = get_db()
   cur = db.cursor()


   cur.execute('''
       INSERT INTO items (id, name, category, location, date_found, finder_name, finder_email, description, image_url, image_filename, status, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
   ''', fields)
   db.commit()


   # Fetch the created item for confirmation
   cur.execute('SELECT * FROM items WHERE id = ?', (item_id,))
   item = cur.fetchone()
   db.close()
   return jsonify(row_to_dict(item)), 201




@app.route('/api/items/<item_id>/status', methods=['PUT'])
def update_item_status(item_id):
  data = request.get_json() or {}
  status = data.get('status')
  if status not in ('pending', 'approved', 'claimed'):
      return jsonify({'error': 'Invalid status'}), 400
  db = get_db()
  cur = db.cursor()
  cur.execute('UPDATE items SET status = ? WHERE id = ?', (status, item_id))
  db.commit()
  cur.execute('SELECT * FROM items WHERE id = ?', (item_id,))
  item = cur.fetchone()
  db.close()
  return jsonify(row_to_dict(item))




@app.route('/api/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
  db = get_db()
  cur = db.cursor()
  cur.execute('SELECT image_filename FROM items WHERE id = ?', (item_id,))
  row = cur.fetchone()
  if row and row['image_filename']:
      path = os.path.join(app.config['UPLOAD_FOLDER'], row['image_filename'])
      if os.path.exists(path):
          try:
              os.remove(path)
          except Exception as e:
              app.logger.warning(f"Failed to delete file {path}: {e}")
  cur.execute('DELETE FROM items WHERE id = ?', (item_id,))
  cur.execute('DELETE FROM claims WHERE item_id = ?', (item_id,))
  db.commit()
  db.close()
  return jsonify({'success': True})




# --- Claims ---
@app.route('/api/claims', methods=['GET'])
def get_claims():
  db = get_db()
  cur = db.cursor()
  cur.execute('SELECT * FROM claims ORDER BY created_at DESC')
  rows = cur.fetchall()
  db.close()
  return jsonify([row_to_dict(r) for r in rows])




@app.route('/api/claims', methods=['POST'])
def create_claim():
  data = request.get_json() or {}
  claim_id = str(uuid.uuid4())
  created_at = datetime.utcnow().isoformat()
  fields = (
      claim_id,
      data.get('item_id', ''),
      data.get('item_name', ''),
      data.get('claimant_name', ''),
      data.get('claimant_email', ''),
      data.get('claimant_phone', ''),
      data.get('description', ''),
      data.get('status', 'pending'),
      created_at
  )
  db = get_db()
  cur = db.cursor()
  cur.execute('''
      INSERT INTO claims (id, item_id, item_name, claimant_name, claimant_email, claimant_phone, description, status, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  ''', fields)
  db.commit()
  cur.execute('SELECT * FROM claims WHERE id = ?', (claim_id,))
  claim = cur.fetchone()
  db.close()
  return jsonify(row_to_dict(claim)), 201




@app.route('/api/claims/<claim_id>/status', methods=['PUT'])
def update_claim_status(claim_id):
  data = request.get_json() or {}
  status = data.get('status')
  if status not in ('pending', 'approved', 'rejected'):
      return jsonify({'error': 'Invalid status'}), 400
  db = get_db()
  cur = db.cursor()
  cur.execute('UPDATE claims SET status = ? WHERE id = ?', (status, claim_id))
  db.commit()
  if status == 'approved':
      claim = cur.execute('SELECT item_id FROM claims WHERE id = ?', (claim_id,)).fetchone()
      if claim:
          cur.execute('UPDATE items SET status = ? WHERE id = ?', ('claimed', claim['item_id']))
          db.commit()
  cur.execute('SELECT * FROM claims WHERE id = ?', (claim_id,))
  claim = cur.fetchone()
  db.close()
  return jsonify(row_to_dict(claim))




@app.route('/api/claims/<claim_id>', methods=['DELETE'])
def delete_claim(claim_id):
  db = get_db()
  cur = db.cursor()
  cur.execute('DELETE FROM claims WHERE id = ?', (claim_id,))
  db.commit()
  db.close()
  return jsonify({'success': True})




# --- Uploads ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
   if 'file' not in request.files:
       return jsonify({'error': 'No file uploaded'}), 400


   file = request.files['file']
   filename = secure_filename(file.filename)


   if filename == '':
       return jsonify({'error': 'Bad filename'}), 400


   # Add timestamp to ensure unique filenames
   timestamped = f"{int(datetime.utcnow().timestamp() * 1000)}-{filename}"
   save_path = os.path.join(app.config['UPLOAD_FOLDER'], timestamped)


   # Save the file to the uploads directory
   file.save(save_path)


   # Generate public URL for the uploaded file
   public_url = f"/uploads/{timestamped}"  # Relative to host
   return jsonify({'publicUrl': public_url}), 201


# ====== AUTH ROUTES ======


@app.route('/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400
    try:
        sb = get_supabase()
        response = sb.auth.sign_in_with_password({'email': email, 'password': password})
        session['access_token'] = response.session.access_token
        session['user_email'] = response.user.email
        return jsonify({'success': True, 'user': {'email': response.user.email}})
    except RuntimeError as e:
        app.logger.error(f'Supabase configuration error: {e}')
        return jsonify({'error': 'Server configuration error. Contact the administrator.'}), 500
    except Exception as e:
        app.logger.warning(f'Login failed for {email}: {e}')
        return jsonify({'error': 'Invalid email or password.'}), 401


@app.route('/auth/logout', methods=['POST'])
def auth_logout():
    token = session.get('access_token')
    if token:
        try:
            sb = get_supabase()
            sb.auth.sign_out()
        except Exception as e:
            app.logger.warning(f'Supabase sign-out error (ignored): {e}')
    session.clear()
    return jsonify({'success': True})


@app.route('/auth/session', methods=['GET'])
def auth_session():
    token = session.get('access_token')
    if not token:
        return jsonify({'authenticated': False}), 401
    try:
        sb = get_supabase()
        user_response = sb.auth.get_user(token)
        return jsonify({
            'authenticated': True,
            'user': {'email': user_response.user.email}
        })
    except Exception as e:
        app.logger.warning(f'Session validation failed: {e}')
        session.clear()
        return jsonify({'authenticated': False}), 401


# ====== START ======
if __name__ == '__main__':
  print("🚀 Starting BlinkFind Server...")
  print(f"📂 Database: {DB_FILE}")
  print(f"📁 Upload folder: {UPLOAD_FOLDER}")
  init_db()
  print("✅ Database initialized")
  app.run(debug=True, port=4000)
