"""
Precedent Finder Application
A full-fledged Python web application for searching legal precedents.
"""

import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
from utils import sanitize_search_query

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
    section = db.Column(db.String(100))
    article = db.Column(db.String(100))
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
            'section': self.section,
            'article': self.article,
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
    query = sanitize_search_query(query)
    
    if not query or len(query) < 2:
        return jsonify({'error': 'Search query must be at least 2 characters'}), 400
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # Get filter parameters
    filter_year = request.args.get('year')
    filter_court = request.args.get('court')
    
    # Get sorting parameters
    sort_by = request.args.get('sort', 'year')
    sort_order = request.args.get('order', 'desc')
    
    # Build base query
    base_query = Precedent.query.filter(
        db.or_(
            Precedent.title.ilike(f'%{query}%'),
            Precedent.description.ilike(f'%{query}%'),
            Precedent.keywords.ilike(f'%{query}%'),
            Precedent.case_number.ilike(f'%{query}%'),
            Precedent.section.ilike(f'%{query}%'),
            Precedent.article.ilike(f'%{query}%')
        )
    )
    
    # Apply filters
    if filter_year:
        try:
            base_query = base_query.filter(Precedent.year == int(filter_year))
        except ValueError:
            pass  # Ignore invalid year
    
    if filter_court:
        base_query = base_query.filter(Precedent.court.ilike(f'%{filter_court}%'))
    
    # Apply sorting
    order_func = db.desc if sort_order == 'desc' else db.asc
    if sort_by == 'year':
        base_query = base_query.order_by(order_func(Precedent.year))
    elif sort_by == 'title':
        base_query = base_query.order_by(order_func(Precedent.title))
    elif sort_by == 'court':
        base_query = base_query.order_by(order_func(Precedent.court))
    else:
        base_query = base_query.order_by(db.desc(Precedent.year))  # Default
    
    # Get total count before pagination
    total = base_query.count()
    
    # Apply pagination
    results = base_query.offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'results': [result.to_dict() for result in results],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total > 0 else 0
    })


@app.route('/api/precedent/<int:precedent_id>', methods=['GET'])
def get_precedent(precedent_id):
    """Get a specific precedent by ID."""
    precedent = Precedent.query.get(precedent_id)

    if not precedent:
        return jsonify({'error': 'Precedent not found'}), 404

    return jsonify(precedent.to_dict())


