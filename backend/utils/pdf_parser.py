import pdfplumber
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PDFParser:
    """
    Parse bank statements from PDF files and extract transaction data.
    Supports multiple bank formats (HDFC, ICICI, SBI, and generic).
    """

    def __init__(self):
        self.transactions = []
        self.bank_type = None
        self.statement_date_range = None

    def parse_pdf(self, pdf_path):
        """
        Main function to parse PDF and extract transactions.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            dict: Contains transactions and metadata
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"Opened PDF with {len(pdf.pages)} pages")
                
                # Detect bank type
                self.detect_bank_type(pdf)
                
                # Extract transactions from all pages
                for page_num, page in enumerate(pdf.pages):
                    self.extract_from_page(page, page_num)
                
                logger.info(f"Extracted {len(self.transactions)} transactions")
                
                return {
                    'status': 'success',
                    'transactions': self.transactions,
                    'bank_type': self.bank_type,
                    'total_transactions': len(self.transactions),
                    'statement_date_range': self.statement_date_range
                }
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            return {
                'status': 'error',
                'message': f"Failed to parse PDF: {str(e)}",
                'transactions': []
            }

    def detect_bank_type(self, pdf):
        """Detect the type of bank statement"""
        try:
            first_page_text = pdf.pages[0].extract_text()
            
            if 'HDFC' in first_page_text.upper():
                self.bank_type = 'HDFC'
            elif 'ICICI' in first_page_text.upper():
                self.bank_type = 'ICICI'
            elif 'SBI' in first_page_text.upper():
                self.bank_type = 'SBI'
            else:
                self.bank_type = 'GENERIC'
                
            logger.info(f"Detected bank type: {self.bank_type}")
        except Exception as e:
            logger.warning(f"Could not detect bank type: {str(e)}")
            self.bank_type = 'GENERIC'

    def extract_from_page(self, page, page_num):
        """Extract transactions from a single page"""
        try:
            text = page.extract_text()
            tables = page.extract_tables()
            
            if tables:
                for table in tables:
                    self.extract_from_table(table)
            
            # Also try to extract from text if no tables found
            if not tables or len(self.transactions) == 0:
                self.extract_from_text(text)
                
        except Exception as e:
            logger.warning(f"Error extracting from page {page_num}: {str(e)}")

    def extract_from_table(self, table):
        """Extract transactions from table format"""
        try:
            for row in table[1:]:  # Skip header row
                if row and len(row) >= 3:
                    transaction = self.parse_row(row)
                    if transaction:
                        self.transactions.append(transaction)
        except Exception as e:
            logger.warning(f"Error extracting from table: {str(e)}")

    def extract_from_text(self, text):
        """Extract transactions from text format"""
        try:
            # Pattern: Date Description Amount Balance
            pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s+(.+?)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)'
            
            matches = re.finditer(pattern, text)
            for match in matches:
                date_str, description, amount, balance = match.groups()
                
                transaction = {
                    'date': self.parse_date(date_str),
                    'description': description.strip(),
                    'amount': self.parse_amount(amount),
                    'balance': self.parse_amount(balance),
                    'type': 'DEBIT' if 'DR' in description.upper() else 'CREDIT'
                }
                
                if transaction['date'] and transaction['amount']:
                    self.transactions.append(transaction)
                    
        except Exception as e:
            logger.warning(f"Error extracting from text: {str(e)}")

    def parse_row(self, row):
        """Parse a single row from table"""
        try:
            if len(row) < 3:
                return None
            
            # Assuming format: [Date, Description, Amount, Balance]
            date_str = str(row[0]).strip() if row[0] else None
            description = str(row[1]).strip() if row[1] else None
            amount_str = str(row[2]).strip() if row[2] else None
            balance_str = str(row[3]).strip() if len(row) > 3 and row[3] else None
            
            if not all([date_str, description, amount_str]):
                return None
            
            date = self.parse_date(date_str)
            amount = self.parse_amount(amount_str)
            balance = self.parse_amount(balance_str) if balance_str else None
            
            if not date or not amount:
                return None
            
            return {
                'date': date,
                'description': description,
                'amount': amount,
                'balance': balance,
                'type': 'DEBIT' if amount < 0 else 'CREDIT'
            }
        except Exception as e:
            logger.debug(f"Error parsing row: {str(e)}")
            return None

    def parse_date(self, date_str):
        """Parse date string in various formats"""
        date_formats = [
            '%d-%m-%Y', '%d/%m/%Y', '%m-%d-%Y', '%m/%d/%Y',
            '%Y-%m-%d', '%Y/%m/%d', '%d-%b-%Y', '%d/%b/%Y',
            '%b-%d-%Y', '%b/%d/%Y', '%d-%B-%Y', '%d/%B/%Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None

    def parse_amount(self, amount_str):
        """Parse amount string and return float"""
        try:
            if not amount_str:
                return None
            
            # Remove commas and spaces
            amount_str = str(amount_str).replace(',', '').strip()
            
            # Handle negative amounts
            if '-' in amount_str:
                amount = -float(amount_str.replace('-', ''))
            else:
                amount = float(amount_str)
            
            return round(amount, 2)
        except ValueError:
            logger.debug(f"Could not parse amount: {amount_str}")
            return None
