import openai
import os
from dotenv import load_dotenv
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Load API key from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Mock mortgage product data
MORTGAGE_PRODUCTS = [
    {
        "name": "Basic Home Loan",
        "min_income": 50000,
        "max_loan": 500000,
        "property_value_min": 200000,
        "interest_rate": "3.5%"
    },
    {
        "name": "Premium Home Loan",
        "min_income": 100000,
        "max_loan": 1000000,
        "property_value_min": 500000,
        "interest_rate": "2.9%"
    },
    {
        "name": "First-Time Buyer Loan",
        "min_income": 40000,
        "max_loan": 300000,
        "property_value_min": 150000,
        "interest_rate": "4.0%"
    }
]

def collect_user_data():
    print(Fore.CYAN + "\nWelcome to the Mortgage Assistant!")
    print(Fore.CYAN + "I'll guide you through a quick pre-eligibility check.")
    print(Style.DIM + "-" * 50)
    
    # Collect inputs
    income = float(input(Fore.YELLOW + "Please enter your annual income (in AUD): "))
    expenses = float(input(Fore.YELLOW + "Please enter your monthly expenses (in AUD): "))
    property_value = float(input(Fore.YELLOW + "What is the value of the property you're looking to buy (in AUD)? "))
    loan_amount = float(input(Fore.YELLOW + "How much loan are you requesting (in AUD)? "))
    
    print(Style.DIM + "-" * 50)
    return {
        "income": income,
        "expenses": expenses,
        "property_value": property_value,
        "loan_amount": loan_amount
    }

def calculate_eligibility(data):
    # Basic pre-eligibility check (mock rule)
    annual_savings = data["income"] - (data["expenses"] * 12)
    eligibility_amount = annual_savings * 5  # Rule: Eligible for loans up to 5x annual savings

    if data["loan_amount"] <= eligibility_amount:
        return True, eligibility_amount
    else:
        return False, eligibility_amount

def recommend_products(user_data):
    # Filter mortgage products based on user inputs
    recommended = []
    for product in MORTGAGE_PRODUCTS:
        if (
            user_data["income"] >= product["min_income"]
            and user_data["loan_amount"] <= product["max_loan"]
            and user_data["property_value"] >= product["property_value_min"]
        ):
            recommended.append(product)
    return recommended

def generate_document_checklist(user_data, is_eligible):
    checklist = ["Proof of Identity (e.g., Passport, Driver's License)"]
    if not is_eligible:
        checklist.append("Proof of Additional Income or Guarantor Letter")
    if user_data["loan_amount"] > 500000:
        checklist.append("Detailed Bank Statements")
    if user_data["property_value"] > 750000:
        checklist.append("Property Valuation Report")
    return checklist

if __name__ == "__main__":
    # Collect user data
    user_data = collect_user_data()
    is_eligible, max_loan = calculate_eligibility(user_data)
    
    print(Fore.CYAN + "\nEligibility Check Results")
    print(Style.DIM + "-" * 50)
    if is_eligible:
        print(Fore.GREEN + f"You are pre-eligible for a loan! Based on your inputs, you can borrow up to AUD {max_loan:.2f}.")
    else:
        print(Fore.RED + f"Unfortunately, you're not pre-eligible for the requested loan amount. You may be eligible for up to AUD {max_loan:.2f}.")
    
    # Recommend products
    print(Fore.CYAN + "\nRecommended Mortgage Products")
    print(Style.DIM + "-" * 50)
    recommendations = recommend_products(user_data)
    if recommendations:
        for product in recommendations:
            print(Fore.YELLOW + f"  - {product['name']} (Interest Rate: {product['interest_rate']})")
    else:
        print(Fore.RED + "No suitable mortgage products found based on your criteria.")
    
    # Generate document checklist
    print(Fore.CYAN + "\nPersonalized Document Checklist")
    print(Style.DIM + "-" * 50)
    checklist = generate_document_checklist(user_data, is_eligible)
    for doc in checklist:
        print(Fore.YELLOW + f"  - {doc}")
    
    print(Fore.GREEN + "\nThank you for using the Mortgage Assistant!")
