import sqlite3

def setup_database():
    conn = sqlite3.connect('mortgage_products.db')
    c = conn.cursor()
    
    # Enhanced products table with more realistic attributes
    c.execute('''
        CREATE TABLE IF NOT EXISTS mortgage_products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            product_type TEXT NOT NULL,  # fixed, variable, split
            min_income REAL,
            max_loan REAL,
            property_value_min REAL,
            base_rate REAL,
            comparison_rate REAL,
            max_lvr REAL,
            term_years INTEGER,
            first_home_buyer_eligible BOOLEAN,
            features TEXT,  # JSON string of features
            early_repayment_allowed BOOLEAN,
            offset_account BOOLEAN
        )
    ''')
    
    # More diverse sample products
    products = [
        ('Standard Variable', 'variable', 50000, 1000000, 200000, 4.5, 4.7, 80, 30, True, 
         '{"offset": true, "redraw": true}', True, True),
        ('Fixed 3-Year Special', 'fixed', 60000, 1500000, 250000, 4.2, 4.4, 85, 3, True, 
         '{"rate_lock": true}', False, False),
        ('First Home Buyer Plus', 'variable', 40000, 600000, 150000, 4.8, 5.0, 95, 30, True, 
         '{"fee_waiver": true, "govt_support": true}', True, True),
        ('Premium Split', 'split', 100000, 2000000, 500000, 4.3, 4.5, 80, 30, False, 
         '{"offset": true, "redraw": true, "rate_lock": true}', True, True),
        ('Investment Property', 'variable', 80000, 1200000, 300000, 4.9, 5.1, 80, 30, False, 
         '{"interest_only": true}', True, True)
    ]
    
    c.executemany('''
        INSERT OR REPLACE INTO mortgage_products 
        (name, product_type, min_income, max_loan, property_value_min, 
         base_rate, comparison_rate, max_lvr, term_years, 
         first_home_buyer_eligible, features, early_repayment_allowed, offset_account)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', products)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()