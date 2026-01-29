"""
Precedent Finder Application
A full-fledged Python web application for searching legal precedents.
"""

import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///precedents.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)


# Database Models
class Precedent(db.Model):
    """Model for storing legal precedents."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, unique=True)
    case_number = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    court = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'case_number': self.case_number,
            'year': self.year,
            'court': self.court,
            'description': self.description,
            'keywords': self.keywords,
        }

    def __repr__(self):
        return f'<Precedent {self.title}>'


# Routes
@app.route('/')
def index():
    """Landing page with search box."""
    return render_template('index.html')


@app.route('/api/search', methods=['GET'])
def search():
    """API endpoint for searching precedents."""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'error': 'Search query must be at least 2 characters'}), 400
    
    # Search in title, description, and keywords
    results = Precedent.query.filter(
        db.or_(
            Precedent.title.ilike(f'%{query}%'),
            Precedent.description.ilike(f'%{query}%'),
            Precedent.keywords.ilike(f'%{query}%'),
            Precedent.case_number.ilike(f'%{query}%')
        )
    ).limit(20).all()
    
    return jsonify({
        'count': len(results),
        'results': [result.to_dict() for result in results]
    })


@app.route('/api/precedent/<int:precedent_id>', methods=['GET'])
def get_precedent(precedent_id):
    """Get a specific precedent by ID."""
    precedent = Precedent.query.get(precedent_id)
    
    if not precedent:
        return jsonify({'error': 'Precedent not found'}), 404
    
    return jsonify(precedent.to_dict())


@app.route('/api/precedent', methods=['POST'])
def create_precedent():
    """Create a new precedent (for admin/API use)."""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['title', 'case_number', 'year', 'court', 'description']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        precedent = Precedent(
            title=data['title'],
            case_number=data['case_number'],
            year=int(data['year']),
            court=data['court'],
            description=data['description'],
            keywords=data.get('keywords', '')
        )
        db.session.add(precedent)
        db.session.commit()
        return jsonify(precedent.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/stats')
def stats():
    """Get statistics about the database."""
    count = Precedent.query.count()
    years = db.session.query(db.func.count(Precedent.id), Precedent.year).group_by(Precedent.year).all()
    courts = db.session.query(db.func.count(Precedent.id), Precedent.court).group_by(Precedent.court).all()
    
    return jsonify({
        'total_precedents': count,
        'by_year': [{'year': year, 'count': count} for count, year in years],
        'by_court': [{'court': court, 'count': count} for count, court in courts]
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Resource not found'}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


def init_db():
    """Initialize the database with sample data."""
    with app.app_context():
        db.create_all()
        
        # Check if data already exists
        if Precedent.query.first():
            return
        
        # Add sample precedents
        sample_precedents = [
            Precedent(
                title="Smith v. Johnson",
                case_number="2023-CV-001",
                year=2023,
                court="Supreme Court",
                description="Landmark case establishing precedent for contract law.",
                keywords="contract, liability, negligence"
            ),
            Precedent(
                title="Brown v. Board of Education",
                case_number="1954-SC-001",
                year=1954,
                court="Supreme Court",
                description="Landmark case on equal protection and education.",
                keywords="education, equality, civil rights"
            ),
            Precedent(
                title="Marbury v. Madison",
                case_number="1803-SC-001",
                year=1803,
                court="Supreme Court",
                description="Established judicial review in the United States.",
                keywords="judicial review, constitutional law"
            ),
        ]
        
        for precedent in sample_precedents:
            db.session.add(precedent)
        
        db.session.commit()
        print("Database initialized with sample data.")


if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the Flask application
    app.run(debug=True, host='0.0.0.0', port=5000)
