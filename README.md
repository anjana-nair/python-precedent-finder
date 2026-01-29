# Precedent Finder

A full-fledged Python web application for searching legal precedents. This application features a modern, responsive landing page with a powerful search functionality.

## Features

✨ **Core Features**
- 🔍 Full-text search across precedents (title, case number, court, description, keywords)
- 📊 Database of legal precedents with SQLAlchemy ORM
- 🎨 Modern, responsive UI with gradient design
- ⚙️ RESTful API endpoints for search and data management
- 📱 Mobile-friendly interface
- 🗄️ SQLite database with sample data included

## Project Structure

```
python-precedent-finder/
├── app.py                 # Main Flask application
├── run.py                 # Entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore file
├── templates/
│   ├── base.html          # Base template with styling
│   └── index.html         # Landing page with search box
├── utils.py               # Utility functions
├── manage.py              # CLI management tool
└── README.md              # This file
```

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or navigate to the repository:**
   ```bash
   cd /workspaces/python-precedent-finder
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and update the `SECRET_KEY` for production use.

5. **Run the application:**
   ```bash
   python run.py
   ```

   The application will be available at `http://localhost:5000`

## Usage

### Web Interface
1. Navigate to the home page
2. Enter your search query in the search box
3. Press Enter or click the Search button
4. Browse through the results

### API Endpoints

#### Search Precedents
```
GET /api/search?q=<query>
```
**Parameters:**
- `q` (string, required): Search query (minimum 2 characters)

**Response:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "title": "Smith v. Johnson",
      "case_number": "2023-CV-001",
      "year": 2023,
      "court": "Supreme Court",
      "description": "Landmark case...",
      "keywords": "contract, liability"
    }
  ]
}
```

#### Get Specific Precedent
```
GET /api/precedent/<id>
```

#### Create a New Precedent
```
POST /api/precedent
Content-Type: application/json

{
  "title": "Case Name",
  "case_number": "2024-CV-001",
  "year": 2024,
  "court": "Court Name",
  "description": "Case description",
  "keywords": "keyword1, keyword2"
}
```

#### Get Statistics
```
GET /stats
```

## Database Schema

### Precedent Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| title | String(255) | Case title (unique) |
| case_number | String(100) | Case number |
| year | Integer | Year of decision |
| court | String(200) | Court name |
| description | Text | Case description |
| keywords | String(500) | Searchable keywords |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

## Development

### Hot Reload
The application runs in debug mode by default, enabling hot reload on file changes.

### Database Reset
To reset the database and reload sample data, delete `precedents.db` and restart the application:
```bash
rm precedents.db
python run.py
```

### Adding More Sample Data
Edit the `init_db()` function in `app.py` to add more sample precedents.

## Technologies Used

- **Backend:** Flask 2.3.3
- **Database:** SQLite with SQLAlchemy ORM
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Environment:** Python 3.8+

## Features Highlights

### Search Capabilities
- Searches across multiple fields: title, case number, court, description, keywords
- Case-insensitive search
- Returns up to 20 results
- Real-time search feedback with loading indicator

### UI/UX
- Modern gradient design with purple theme
- Responsive layout for mobile and desktop
- Smooth transitions and hover effects
- Semantic HTML5 structure
- Accessible form elements

### Backend Architecture
- Modular Flask application structure
- RESTful API design
- SQLAlchemy ORM for database abstraction
- Configuration management via environment variables
- Error handling for common scenarios

## Deployment

### For Production
1. Change `FLASK_ENV` to `production` in `.env`
2. Update `SECRET_KEY` to a secure random value
3. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn app:app
   ```
4. Set up a reverse proxy (nginx/Apache)
5. Use PostgreSQL or MySQL for the database

### Docker Deployment
Create a `Dockerfile` for containerization:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
```

## Future Enhancements

- 📈 Advanced filtering (by year, court, etc.)
- 💾 Export search results (PDF, CSV)
- 🏷️ Tagging system for precedents
- 👤 User authentication and saved searches
- 🔗 Citation tracking and references
- 📊 Analytics dashboard
- 🌙 Dark mode support
- 🌐 Multi-language support

## CLI Management Tool

Use the `manage.py` script to manage the database from the command line:

### Add a Precedent
```bash
python manage.py add --title "Case Name" --case-number "2024-CV-001" --year 2024 --court "Court Name" --description "Description" --keywords "keyword1, keyword2"
```

### List All Precedents
```bash
python manage.py list
```

### Search Precedents
```bash
python manage.py search "query"
```

### Delete a Precedent
```bash
python manage.py delete <id>
```

## Troubleshooting

### Port Already in Use
If port 5000 is already in use:
```python
app.run(port=5001)  # Use different port
```

### Database Errors
Delete `precedents.db` to reset:
```bash
rm precedents.db
python run.py
```

### Module Import Errors
Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## License

MIT License - Feel free to use this project for educational and commercial purposes.

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## Support

For issues or questions, please open an issue in the repository.

---

**Happy Searching! 🔍**