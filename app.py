from flask import Flask, jsonify, request, send_from_directory, render_template, send_file
from flask_cors import CORS
from datetime import datetime
import os
import logging
import shutil
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='.')

CORS(app)

UPLOAD_FOLDER = 'static/uploads'
PASSPORT_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'passports')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'webp'}

os.makedirs(PASSPORT_UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None

def init_db():
    conn = get_db()
    if not conn:
        return
    
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS trips (
        id SERIAL PRIMARY KEY,
        date TEXT NOT NULL,
        airline TEXT NOT NULL,
        airline_logo TEXT,
        hotel TEXT NOT NULL,  
        hotel_logo TEXT,    
        hotel_distance TEXT,  
        route TEXT NOT NULL,
        duration INTEGER NOT NULL,
        type TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'all',
        room5_price INTEGER NOT NULL,
        room5_status TEXT NOT NULL DEFAULT 'available',
        room4_price INTEGER NOT NULL,
        room4_status TEXT NOT NULL DEFAULT 'available',
        room3_price INTEGER NOT NULL,
        room3_status TEXT NOT NULL DEFAULT 'available',
        room2_price INTEGER NOT NULL,
        room2_status TEXT NOT NULL DEFAULT 'available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_deleted BOOLEAN DEFAULT FALSE,
        deleted_at TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id SERIAL PRIMARY KEY,
        trip_id INTEGER NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        whatsapp_number TEXT,
        birth_date TEXT NOT NULL,
        birth_place TEXT NOT NULL,
        passport_number TEXT NOT NULL,
        passport_issue_date TEXT NOT NULL,
        passport_expiry_date TEXT NOT NULL,
        passport_scan TEXT,
        passport_file TEXT,
        marital_status TEXT NOT NULL,
        father_name TEXT NOT NULL,
        grandfather_name TEXT NOT NULL,
        job_title TEXT NOT NULL,
        education_level TEXT NOT NULL,
        facebook_profile TEXT,
        umrah_type TEXT NOT NULL,
        room_type TEXT NOT NULL,
        notes TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        booking_date TEXT NOT NULL,
        branch_state TEXT,
        is_deleted BOOLEAN DEFAULT FALSE,
        deleted_at TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES trips (id) ON DELETE SET NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS deleted_trips (
        id SERIAL PRIMARY KEY,
        original_id INTEGER,
        date TEXT NOT NULL,
        airline TEXT NOT NULL,
        airline_logo TEXT,
        hotel TEXT NOT NULL,  
        hotel_logo TEXT,    
        hotel_distance TEXT,  
        route TEXT NOT NULL,
        duration INTEGER NOT NULL,
        type TEXT NOT NULL,
        state TEXT NOT NULL,
        room5_price INTEGER NOT NULL,
        room5_status TEXT NOT NULL,
        room4_price INTEGER NOT NULL,
        room4_status TEXT NOT NULL,
        room3_price INTEGER NOT NULL,
        room3_status TEXT NOT NULL,
        room2_price INTEGER NOT NULL,
        room2_status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS deleted_bookings (
        id SERIAL PRIMARY KEY,
        original_id INTEGER,
        trip_id INTEGER,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        whatsapp_number TEXT,
        birth_date TEXT NOT NULL,
        birth_place TEXT NOT NULL,
        passport_number TEXT NOT NULL,
        passport_issue_date TEXT NOT NULL,
        passport_expiry_date TEXT NOT NULL,
        passport_scan TEXT,
        passport_file TEXT,
        marital_status TEXT NOT NULL,
        father_name TEXT NOT NULL,
        grandfather_name TEXT NOT NULL,
        job_title TEXT NOT NULL,
        education_level TEXT NOT NULL,
        facebook_profile TEXT,
        umrah_type TEXT NOT NULL,
        room_type TEXT NOT NULL,
        notes TEXT,
        status TEXT NOT NULL,
        booking_date TEXT NOT NULL,
        branch_state TEXT,
        deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/check-password', methods=['POST'])
def check_password():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        correct_password = "baya2288@."
        if data.get('password') == correct_password:
            return jsonify({'success': True})
        return jsonify({'success': False}), 401
    except Exception as e:
        logger.error(f"Password check error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard')
def serve_dashboard():
    return render_template('dashboard.html')

@app.route('/api/trips', methods=['GET'])
def get_all_trips():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    c = conn.cursor()

    state_filter = request.args.get('state', 'all')
    type_filter = request.args.get('type', 'all')

    query = 'SELECT * FROM trips WHERE is_deleted = FALSE'
    params = []

    if state_filter != 'all':
        query += ' AND (state = %s OR state = %s OR state LIKE %s)'
        params.extend(['all', state_filter, f'%{state_filter}%'])
        
        if type_filter != 'all':
            query += ' AND type = %s'
            params.append(type_filter)
    elif type_filter != 'all':
        query += ' AND type = %s'
        params.append(type_filter)

    c.execute(query, params)
    trips = c.fetchall()

    trips_list = []
    for trip in trips:
        trip_data = {
            'id': trip['id'],
            'date': trip['date'],
            'airline': trip['airline'],
            'airline_logo': (trip['airline_logo'] or '').replace('static/', ''),
            'hotel': trip['hotel'],
            'hotel_logo': trip['hotel_logo'] or '',
            'hotel_distance': trip['hotel_distance'] or '',
            'route': trip['route'],
            'duration': trip['duration'],
            'type': trip['type'],
            'state': trip['state'],
            'room5': {
                'price': trip['room5_price'],
                'status': trip['room5_status']
            },
            'room4': {
                'price': trip['room4_price'],
                'status': trip['room4_status']
            },
            'room3': {
                'price': trip['room3_price'],
                'status': trip['room3_status']
            },
            'room2': {
                'price': trip['room2_price'],
                'status': trip['room2_status']
            }
        }
        trips_list.append(trip_data)

    conn.close()
    return jsonify({'trips': trips_list})

@app.route('/api/trips/<int:trip_id>', methods=['GET'])
def get_trip(trip_id):
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    c = conn.cursor()

    c.execute('SELECT * FROM trips WHERE id = %s AND is_deleted = FALSE', (trip_id,))
    trip = c.fetchone()

    if not trip:
        conn.close()
        return jsonify({'error': 'Trip not found'}), 404

    trip_data = {
        'id': trip['id'],
        'date': trip['date'],
        'airline': trip['airline'],
        'airline_logo': trip['airline_logo'] or '',
        'hotel': trip['hotel'],
        'hotel_logo': trip['hotel_logo'] or '',
        'hotel_distance': trip['hotel_distance'] or '',
        'route': trip['route'],
        'duration': trip['duration'],
        'type': trip['type'],
        'state': trip['state'],
        'room5': {
            'price': trip['room5_price'],
            'status': trip['room5_status']
        },
        'room4': {
            'price': trip['room4_price'],
            'status': trip['room4_status']
        },
        'room3': {
            'price': trip['room3_price'],
            'status': trip['room3_status']
        },
        'room2': {
            'price': trip['room2_price'],
            'status': trip['room2_status']
        }
    }

    conn.close()
    return jsonify(trip_data)

@app.route('/api/trips', methods=['POST'])
def create_trip():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = [
            'date', 'airline', 'hotel', 'route', 'duration', 'type', 'state',
            'room5_price', 'room4_price', 'room3_price', 'room2_price'
        ]

        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        c = conn.cursor()

        if isinstance(data['state'], list):
            state_value = ','.join(data['state'])
        else:
            state_value = data['state']

        c.execute('''INSERT INTO trips 
            (date, airline, airline_logo, hotel, hotel_logo, hotel_distance, route, duration, type, state,
             room5_price, room5_status, room4_price, room4_status,
             room3_price, room3_status, room2_price, room2_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                  (
                      data['date'], 
                      data['airline'], 
                      data.get('airline_logo', ''),
                      data['hotel'], 
                      data.get('hotel_logo', ''), 
                      data.get('hotel_distance', ''),
                      data['route'], 
                      data['duration'], 
                      data['type'], 
                      state_value,
                      data['room5_price'], 
                      'available', 
                      data['room4_price'], 
                      'available',
                      data['room3_price'], 
                      'available', 
                      data['room2_price'], 
                      'available'
                  ))

        trip_id = c.fetchone()['id']
        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Trip created successfully',
            'id': trip_id,
            'trip': {
                'id': trip_id,
                **data
            }
        }), 201
    except Exception as e:
        logger.error(f"Error creating trip: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trips/<int:trip_id>', methods=['DELETE'])
def delete_trip(trip_id):
    try:
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        c = conn.cursor()

        c.execute('SELECT * FROM trips WHERE id = %s AND is_deleted = FALSE', (trip_id,))
        trip = c.fetchone()

        if not trip:
            conn.close()
            return jsonify({'error': 'Trip not found'}), 404

        c.execute('''INSERT INTO deleted_trips 
            (original_id, date, airline, airline_logo, hotel, hotel_logo, hotel_distance, 
             route, duration, type, state, room5_price, room5_status, room4_price, room4_status,
             room3_price, room3_status, room2_price, room2_status, created_at)
            SELECT 
                id, date, airline, airline_logo, hotel, hotel_logo, hotel_distance, 
                route, duration, type, state, room5_price, room5_status, room4_price, room4_status,
                room3_price, room3_status, room2_price, room2_status, created_at
            FROM trips WHERE id = %s''', (trip_id,))

        c.execute('UPDATE trips SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP WHERE id = %s', (trip_id,))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Trip moved to trash successfully'})
    except Exception as e:
        logger.error(f"Error deleting trip {trip_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trips/<int:trip_id>', methods=['PUT'])
def update_trip(trip_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        c = conn.cursor()

        c.execute('SELECT * FROM trips WHERE id = %s AND is_deleted = FALSE', (trip_id,))
        trip = c.fetchone()

        if not trip:
            conn.close()
            return jsonify({'error': 'Trip not found'}), 404

        if 'state' in data and isinstance(data['state'], list):
            state_value = ','.join(data['state'])
        else:
            state_value = data.get('state', trip['state'])

        update_fields = {
            'date': data.get('date', trip['date']),
            'airline': data.get('airline', trip['airline']),
            'airline_logo': data.get('airline_logo', trip['airline_logo']),
            'hotel': data.get('hotel', trip['hotel']),
            'hotel_logo': data.get('hotel_logo', trip['hotel_logo']),
            'hotel_distance': data.get('hotel_distance', trip['hotel_distance']),
            'route': data.get('route', trip['route']),
            'duration': data.get('duration', trip['duration']),
            'type': data.get('type', trip['type']),
            'state': state_value,
            'room5_price': data.get('room5_price', trip['room5_price']),
            'room4_price': data.get('room4_price', trip['room4_price']),
            'room3_price': data.get('room3_price', trip['room3_price']),
            'room2_price': data.get('room2_price', trip['room2_price'])
        }

        c.execute('''UPDATE trips SET 
                        date = %s, airline = %s, airline_logo = %s, hotel = %s, hotel_logo = %s, 
                        hotel_distance = %s, route = %s, duration = %s, type = %s, state = %s, 
                        room5_price = %s, room4_price = %s, room3_price = %s, room2_price = %s
                     WHERE id = %s''',
                  (
                      update_fields['date'], 
                      update_fields['airline'], 
                      update_fields['airline_logo'],
                      update_fields['hotel'], 
                      update_fields['hotel_logo'], 
                      update_fields['hotel_distance'],
                      update_fields['route'], 
                      update_fields['duration'], 
                      update_fields['type'], 
                      update_fields['state'],
                      update_fields['room5_price'], 
                      update_fields['room4_price'],
                      update_fields['room3_price'], 
                      update_fields['room2_price'], 
                      trip_id
                  ))

        conn.commit()
        conn.close()
        return jsonify({
            'message': 'Trip updated successfully',
            'trip': {
                'id': trip_id,
                **update_fields
            }
        })
    except Exception as e:
        logger.error(f"Error updating trip {trip_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trips/<int:trip_id>/status', methods=['PUT'])
def update_trip_status(trip_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['room5_status', 'room4_status', 'room3_status', 'room2_status']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        c = conn.cursor()

        c.execute('SELECT * FROM trips WHERE id = %s AND is_deleted = FALSE', (trip_id,))
        trip = c.fetchone()

        if not trip:
            conn.close()
            return jsonify({'error': 'Trip not found'}), 404

        c.execute('''UPDATE trips SET 
            room5_status = %s, room4_status = %s, room3_status = %s, room2_status = %s
            WHERE id = %s''',
                  (
                      data['room5_status'], 
                      data['room4_status'],
                      data['room3_status'], 
                      data['room2_status'], 
                      trip_id
                  ))

        conn.commit()
        conn.close()
        return jsonify({'message': 'Trip status updated successfully'})
    except Exception as e:
        logger.error(f"Error updating trip {trip_id} status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    try:
        data = request.form.to_dict()
        
        required_fields = [
            'tripId', 'firstName', 'lastName', 'email', 'phone',
            'birthDate', 'birthPlace', 'passportNumber',
            'passportIssueDate', 'passportExpiryDate',
            'umrahType', 'roomType', 'maritalStatus',
            'fatherName', 'grandfatherName',
            'jobTitle', 'educationLevel'
        ]

        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        c = conn.cursor()

        c.execute('SELECT * FROM trips WHERE id = %s AND is_deleted = FALSE', (data['tripId'],))
        trip = c.fetchone()

        if not trip:
            conn.close()
            return jsonify({'error': 'Trip not found'}), 404

        room_status_field = f'room{data["roomType"]}_status'
        if trip[room_status_field] == 'full':
            conn.close()
            return jsonify({'error': 'This room type is fully booked'}), 400

        passport_file = request.files.get('passportFile')
        passport_filename = None
        
        if passport_file and passport_file.filename != '':
            if allowed_file(passport_file.filename):
                filename = secure_filename(passport_file.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                filepath = os.path.join(PASSPORT_UPLOAD_FOLDER, unique_filename)
                passport_file.save(filepath)
                passport_filename = f"uploads/passports/{unique_filename}"
            else:
                return jsonify({'error': 'File type not allowed. Allowed types: png, jpg, jpeg, pdf, webp'}), 400

        c.execute('''INSERT INTO bookings 
            (trip_id, first_name, last_name, email, phone, whatsapp_number,
             birth_date, birth_place, passport_number, passport_issue_date, 
             passport_expiry_date, passport_scan, passport_file, marital_status, father_name,
             grandfather_name, job_title, education_level, facebook_profile,
             umrah_type, room_type, notes, booking_date, branch_state)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                  (
                      data['tripId'], 
                      data['firstName'], 
                      data['lastName'], 
                      data['email'],
                      data['phone'], 
                      data.get('whatsappNumber', ''),
                      data['birthDate'], 
                      data['birthPlace'], 
                      data['passportNumber'],
                      data['passportIssueDate'], 
                      data['passportExpiryDate'], 
                      data.get('passportScan', ''),
                      passport_filename,
                      data['maritalStatus'],
                      data['fatherName'],
                      data['grandfatherName'],
                      data['jobTitle'],
                      data['educationLevel'],
                      data.get('facebookProfile', ''),
                      data['umrahType'],
                      data['roomType'], 
                      data.get('notes', ''), 
                      datetime.now().isoformat(),
                      data.get('birthPlace', '')
                  ))

        booking_id = c.fetchone()['id']
        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Booking created successfully',
            'id': booking_id
        }), 201

    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        if 'status' not in data:
            return jsonify({'error': 'Missing required field: status'}), 400

        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        c = conn.cursor()

        c.execute('SELECT * FROM bookings WHERE id = %s AND is_deleted = FALSE', (booking_id,))
        booking = c.fetchone()

        if not booking:
            conn.close()
            return jsonify({'error': 'Booking not found'}), 404

        c.execute('UPDATE bookings SET status = %s WHERE id = %s',
                  (data['status'], booking_id))

        conn.commit()
        conn.close()
        return jsonify({'message': 'Booking status updated successfully'})
    except Exception as e:
        logger.error(f"Error updating booking {booking_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    try:
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        c = conn.cursor()

        c.execute('SELECT * FROM bookings WHERE id = %s AND is_deleted = FALSE', (booking_id,))
        booking = c.fetchone()

        if not booking:
            conn.close()
            return jsonify({'error': 'Booking not found'}), 404

        c.execute('''INSERT INTO deleted_bookings 
            (original_id, trip_id, first_name, last_name, email, phone, whatsapp_number,
             birth_date, birth_place, passport_number, passport_issue_date, 
             passport_expiry_date, passport_scan, passport_file, marital_status, father_name,
             grandfather_name, job_title, education_level, facebook_profile,
             umrah_type, room_type, notes, status, booking_date, branch_state)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                  (
                      booking_id,
                      booking['trip_id'],
                      booking['first_name'],
                      booking['last_name'],
                      booking['email'],
                      booking['phone'],
                      booking['whatsapp_number'],
                      booking['birth_date'],
                      booking['birth_place'],
                      booking['passport_number'],
                      booking['passport_issue_date'],
                      booking['passport_expiry_date'],
                      booking['passport_scan'],
                      booking['passport_file'],
                      booking['marital_status'],
                      booking['father_name'],
                      booking['grandfather_name'],
                      booking['job_title'],
                      booking['education_level'],
                      booking['facebook_profile'],
                      booking['umrah_type'],
                      booking['room_type'],
                      booking['notes'],
                      booking['status'],
                      booking['booking_date'],
                      booking['branch_state']
                  ))

        c.execute('UPDATE bookings SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP WHERE id = %s', (booking_id,))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Booking moved to trash successfully'})
    except Exception as e:
        logger.error(f"Error deleting booking {booking_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings/<int:booking_id>/restore', methods=['POST'])
def restore_booking(booking_id):
    try:
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        c = conn.cursor()

        c.execute('SELECT * FROM deleted_bookings WHERE original_id = %s ORDER BY deleted_at DESC LIMIT 1', (booking_id,))
        deleted_booking = c.fetchone()

        if not deleted_booking:
            conn.close()
            return jsonify({'error': 'Deleted booking not found'}), 404

        c.execute('UPDATE bookings SET is_deleted = FALSE, deleted_at = NULL WHERE id = %s', (booking_id,))

        c.execute('DELETE FROM deleted_bookings WHERE original_id = %s', (booking_id,))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Booking restored successfully'})
    except Exception as e:
        logger.error(f"Error restoring booking {booking_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings/<int:booking_id>/permanent', methods=['DELETE'])
def delete_booking_permanent(booking_id):
    try:
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        c = conn.cursor()

        c.execute('DELETE FROM deleted_bookings WHERE original_id = %s', (booking_id,))
        
        c.execute('DELETE FROM bookings WHERE id = %s', (booking_id,))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Booking permanently deleted'})
    except Exception as e:
        logger.error(f"Error permanently deleting booking {booking_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trash/trips', methods=['GET'])
def get_trash_trips():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    c = conn.cursor()

    c.execute('SELECT * FROM deleted_trips ORDER BY deleted_at DESC')
    trips = c.fetchall()

    trips_list = []
    for trip in trips:
        trips_list.append({
            'id': trip['original_id'],
            'date': trip['date'],
            'airline': trip['airline'],
            'deleted_at': trip['deleted_at']
        })

    conn.close()
    return jsonify({'trips': trips_list})

@app.route('/api/trash/bookings', methods=['GET'])
def get_trash_bookings():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    c = conn.cursor()

    c.execute('SELECT * FROM deleted_bookings ORDER BY deleted_at DESC')
    bookings = c.fetchall()

    bookings_list = []
    for booking in bookings:
        bookings_list.append({
            'id': booking['original_id'],
            'firstName': booking['first_name'],
            'lastName': booking['last_name'],
            'email': booking['email'],
            'phone': booking['phone'],
            'deleted_at': booking['deleted_at']
        })

    conn.close()
    return jsonify({'bookings': bookings_list})

@app.route('/api/trash/trips/<int:trip_id>/restore', methods=['POST'])
def restore_trip(trip_id):
    try:
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        c = conn.cursor()

        c.execute('UPDATE trips SET is_deleted = FALSE, deleted_at = NULL WHERE id = %s', (trip_id,))

        c.execute('DELETE FROM deleted_trips WHERE original_id = %s', (trip_id,))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Trip restored successfully'})
    except Exception as e:
        logger.error(f"Error restoring trip {trip_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trash/trips/<int:trip_id>/permanent', methods=['DELETE'])
def delete_trip_permanent(trip_id):
    try:
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        c = conn.cursor()

        c.execute('DELETE FROM deleted_trips WHERE original_id = %s', (trip_id,))
        c.execute('DELETE FROM trips WHERE id = %s', (trip_id,))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Trip permanently deleted'})
    except Exception as e:
        logger.error(f"Error permanently deleting trip {trip_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM bookings WHERE is_deleted = FALSE')
    total_bookings = c.fetchone()['count']

    c.execute('SELECT COUNT(*) FROM bookings WHERE status = %s AND is_deleted = FALSE', ('pending',))
    pending_bookings = c.fetchone()['count']

    c.execute('SELECT COUNT(*) FROM bookings WHERE status = %s AND is_deleted = FALSE', ('approved',))
    approved_bookings = c.fetchone()['count']

    c.execute('SELECT COUNT(*) FROM trips WHERE is_deleted = FALSE')
    total_trips = c.fetchone()['count']

    c.execute('''SELECT branch_state as state, COUNT(*) as count 
               FROM bookings WHERE is_deleted = FALSE GROUP BY branch_state''')
    rows = c.fetchall()
    state_stats = {row['state']: row['count'] for row in rows}

    c.execute('''SELECT umrah_type as type, COUNT(*) as count 
               FROM bookings WHERE is_deleted = FALSE GROUP BY umrah_type''')
    rows = c.fetchall()
    type_stats = {row['type']: row['count'] for row in rows}

    conn.close()
    return jsonify({
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings,
        'total_trips': total_trips,
        'state_stats': state_stats,
        'type_stats': type_stats
    })

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    c = conn.cursor()

    branch_filter = request.args.get('branch', 'all')

    if branch_filter == 'all':
        c.execute('''SELECT b.*, t.date as trip_date, t.airline as trip_airline 
                     FROM bookings b 
                     JOIN trips t ON b.trip_id = t.id 
                     WHERE b.is_deleted = FALSE''')
    else:
        c.execute('''SELECT b.*, t.date as trip_date, t.airline as trip_airline 
                     FROM bookings b 
                     JOIN trips t ON b.trip_id = t.id 
                     WHERE b.is_deleted = FALSE AND b.branch_state = %s''', (branch_filter,))

    bookings = c.fetchall()

    bookings_list = []
    for booking in bookings:
        bookings_list.append({
            'id': booking['id'],
            'tripId': booking['trip_id'],
            'firstName': booking['first_name'],
            'lastName': booking['last_name'],
            'email': booking['email'],
            'phone': booking['phone'],
            'whatsappNumber': booking['whatsapp_number'],
            'birthDate': booking['birth_date'],
            'birthPlace': booking['birth_place'],
            'passportNumber': booking['passport_number'],
            'passportIssueDate': booking['passport_issue_date'],
            'passportExpiryDate': booking['passport_expiry_date'],
            'passportScan': booking['passport_scan'],
            'passportFile': booking['passport_file'],
            'maritalStatus': booking['marital_status'],
            'fatherName': booking['father_name'],
            'grandfatherName': booking['grandfather_name'],
            'jobTitle': booking['job_title'],
            'educationLevel': booking['education_level'],
            'facebookProfile': booking['facebook_profile'],
            'umrahType': booking['umrah_type'],
            'roomType': booking['room_type'],
            'notes': booking['notes'],
            'status': booking['status'],
            'bookingDate': booking['booking_date'],
            'branchState': booking['branch_state'],
            'trip': {
                'date': booking['trip_date'],
                'airline': booking['trip_airline']
            }
        })

    conn.close()
    return jsonify(bookings_list)

if __name__ == '__main__':
    init_db()

    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask app on port {port}")
    
    app.run(host="0.0.0.0", port=port, debug=False)
