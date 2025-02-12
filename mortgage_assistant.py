import streamlit as st
from openai import OpenAI
import sqlite3
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ConversationalMortgageAgent:
    def __init__(self):
        """Initialize the mortgage agent with empty state"""
        self.db_path = 'mortgage_products.db'  # Define this first
        self.state = {
            'conversation_history': [],
            'collected_info': {},
            'current_step': 'initial',
            'products': self.get_products_from_db(),
            'serviceability_metrics': {}
        }
    
    def get_products_from_db(self):
        """Fetch mortgage products from SQLite database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM mortgage_products')
        columns = [description[0] for description in c.description]
        products = [dict(zip(columns, row)) for row in c.fetchall()]
        conn.close()
        return products

    def get_system_prompt(self):
        """Generate system prompt based on current conversation state"""
        base_prompt = f"""You are an highly experienced and seasoned mortgage loan officer in Australia. Follow this conversation approach:

        [INTERNAL GUIDELINES - DO NOT SHOW IN RESPONSE]
        Formatting:
        - Use bold and color highlight (**) for numbers, rates, amounts
        - Use markdown tables for comparisons
        - Use bullet points (•) for lists
        - Never show section headers like 'Basic Data Collection' or 'Initial Engagement'
        [END INTERNAL GUIDELINES]
        
        Conversation Approach:
        1. Initial Engagement
        - Warmly greet the customer
        - Ask about mortgage goals (first home, investment, refinancing)
        - Be conversational and supportive
        
        2. Basic Data Collection
        - Gather financial information progressively, one topic at a time
        - Start with property value and deposit
        - Then income and expenses
        - Finally, discuss life events and future plans
        - Mention relevant government incentives for first-time buyers as a separate call out so that it's easily readable
        
        3. Advanced Understanding
        - Understand complex financial situations
        - Capture loan preferences (fixed/variable, tenure). But make sure these questions are in two bullet points for easy readability
        - Then discuss long-term goals and life events
        - Consider market trends in the area.
        - Explore property preferences and locations
        
        4. Recommendations
        - Present options in clear tables
        - Explain why each option suits their situation. But make sure it's easy to read . Avoid long paragraphs
        - Compare features and benefits
        - Consider future flexibility needs

        Current State:
        Previously collected information: {self.state['collected_info']}
        Available products: {self.state['products']}
        Customer preferences: {self.state.get('customer_preferences', {})}
        Customer goals: {self.state.get('customer_goals', {})}
        """
        
        if 'mortgage_purpose' in self.state:
            base_prompt += f"\nCustomer Purpose: {self.state['mortgage_purpose']}"
        
        if 'serviceability_metrics' in self.state:
            metrics = self.state['serviceability_metrics']
            base_prompt += f"""
            | Metric | Value |
            |--------|-------|
            | DSR | **{metrics.get('dsr', 0):.2%}** |
            | LVR | **{metrics.get('lvr', 0):.2%}** |
            """
        
        return base_prompt
    def extract_enhanced_info(self, message):
        try:
            analysis_prompt = f"""
            Analyze this message and extract as JSON:
            1. Basic Financial:
            - Income
            - Expenses
            - Loan amount
            - Property value
            - Deposit amount
            
            2. Life Events & Goals:
            - Upcoming life changes (marriage, children, career)
            - Timeline for these changes
            - Property preferences (location, type)
            - Financial goals (quick repayment, lower payments)
            
            3. Risk & Preferences:
            - Rate preference (fixed/variable)
            - Risk tolerance
            - Flexibility needs
            
            Return exact JSON structure:
            {{
                "financial": {{
                    "income": null,
                    "expenses": null,
                    "loan_amount": null,
                    "property_value": null,
                    "deposit": null
                }},
                "life_events": {{
                    "upcoming_changes": [],
                    "timeline": null,
                    "property_preferences": null
                }},
                "preferences": {{
                    "rate_type": null,
                    "risk_tolerance": null,
                    "flexibility_needed": null
                }}
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": analysis_prompt}],
                temperature=0.1
            )
            
            extracted_info = json.loads(response.choices[0].message.content)
            self.update_state_with_info(extracted_info)
            return extracted_info
        except Exception as e:
            print(f"Error extracting info: {e}")
            return {}
    def extract_purpose(self, message):
        """Extract mortgage purpose from user message"""
        try:
            purpose_prompt = f"""
            Analyze this message and determine if it indicates:
            1. First home purchase
            2. Investment property
            3. Refinancing
            4. Unknown/Other
            
            Return only one of these exact terms.
            Message: {message}
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": purpose_prompt}],
                temperature=0.1
            )
            
            purpose = response.choices[0].message.content.strip()
            self.state['mortgage_purpose'] = purpose
            
            if purpose == "First home purchase":
                self.state['first_time_buyer'] = True
            
            return purpose
        except Exception as e:
            print(f"Error extracting purpose: {e}")
            return "Unknown"

    def extract_financial_info(self, message):
        """Extract financial information from user message"""
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """Extract financial information from the message. 
                    Return a valid JSON object with keys: income, expenses, loan_amount, property_value, other_debts.
                    Only include keys where values are clearly mentioned in the message.
                    Example: {"income": 80000} or {}"""},
                    {"role": "user", "content": message}
                ],
                temperature=0.1
            )
            
            import json
            try:
                extracted_info = json.loads(response.choices[0].message.content)
                self.state['collected_info'].update(extracted_info)
                
                # Only calculate serviceability if we have all required info
                required_fields = ['income', 'expenses', 'loan_amount', 'property_value']
                if all(field in self.state['collected_info'] for field in required_fields):
                    info = self.state['collected_info']
                    self.calculate_serviceability(
                        info['income'],
                        info['expenses'],
                        info['loan_amount'],
                        info['property_value'],
                        info.get('other_debts', 0)
                    )
                return extracted_info
            except json.JSONDecodeError:
                return {}
                
        except Exception as e:
            print(f"Error extracting financial info: {e}")
            return {}

    def analyze_rate_impact(self, loan_amount, current_rate, term_years=30):
        """Analyze impact of rate changes on monthly payments"""
        if loan_amount is None or current_rate is None:
            return {}
            
        rate_changes = [-0.5, 0, 0.5, 1.0, 1.5]
        analysis = {}
        
        for change in rate_changes:
            new_rate = float(current_rate) + change
            monthly_payment = self.estimate_monthly_payment(float(loan_amount), new_rate/100, term_years)
            analysis[f"{new_rate:.1f}%"] = monthly_payment
        
        return analysis

    def format_rate_impact_message(self, analysis):
        """Format rate impact analysis for user"""
        message = "Here's how your monthly payments would change with different rates:\n\n"
        base_payment = None
        
        for rate, payment in analysis.items():
            if base_payment is None:
                base_payment = payment
                message += f"At current rate ({rate}): ${payment:,.2f}/month\n"
            else:
                diff = payment - base_payment
                message += f"At {rate}: ${payment:,.2f}/month (${diff:,.2f} change)\n"
        
        return message

    def estimate_monthly_payment(self, loan_amount, annual_rate, years):
        """Calculate monthly mortgage payment"""
        if loan_amount is None or annual_rate is None:
            return 0
        
        monthly_rate = float(annual_rate) / 12
        num_payments = int(years) * 12
        monthly_payment = float(loan_amount) * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        return monthly_payment

    def calculate_serviceability(self, income, expenses, loan_amount, property_value, other_debts=0):
        """Calculate key serviceability metrics"""
        monthly_income = income / 12
        monthly_loan_payment = self.estimate_monthly_payment(loan_amount, 0.035, 30)
        
        dsr = (monthly_loan_payment + other_debts) / monthly_income
        lvr = loan_amount / property_value
        nsr = (monthly_income - expenses) / monthly_loan_payment
        
        return {
            'dsr': dsr,
            'lvr': lvr,
            'nsr': nsr,
            'monthly_payment': monthly_loan_payment
        }
    
    def generate_loan_scenarios(self, customer_profile):
        """Generate personalized loan scenarios based on customer profile"""
        scenarios = []
        financial = customer_profile.get('financial', {})
        life_events = customer_profile.get('life_events', {})
        preferences = customer_profile.get('preferences', {})
        
        # Get base loan details
        property_value = financial.get('property_value', 0)
        income = financial.get('income', 0)
        loan_amount = financial.get('loan_amount', 0)
        
        # Analyze customer needs
        needs_flexibility = 'marriage' in str(life_events.get('upcoming_changes', []))
        risk_tolerance = preferences.get('risk_tolerance', 'moderate')
        
        # Fetch matching products from database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM mortgage_products WHERE min_income <= ?', (income,))
        eligible_products = c.fetchall()
        conn.close()
        
        for product in eligible_products:
            monthly_payment = self.estimate_monthly_payment(loan_amount, float(product[5].strip('%'))/100, 30)
            
            scenario = {
                'product_name': product[1],
                'loan_amount': loan_amount,
                'interest_rate': float(product[5].strip('%')),
                'monthly_payment': monthly_payment,
                'features': [],
                'suitability_reasons': [],
                'considerations': []
            }
            
            # Add personalized recommendations
            if needs_flexibility and product[2] == 'variable':
                scenario['suitability_reasons'].append("Provides flexibility for post-marriage expenses")
                scenario['features'].extend(["Extra repayments", "Redraw facility"])
            
            scenarios.append(scenario)
        
        return scenarios
    def format_scenario_message(self, scenarios):
        """Format loan scenarios into clear, structured output"""
        message = "## Based on your circumstances and preference here are recommended Loan Options\n\n"
        
        for i, scenario in enumerate(scenarios, 1):
            message += f"### Option {i}: {scenario['product_name']}\n"
            message += "| Category | Details |\n|----------|----------|\n"
            message += f"| Interest Rate | **{scenario['interest_rate']}%** |\n"
            message += f"| Monthly Payment | **${scenario['monthly_payment']:,.2f}** |\n"
            
            if scenario['features']:
                message += "\n**Key Features:**\n"
                for feature in scenario['features']:
                    message += f"• {feature}\n"
                    
            if scenario['suitability_reasons']:
                message += "\n**Why This Suits You:**\n"
                for reason in scenario['suitability_reasons']:
                    message += f"• {reason}\n"
            
            message += "\n---\n\n"
        
        return message
    def update_conversation_stage(self):
        """Update the conversation stage based on collected information"""
        info = self.state['collected_info']
        
        if 'mortgage_purpose' not in self.state:
            self.state['current_stage'] = 'initial_engagement'
        elif len(info) == 0:
            self.state['current_stage'] = 'data_collection'
        elif all(field in info for field in ['income', 'expenses', 'loan_amount']):
            self.state['current_stage'] = 'financial_analysis'
        else:
            self.state['current_stage'] = 'data_collection'

    def get_next_response(self, user_message):
        """Process user message and generate next response"""
        # Extract purpose if not already known
        if 'mortgage_purpose' not in self.state:
            self.extract_purpose(user_message)
        
        # Extract financial info
        self.extract_enhanced_info(user_message)
        
        # Update stage based on collected info
        self.update_conversation_stage()
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    *self.state['conversation_history'],
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message.content
            
            # Create customer profile from state
            customer_profile = {
                'financial': self.state['collected_info'],
                'preferences': self.state.get('customer_preferences', {}),
                'goals': self.state.get('customer_goals', {})
            }
            
            # Add scenario analysis when we have basic financial info
            if all(key in self.state['collected_info'] for key in ['income', 'property_value']):
                scenarios = self.generate_loan_scenarios(customer_profile)  # Fixed!
                scenario_message = self.format_scenario_message(scenarios)
                assistant_message += f"\n\n{scenario_message}"
            
            self.state['conversation_history'].extend([
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message}
            ])
            
            return assistant_message
                
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"
'''
def initialize_chat():
    """Initialize chat session and welcome message"""
    if 'mortgage_agent' not in st.session_state:
        st.session_state['mortgage_agent'] = ConversationalMortgageAgent()
        welcome_msg = "Hello! I'm your mortgage advisor. I'm here to help you find the right mortgage solution. What brings you in today?"
        st.session_state['messages'] = [{"role": "assistant", "content": welcome_msg}]
'''
'''
def main():
    """Main application function"""
    st.title("💬 Mortgage Advisor")
    initialize_chat()

    # Display chat messages
    for message in st.session_state['messages']:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if user_input := st.chat_input("Type your message here..."):
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Get and display assistant response
        agent = st.session_state['mortgage_agent']
        response = agent.get_next_response(user_input)
        
        with st.chat_message("assistant"):
            st.write(response)
        
        # Add messages to chat history
        st.session_state['messages'].append({"role": "user", "content": user_input})
        st.session_state['messages'].append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
    
 '''   