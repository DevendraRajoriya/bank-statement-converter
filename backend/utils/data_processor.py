import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataProcessor:
    def __init__(self):
        self.processed_transactions = []
        self.validation_errors = []

    def process_transactions(self, transactions):
        self.processed_transactions = []
        self.validation_errors = []
        
        for idx, transaction in enumerate(transactions):
            try:
                processed = self.validate_and_clean_transaction(transaction, idx)
                if processed:
                    self.processed_transactions.append(processed)
            except Exception as e:
                self.validation_errors.append({
                    'index': idx,
                    'error': str(e),
                    'transaction': transaction
                })
                logger.warning(f"Error processing transaction {idx}: {str(e)}")
        
        logger.info(f"Processed {len(self.processed_transactions)} transactions")
        
        return {
            'status': 'success',
            'transactions': self.processed_transactions,
            'total_processed': len(self.processed_transactions),
            'total_errors': len(self.validation_errors),
            'validation_errors': self.validation_errors,
            'summary': self.generate_summary()
        }

    def validate_and_clean_transaction(self, transaction, idx):
        try:
            date = transaction.get('date')
            description = transaction.get('description')
            amount = transaction.get('amount')
            balance = transaction.get('balance')
            trans_type = transaction.get('type', 'CREDIT')
            
            if not date:
                raise ValueError("Missing date")
            if not description or description.strip() == '':
                raise ValueError("Missing description")
            if amount is None:
                raise ValueError("Missing amount")
            
            description = self.clean_description(description)
            amount = float(amount)
            balance = float(balance) if balance else None
            
            trans_type = 'DEBIT' if amount < 0 else 'CREDIT'
            category = self.categorize_transaction(description)
            
            return {
                'date': date,
                'description': description,
                'amount': abs(amount),
                'type': trans_type,
                'balance': balance,
                'category': category,
                'raw_amount': amount,
                'row_num': idx + 2
            }
        except Exception as e:
            raise e

    def clean_description(self, description):
        try:
            description = ' '.join(description.split())
            description = description.strip()
            if len(description) > 100:
                description = description[:97] + '...'
            return description
        except Exception as e:
            logger.warning(f"Error cleaning description: {str(e)}")
            return description

    def categorize_transaction(self, description):
        desc_lower = description.lower()
        categories = {
            'SALARY': ['salary', 'wage', 'stipend', 'payroll'],
            'TRANSFER': ['transfer', 'trf', 'neft', 'rtgs', 'imps'],
            'WITHDRAWAL': ['withdrawal', 'atm', 'cash'],
            'DEPOSIT': ['deposit', 'cheque', 'check'],
            'UTILITY': ['electricity', 'water', 'gas', 'phone', 'internet'],
            'FOOD': ['restaurant', 'food', 'cafe', 'grocery', 'supermarket'],
            'ENTERTAINMENT': ['movie', 'cinema', 'entertainment', 'games'],
            'HEALTHCARE': ['hospital', 'clinic', 'pharmacy', 'doctor', 'medical'],
            'SHOPPING': ['shopping', 'mall', 'store', 'retail'],
            'TRANSPORT': ['uber', 'taxi', 'petrol', 'fuel', 'transport'],
            'SUBSCRIPTION': ['subscription', 'netflix', 'spotify', 'prime'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in desc_lower for keyword in keywords):
                return category
        return 'OTHER'

    def generate_summary(self):
        try:
            if not self.processed_transactions:
                return {
                    'total_transactions': 0,
                    'total_credits': 0,
                    'total_debits': 0,
                    'net_amount': 0,
                    'opening_balance': None,
                    'closing_balance': None
                }
            
            credits = sum(t['amount'] for t in self.processed_transactions if t['type'] == 'CREDIT')
            debits = sum(t['amount'] for t in self.processed_transactions if t['type'] == 'DEBIT')
            
            opening_balance = None
            closing_balance = None
            
            if self.processed_transactions:
                first = self.processed_transactions[0]
                last = self.processed_transactions[-1]
                if first.get('balance'):
                    opening_balance = first['balance']
                if last.get('balance'):
                    closing_balance = last['balance']
            
            return {
                'total_transactions': len(self.processed_transactions),
                'total_credits': round(credits, 2),
                'total_debits': round(debits, 2),
                'net_amount': round(credits - debits, 2),
                'opening_balance': opening_balance,
                'closing_balance': closing_balance
            }
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return {}