@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """Get search suggestions based on query prefix."""
    prefix = request.args.get('q', '').strip().lower()

    if len(prefix) < 2:
        return jsonify({'suggestions': []})

    # Collect all searchable terms
    terms = set()

    for precedent in Precedent.query.all():
        # Add keywords
        if precedent.keywords:
            terms.update(kw.strip().lower() for kw in precedent.keywords.split(','))
        # Add section terms
        if precedent.section:
            terms.add(precedent.section.lower())
        # Add article terms
        if precedent.article:
            terms.add(precedent.article.lower())
        # Add title words
        terms.update(word.lower() for word in precedent.title.split() if len(word) > 2)

    # Filter terms that start with prefix
    suggestions = [term for term in terms if term.startswith(prefix)]
    suggestions = sorted(set(suggestions))[:5]  # Remove duplicates, sort, limit to 5

    return jsonify({'suggestions': suggestions})


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
        db.drop_all()
        db.create_all()

        # Check if data already exists
        if Precedent.query.first():
            return
        
        # Add sample precedents (Indian Legal System)
        sample_precedents = [
            # Constitutional Law
            Precedent(
                title="Kesavananda Bharati v. State of Kerala",
                case_number="1973-SC-001",
                year=1973,
                court="Supreme Court of India",
                description="Established the Basic Structure Doctrine of the Constitution.",
                keywords="basic structure, constitutional amendments, judicial review, parliament",
                section="Article 368",
                article="Article 368"
            ),
            Precedent(
                title="Maneka Gandhi v. Union of India",
                case_number="1978-SC-002",
                year=1978,
                court="Supreme Court of India",
                description="Expanded the right to life under Article 21 to include right to travel abroad.",
                keywords="right to life, personal liberty, due process, privacy, freedom",
                section="Article 21",
                article="Article 21"
            ),
            Precedent(
                title="State of Kerala v. N.M. Thomas",
                case_number="1976-SC-011",
                year=1976,
                court="Supreme Court of India",
                description="Held that classification for reservation must be reasonable under Article 14.",
                keywords="equality, classification, reservation, reasonable nexus",
                section="Article 14",
                article="Article 14"
            ),
            Precedent(
                title="Indira Gandhi v. Raj Narain",
                case_number="1975-SC-005",
                year=1975,
                court="Supreme Court of India",
                description="Struck down the 39th Amendment and upheld the right to information.",
                keywords="election, corruption, right to know, democracy, freedom of speech",
                section="Article 329",
                article="Article 19"
            ),
            Precedent(
                title="State of Karnataka v. Union of India",
                case_number="1977-SC-006",
                year=1977,
                court="Supreme Court of India",
                description="Upheld reservation policies under Article 16 for backward classes.",
                keywords="reservation, equality, backward classes, affirmative action, discrimination",
                section="Article 16",
                article="Article 16"
            ),
            Precedent(
                title="Minerva Mills Ltd. v. Union of India",
                case_number="1980-SC-012",
                year=1980,
                court="Supreme Court of India",
                description="Struck down amendments limiting judicial review under Article 32.",
                keywords="judicial review, basic structure, fundamental rights, writ jurisdiction",
                section="Article 32",
                article="Article 32"
            ),
            Precedent(
                title="Commissioner, Hindu Religious Endowments v. Sri Lakshmindra Thirtha Swamiar",
                case_number="1954-SC-013",
                year=1954,
                court="Supreme Court of India",
                description="Held that freedom of religion under Article 25 includes right to manage religious affairs.",
                keywords="freedom of religion, religious freedom, conscience, management of religious affairs",
                section="Article 25",
                article="Article 25"
            ),

            # Criminal Law (IPC)
            Precedent(
                title="Vishaka v. State of Rajasthan",
                case_number="1997-SC-003",
                year=1997,
                court="Supreme Court of India",
                description="Guidelines for prevention of sexual harassment at workplace.",
                keywords="sexual harassment, workplace safety, gender equality, dignity",
                section="Section 509 IPC",
                article="Article 15"
            ),
            Precedent(
                title="State of Maharashtra v. Madhukar Narayan Mardikar",
                case_number="1991-SC-007",
                year=1991,
                court="Supreme Court of India",
                description="Defined custodial death and torture under Section 302 IPC.",
                keywords="custodial death, torture, police brutality, murder",
                section="Section 302 IPC",
                article="Article 21"
            ),
            Precedent(
                title="Sachin v. State of Madhya Pradesh",
                case_number="2006-SC-008",
                year=2006,
                court="Supreme Court of India",
                description="Reduced sentence for juvenile offenders under Section 376 IPC.",
                keywords="rape, juvenile, sentencing, criminal justice",
                section="Section 376 IPC",
                article="Article 21"
            ),

            # Civil Law
            Precedent(
                title="K. Kamaraj v. State of Tamil Nadu",
                case_number="1971-SC-004",
                year=1971,
                court="Supreme Court of India",
                description="Held that Section 123(7) of RPA is unconstitutional.",
                keywords="election law, corrupt practices, representation of people act",
                section="Section 123(7) RPA",
                article="Article 19"
            ),
            Precedent(
                title="Union of India v. Association for Democratic Reforms",
                case_number="2002-SC-009",
                year=2002,
                court="Supreme Court of India",
                description="Candidates must disclose criminal antecedents under RPA.",
                keywords="election disclosure, criminal record, transparency, democracy",
                section="Section 33B RPA",
                article="Article 19"
            ),

            # Evidence Law
            Precedent(
                title="Ram Narain v. State of U.P.",
                case_number="1973-SC-010",
                year=1973,
                court="Supreme Court of India",
                description="Admissibility of dying declaration under Section 32 of Evidence Act.",
                keywords="dying declaration, evidence, hearsay, murder trial, criminal procedure",
                section="Section 32 Indian Evidence Act",
                article="Article 21"
            ),

            # Civil Procedure (CPC) - Various Orders
            Precedent(
                title="Dorab Cawasji Warden v. Coomi Sorab Warden",
                case_number="1990-SC-014",
                year=1990,
                court="Supreme Court of India",
                description="Guidelines for grant of temporary injunction under Order 39 Rule 1 of CPC.",
                keywords="injunction, temporary injunction, prima facie case, civil procedure, balance of convenience",
                section="Order 39 Rule 1 CPC",
                article="Article 226"
            ),
            Precedent(
                title="Syed Abdul Khader v. Rami Reddy",
                case_number="1979-SC-027",
                year=1979,
                court="Supreme Court of India",
                description="Execution of decree under Order 21 Rule 1 of CPC.",
                keywords="execution, decree, civil procedure, court execution, judgment debtor",
                section="Order 21 Rule 1 CPC",
                article="Article 226"
            ),
            Precedent(
                title="Sushil Kumar v. Rakesh Kumar",
                case_number="2003-SC-028",
                year=2003,
                court="Supreme Court of India",
                description="Framing of issues under Order 14 Rule 1 of CPC.",
                keywords="issues, framing of issues, civil procedure, trial, pleadings",
                section="Order 14 Rule 1 CPC",
                article="Article 226"
            ),
            Precedent(
                title="B.V. Nagaraju v. State of Karnataka",
                case_number="2007-SC-029",
                year=2007,
                court="Supreme Court of India",
                description="Examination of witnesses under Order 18 Rule 1 of CPC.",
                keywords="witnesses, examination, cross-examination, civil procedure, evidence",
                section="Order 18 Rule 1 CPC",
                article="Article 21"
            ),
            Precedent(
                title="K. Venkataramiah v. A. Seetharama Reddy",
                case_number="2006-SC-030",
                year=2006,
                court="Supreme Court of India",
                description="Appeals under Order 41 Rule 1 of CPC.",
                keywords="appeals, first appeal, memorandum of appeal, civil procedure, appellate court",
                section="Order 41 Rule 1 CPC",
                article="Article 226"
            ),
            Precedent(
                title="Shah Babulal Khimji v. Jayaben D. Kania",
                case_number="1981-SC-015",
                year=1981,
                court="Supreme Court of India",
                description="Principles for grant of permanent injunction under Section 38 of Specific Relief Act.",
                keywords="permanent injunction, specific relief, civil procedure, equity",
                section="Section 38 Specific Relief Act",
                article="Article 226"
            ),

            # Criminal Procedure (CrPC)
            Precedent(
                title="State of Rajasthan v. Balchand",
                case_number="1977-SC-016",
                year=1977,
                court="Supreme Court of India",
                description="Scope of anticipatory bail under Section 438 of CrPC.",
                keywords="anticipatory bail, bail, criminal procedure, apprehension of arrest",
                section="Section 438 CrPC",
                article="Article 21"
            ),
            Precedent(
                title="Ram Prasad v. State of U.P.",
                case_number="1974-SC-017",
                year=1974,
                court="Supreme Court of India",
                description="Maintenance under Section 125 CrPC for wives and children.",
                keywords="maintenance, criminal procedure, family law, domestic violence",
                section="Section 125 CrPC",
                article="Article 21"
            ),

            # Limitation Act
            Precedent(
                title="Consolidated Engineering Enterprises v. Principal Secretary, Irrigation Department",
                case_number="2008-SC-018",
                year=2008,
                court="Supreme Court of India",
                description="Principles for condonation of delay under Section 5 of Limitation Act.",
                keywords="limitation, condonation of delay, sufficient cause, civil procedure",
                section="Section 5 Limitation Act",
                article="Article 226"
            ),

            # Arbitration Law
            Precedent(
                title="Bharat Aluminium Co. v. Kaiser Aluminium Technical Services Inc.",
                case_number="2012-SC-019",
                year=2012,
                court="Supreme Court of India",
                description="Scope of judicial intervention in arbitration under Section 34 of Arbitration Act.",
                keywords="arbitration, judicial review, arbitration award, commercial disputes",
                section="Section 34 Arbitration and Conciliation Act",
                article="Article 226"
            ),

            # More CrPC Sections
            Precedent(
                title="Abhinandan Jha v. Dinesh Mishra",
                case_number="1968-SC-020",
                year=1968,
                court="Supreme Court of India",
                description="Cognizance of offenses by Magistrate under Section 190 of CrPC.",
                keywords="cognizance, magistrate, criminal procedure, jurisdiction",
                section="Section 190 CrPC",
                article="Article 21"
            ),

            # Family Law - Hindu Marriage Act
            Precedent(
                title="Naveen Kohli v. Neelu Kohli",
                case_number="2006-SC-021",
                year=2006,
                court="Supreme Court of India",
                description="Irretrievable breakdown of marriage under Section 13(1)(ia) of Hindu Marriage Act.",
                keywords="divorce, irretrievable breakdown, family law, marriage",
                section="Section 13(1)(ia) Hindu Marriage Act",
                article="Article 21"
            ),

            # Contract Law - Indian Contract Act
            Precedent(
                title="Murlidhar Chiranjilal v. Harishchandra Dwarkadas",
                case_number="1962-SC-022",
                year=1962,
                court="Supreme Court of India",
                description="Measure of damages under Section 73 of Indian Contract Act.",
                keywords="damages, contract law, breach of contract, remoteness",
                section="Section 73 Indian Contract Act",
                article="Article 19"
            ),

            # Property Law - Transfer of Property Act
            Precedent(
                title="T. Lakshmipathi v. P. Nithyananda Reddy",
                case_number="2003-SC-023",
                year=2003,
                court="Supreme Court of India",
                description="Part performance under Section 53A of Transfer of Property Act.",
                keywords="part performance, transfer of property, equitable doctrine, immovable property",
                section="Section 53A Transfer of Property Act",
                article="Article 19"
            ),

            # Company Law - Companies Act
            Precedent(
                title="Vodafone International Holdings BV v. Union of India",
                case_number="2012-SC-024",
                year=2012,
                court="Supreme Court of India",
                description="Retrospective taxation under Section 195 of Income-tax Act and Vodafone case.",
                keywords="taxation, capital gains, retrospective legislation, company law",
                section="Section 195 Income-tax Act",
                article="Article 14"
            ),

            # Consumer Protection - Consumer Protection Act
            Precedent(
                title="Indian Medical Association v. V.P. Shantha",
                case_number="1995-SC-025",
                year=1995,
                court="Supreme Court of India",
                description="Medical negligence under Consumer Protection Act.",
                keywords="medical negligence, consumer protection, service deficiency, healthcare",
                section="Section 2(1)(o) Consumer Protection Act",
                article="Article 21"
            ),

            # Labour Law - Industrial Disputes Act
            Precedent(
                title="Workmen of Dimakuchi Tea Estate v. Dimakuchi Tea Estate",
                case_number="1958-SC-026",
                year=1958,
                court="Supreme Court of India",
                description="Retrenchment under Section 25F of Industrial Disputes Act.",
                keywords="retrenchment, labour law, industrial disputes, unfair labour practices",
                section="Section 25F Industrial Disputes Act",
                article="Article 19"
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
