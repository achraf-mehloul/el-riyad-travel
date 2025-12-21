from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from datetime import datetime
import psycopg2
import os
import logging
from psycopg2.extras import DictCursor
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='.')

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})

# PostgreSQL configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://umrah_admin:9GDKSIxeUrhQLLI3yR3HpMLAO6jT2tHW@dpg-d1v54gh5pdvs73ct6s6g-a.oregon-postgres.render.com/umrah_mv09')

def init_db():
    conn = None
    try:
        conn = get_db()
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
            state TEXT NOT NULL,
            room5_price INTEGER NOT NULL,
            room5_status TEXT NOT NULL DEFAULT 'available',
            room4_price INTEGER NOT NULL,
            room4_status TEXT NOT NULL DEFAULT 'available',
            room3_price INTEGER NOT NULL,
            room3_status TEXT NOT NULL DEFAULT 'available',
            room2_price INTEGER NOT NULL,
            room2_status TEXT NOT NULL DEFAULT 'available'
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            trip_id INTEGER NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            birth_place TEXT NOT NULL,
            passport_number TEXT NOT NULL,
            passport_issue_date TEXT NOT NULL,
            passport_expiry_date TEXT NOT NULL,
            umrah_type TEXT NOT NULL,
            room_type TEXT NOT NULL,
            notes TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            booking_date TEXT NOT NULL,
            FOREIGN KEY (trip_id) REFERENCES trips (id) ON DELETE CASCADE
        )''')

        c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = c.fetchall()
        logger.debug(f"Tables in database: {tables}")

        conn.commit()
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def get_db():
    try:
        # Parse database URL
        result = urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
            sslmode="require"
        )
        conn.set_session(autocommit=False)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

# Initialize database
init_db()

@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

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
    conn = None
    try:
        conn = get_db()
        c = conn.cursor(cursor_factory=DictCursor)

        state_filter = request.args.get('state', 'all')
        type_filter = request.args.get('type', 'all')

        query = 'SELECT * FROM trips'
        params = []

        if state_filter != 'all':
            query += ' WHERE state = %s'
            params.append(state_filter)
            if type_filter != 'all':
                query += ' AND type = %s'
                params.append(type_filter)
        elif type_filter != 'all':
            query += ' WHERE type = %s'
            params.append(type_filter)

        logger.debug(f"Executing query: {query} with params: {params}")
        c.execute(query, params)
        trips = c.fetchall()

        trips_list = []
        for trip in trips:
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
            trips_list.append(trip_data)

        return jsonify({'trips': trips_list})
    except Exception as e:
        logger.error(f"Error getting trips: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/trips/<int:trip_id>', methods=['GET'])
def get_trip(trip_id):
    conn = None
    try:
        conn = get_db()
        c = conn.cursor(cursor_factory=DictCursor)

        c.execute('SELECT * FROM trips WHERE id = %s', (trip_id,))
        trip = c.fetchone()

        if not trip:
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

        return jsonify(trip_data)
    except Exception as e:
        logger.error(f"Error getting trip {trip_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/trips', methods=['POST'])
def create_trip():
    conn = None
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
        c = conn.cursor()

        c.execute('''INSERT INTO trips 
            (date, airline, airline_logo, hotel, hotel_logo, hotel_distance, route, duration, type, state,
             room5_price, room5_status, room4_price, room4_status,
             room3_price, room3_status, room2_price, room2_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id''',
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
                      data['state'],
                      data['room5_price'], 
                      'available', 
                      data['room4_price'], 
                      'available',
                      data['room3_price'], 
                      'available', 
                      data['room2_price'], 
                      'available'
                  ))

        trip_id = c.fetchone()[0]
        conn.commit()

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
    finally:
        if conn:
            conn.close()

@app.route('/api/trips/<int:trip_id>', methods=['DELETE'])
def delete_trip(trip_id):
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()

        # تحقق هل توجد حجوزات مرتبطة بالرحلة
        c.execute('SELECT COUNT(*) FROM bookings WHERE trip_id = %s', (trip_id,))
        bookings_count = c.fetchone()[0]

        if bookings_count > 0:
            return jsonify({'error': 'Cannot delete trip with existing bookings'}), 400

        c.execute('DELETE FROM trips WHERE id = %s', (trip_id,))
        conn.commit()

        return jsonify({'message': 'Trip deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting trip {trip_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/trips/<int:trip_id>', methods=['PUT'])
def update_trip(trip_id):
    conn = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        conn = get_db()
        c = conn.cursor(cursor_factory=DictCursor)

        c.execute('SELECT * FROM trips WHERE id = %s', (trip_id,))
        trip = c.fetchone()

        if not trip:
            return jsonify({'error': 'Trip not found'}), 404

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
            'state': data.get('state', trip['state']),
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
    finally:
        if conn:
            conn.close()

@app.route('/api/trips/<int:trip_id>/status', methods=['PUT'])
def update_trip_status(trip_id):
    conn = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['room5_status', 'room4_status', 'room3_status', 'room2_status']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        conn = get_db()
        c = conn.cursor()

        c.execute('SELECT * FROM trips WHERE id = %s', (trip_id,))
        trip = c.fetchone()

        if not trip:
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
        return jsonify({'message': 'Trip status updated successfully'})
    except Exception as e:
        logger.error(f"Error updating trip {trip_id} status: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    conn = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = [
            'tripId', 'firstName', 'lastName', 'email', 'phone',
            'birthDate', 'birthPlace', 'passportNumber',
            'passportIssueDate', 'passportExpiryDate',
            'umrahType', 'roomType'
        ]

        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        conn = get_db()
        c = conn.cursor()

        # التحقق من وجود الرحلة
        c.execute('SELECT * FROM trips WHERE id = %s', (data['tripId'],))
        trip = c.fetchone()

        if not trip:
            return jsonify({'error': 'Trip not found'}), 404

        # تحويل الـ tuple إلى dict
        columns = [desc[0] for desc in c.description]
        trip_dict = dict(zip(columns, trip))

        # التحقق من توفر الغرفة المطلوبة
        room_status_field = f'room{data["roomType"]}_status'
        if trip_dict[room_status_field] == 'full':
            return jsonify({'error': 'This room type is fully booked'}), 400

        # تسجيل الحجز
        c.execute('''INSERT INTO bookings 
            (trip_id, first_name, last_name, email, phone, birth_date, birth_place,
             passport_number, passport_issue_date, passport_expiry_date, umrah_type,
             room_type, notes, booking_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id''',
                  (
                      data['tripId'], 
                      data['firstName'], 
                      data['lastName'], 
                      data['email'],
                      data['phone'], 
                      data['birthDate'], 
                      data['birthPlace'], 
                      data['passportNumber'],
                      data['passportIssueDate'], 
                      data['passportExpiryDate'], 
                      data['umrahType'],
                      data['roomType'], 
                      data.get('notes', ''), 
                      datetime.now().isoformat()
                  ))

        booking_id = c.fetchone()[0]
        conn.commit()

        return jsonify({
            'message': 'Booking created successfully',
            'id': booking_id
        }), 201

    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        return jsonify({'error': str(e)}), 500

    finally:
        if conn:
            conn.close()


@app.route('/api/bookings/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    conn = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        if 'status' not in data:
            return jsonify({'error': 'Missing required field: status'}), 400

        conn = get_db()
        c = conn.cursor()

        c.execute('SELECT * FROM bookings WHERE id = %s', (booking_id,))
        booking = c.fetchone()

        if not booking:
            return jsonify({'error': 'Booking not found'}), 404

        c.execute('UPDATE bookings SET status = %s WHERE id = %s',
                  (data['status'], booking_id))

        conn.commit()
        return jsonify({'message': 'Booking status updated successfully'})
    except Exception as e:
        logger.error(f"Error updating booking {booking_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()

        c.execute('SELECT * FROM bookings WHERE id = %s', (booking_id,))
        booking = c.fetchone()

        if not booking:
            return jsonify({'error': 'Booking not found'}), 404

        c.execute('DELETE FROM bookings WHERE id = %s', (booking_id,))
        conn.commit()

        return jsonify({'message': 'Booking deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting booking {booking_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()
@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()

        c.execute('SELECT COUNT(*) FROM bookings')
        total_bookings = c.fetchone()[0]

        c.execute('SELECT COUNT(*) FROM bookings WHERE status = %s', ('pending',))
        pending_bookings = c.fetchone()[0]

        c.execute('SELECT COUNT(*) FROM bookings WHERE status = %s', ('approved',))
        approved_bookings = c.fetchone()[0]

        c.execute('SELECT COUNT(*) FROM trips')
        total_trips = c.fetchone()[0]

        # Get bookings by state
        c.execute('''SELECT b.birth_place as state, COUNT(*) as count 
                   FROM bookings b GROUP BY b.birth_place''')
        state_stats = {row[0]: row[1] for row in c.fetchall()}

        # Get bookings by type
        c.execute('''SELECT umrah_type as type, COUNT(*) as count 
                   FROM bookings GROUP BY umrah_type''')
        type_stats = {row[0]: row[1] for row in c.fetchall()}

        return jsonify({
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'approved_bookings': approved_bookings,
            'total_trips': total_trips,
            'state_stats': state_stats,
            'type_stats': type_stats
        })
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    conn = None
    try:
        conn = get_db()
        c = conn.cursor(cursor_factory=DictCursor)

        c.execute('''SELECT b.*, t.date as trip_date, t.airline as trip_airline 
                     FROM bookings b JOIN trips t ON b.trip_id = t.id''')
        bookings = c.fetchall()

        bookings_list = []
        for booking in bookings:
            trip_date = booking['trip_date'] if 'trip_date' in booking.keys() else None
            trip_airline = booking['trip_airline'] if 'trip_airline' in booking.keys() else None

            bookings_list.append({
                'id': booking['id'],
                'tripId': booking['trip_id'],
                'firstName': booking['first_name'],
                'lastName': booking['last_name'],
                'email': booking['email'],
                'phone': booking['phone'],
                'birthDate': booking['birth_date'],
                'birthPlace': booking['birth_place'],
                'passportNumber': booking['passport_number'],
                'passportIssueDate': booking['passport_issue_date'],
                'passportExpiryDate': booking['passport_expiry_date'],
                'umrahType': booking['umrah_type'],
                'roomType': booking['room_type'],
                'notes': booking['notes'],
                'status': booking['status'],
                'bookingDate': booking['booking_date'],
                'trip': {
                    'date': trip_date,
                    'airline': trip_airline
                }
            })

        return jsonify(bookings_list)
    except Exception as e:
        logger.error(f"Error getting bookings: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
