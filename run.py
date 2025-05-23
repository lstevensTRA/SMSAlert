from app import create_app, db
import sys

app = create_app()

if __name__ == '__main__':
    if '--init-db' in sys.argv:
        with app.app_context():
            db.create_all()
        print('Database tables created.')
    else:
        app.run(host="127.0.0.1", port=5050, debug=True) 