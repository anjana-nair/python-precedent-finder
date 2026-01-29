"""
Entry point for running the Precedent Finder application.
"""

from app import app, init_db

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8000)
