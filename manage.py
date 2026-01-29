#!/usr/bin/env python
"""
CLI tool for managing the Precedent Finder database.
"""

import argparse
import sys
from app import app, db, Precedent


def add_precedent(title, case_number, year, court, description, keywords=''):
    """Add a new precedent to the database."""
    with app.app_context():
        try:
            precedent = Precedent(
                title=title,
                case_number=case_number,
                year=int(year),
                court=court,
                description=description,
                keywords=keywords
            )
            db.session.add(precedent)
            db.session.commit()
            print(f"✓ Successfully added precedent: {title}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error adding precedent: {e}")
            return False


def list_precedents():
    """List all precedents in the database."""
    with app.app_context():
        precedents = Precedent.query.all()
        if not precedents:
            print("No precedents found in database.")
            return
        
        print(f"\n{'ID':<5} {'Title':<30} {'Year':<6} {'Court':<20}")
        print("-" * 65)
        for p in precedents:
            title = p.title[:27] + '...' if len(p.title) > 30 else p.title
            print(f"{p.id:<5} {title:<30} {p.year:<6} {p.court:<20}")
        print(f"\nTotal: {len(precedents)} precedents")


def delete_precedent(precedent_id):
    """Delete a precedent from the database."""
    with app.app_context():
        try:
            precedent = Precedent.query.get(precedent_id)
            if not precedent:
                print(f"✗ Precedent with ID {precedent_id} not found.")
                return False
            
            db.session.delete(precedent)
            db.session.commit()
            print(f"✓ Successfully deleted precedent: {precedent.title}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error deleting precedent: {e}")
            return False


def search_precedents(query):
    """Search for precedents."""
    with app.app_context():
        results = Precedent.query.filter(
            db.or_(
                Precedent.title.ilike(f'%{query}%'),
                Precedent.description.ilike(f'%{query}%'),
                Precedent.keywords.ilike(f'%{query}%'),
                Precedent.case_number.ilike(f'%{query}%')
            )
        ).all()
        
        if not results:
            print(f"No results found for: {query}")
            return
        
        print(f"\nFound {len(results)} result(s) for '{query}':\n")
        for p in results:
            print(f"Title: {p.title}")
            print(f"Case #: {p.case_number}")
            print(f"Year: {p.year}")
            print(f"Court: {p.court}")
            print(f"Description: {p.description[:100]}...")
            print(f"Keywords: {p.keywords}")
            print("-" * 60)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Precedent Finder - Database Management Tool'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new precedent')
    add_parser.add_argument('--title', required=True, help='Case title')
    add_parser.add_argument('--case-number', required=True, help='Case number')
    add_parser.add_argument('--year', required=True, help='Year')
    add_parser.add_argument('--court', required=True, help='Court name')
    add_parser.add_argument('--description', required=True, help='Case description')
    add_parser.add_argument('--keywords', default='', help='Keywords (comma-separated)')
    
    # List command
    subparsers.add_parser('list', help='List all precedents')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a precedent')
    delete_parser.add_argument('id', type=int, help='Precedent ID')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search precedents')
    search_parser.add_argument('query', help='Search query')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        add_precedent(
            args.title,
            args.case_number,
            args.year,
            args.court,
            args.description,
            args.keywords
        )
    elif args.command == 'list':
        list_precedents()
    elif args.command == 'delete':
        delete_precedent(args.id)
    elif args.command == 'search':
        search_precedents(args.query)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
