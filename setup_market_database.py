import sqlite3
import random
from datetime import datetime, timedelta

def setup_market_database():
    """Create and populate market data database with synthetic Sydney property data"""
    conn = sqlite3.connect('property_market.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS suburbs (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            postcode TEXT NOT NULL,
            state TEXT NOT NULL,
            median_price REAL,
            price_growth_ytd REAL,
            avg_days_on_market INTEGER
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS recent_sales (
            id INTEGER PRIMARY KEY,
            suburb_id INTEGER,
            property_type TEXT,
            bedrooms INTEGER,
            bathrooms INTEGER,
            parking INTEGER,
            sale_price REAL,
            sale_date DATE,
            days_on_market INTEGER,
            FOREIGN KEY (suburb_id) REFERENCES suburbs (id)
        )
    ''')

    # Add these new tables here
    c.execute('''
        CREATE TABLE IF NOT EXISTS market_trends (
            id INTEGER PRIMARY KEY,
            suburb_id INTEGER,
            month DATE,
            avg_interest_rate REAL,
            clearance_rate REAL,
            new_listings INTEGER,
            FOREIGN KEY (suburb_id) REFERENCES suburbs (id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS competitor_rates (
            id INTEGER PRIMARY KEY,
            lender_name TEXT,
            product_type TEXT,
            interest_rate REAL,
            comparison_rate REAL,
            last_updated DATE
        )
    ''')

    # Then add some sample data for these new tables
    competitor_data = [
        ('Commonwealth Bank', 'variable', 4.29, 4.45, '2024-02-07'),
        ('Westpac', 'variable', 4.35, 4.52, '2024-02-07'),
        ('NAB', 'fixed_3yr', 4.79, 4.95, '2024-02-07'),
        ('ANZ', 'variable', 4.32, 4.48, '2024-02-07'),
        ('ING', 'variable', 4.15, 4.30, '2024-02-07'),
        ('Macquarie', 'fixed_2yr', 4.55, 4.72, '2024-02-07')
    ]
    
    c.executemany('''
        INSERT OR REPLACE INTO competitor_rates 
        (lender_name, product_type, interest_rate, comparison_rate, last_updated)
        VALUES (?, ?, ?, ?, ?)
    ''', competitor_data)
    
    # Generate recent sales for each suburb
    for suburb_id in range(1, len(suburbs_data) + 1):
        # Get suburb median price
        c.execute('SELECT median_price FROM suburbs WHERE id = ?', (suburb_id,))
        median_price = c.fetchone()[0]
        
        # Generate 10 recent sales per suburb
        sales_data = []
        for _ in range(10):
            # Vary price around median
            price_variation = random.uniform(0.85, 1.15)
            sale_price = median_price * price_variation
            
            # Random date in last 6 months
            days_ago = random.randint(1, 180)
            sale_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            # Property details
            property_types = ["House", "Apartment", "Townhouse"]
            sales_data.append((
                suburb_id,
                random.choice(property_types),
                random.randint(1, 5),  # bedrooms
                random.randint(1, 3),  # bathrooms
                random.randint(1, 3),  # parking
                sale_price,
                sale_date,
                random.randint(20, 90)  # days on market
            ))
    
        c.executemany('''
            INSERT INTO recent_sales 
            (suburb_id, property_type, bedrooms, bathrooms, parking, sale_price, sale_date, days_on_market)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sales_data)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_market_database()