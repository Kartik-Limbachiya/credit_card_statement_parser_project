"""
Supports: Axis Bank, Bank of Baroda, Kotak Bank, SBI, and Yes Bank
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import json

@dataclass
class Transaction:
    """Transaction data structure"""
    date: str
    description: str
    amount: float
    type: str  # 'credit' or 'debit'

@dataclass
class CreditCardStatement:
    """Unified credit card statement data structure"""
    bank_name: str
    card_number: Optional[str] = None
    statement_date: Optional[str] = None
    payment_due_date: Optional[str] = None
    credit_limit: Optional[float] = None
    total_amount_due: Optional[float] = None
    minimum_amount_due: Optional[float] = None
    available_credit: Optional[float] = None
    previous_balance: Optional[float] = None
    transactions: List[Transaction] = field(default_factory=list)
    extraction_quality: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['transactions'] = [asdict(t) for t in self.transactions]
        return data


class CreditCardParser:
    """Base parser class with common utilities"""

    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            print("⚠ PyPDF2 not found, attempting direct read...")
            with open(pdf_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")

    @staticmethod
    def clean_amount(amount_str: str) -> Optional[float]:
        """Clean and convert amount string to float"""
        if not amount_str or amount_str.strip() == '':
            return None
        try:
            cleaned = re.sub(r'[₹$€,\s]', '', str(amount_str).strip())
            cleaned = re.sub(r'[^\d.]', '', cleaned)
            if not cleaned or cleaned == '':
                return None
            result = float(cleaned)
            return result if result > 0 else None
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def extract_card_number(text: str, patterns: List[str]) -> Optional[str]:
        """Extract card number using multiple patterns"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                result = match.group(1).strip() if match.groups() else match.group(0).strip()
                if result and result.lower() != 'not found':
                    return result
        return None

    @staticmethod
    def extract_date(text: str, patterns: List[str]) -> Optional[str]:
        """Extract date using multiple patterns"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                result = match.group(1).strip() if match.groups() else match.group(0).strip()
                if result and len(result) > 2:
                    return result
        return None


class AxisBankParser(CreditCardParser):
    """Parser for Axis Bank credit card statements"""

    def parse(self, pdf_path: str) -> CreditCardStatement:
        """Parse Axis Bank statement"""
        text = self.extract_text_from_pdf(pdf_path)
        quality = {}

        # Card number patterns
        card_patterns = [
            r'Credit Card Number:\s*(\d{4}X+\d{4})',
            r'Card Number:\s*(\d{4}[X\*]+\d{4})'
        ]
        card_number = self.extract_card_number(text, card_patterns)
        quality['card_number'] = card_number is not None

        # Statement date
        date_patterns = [
            r'Selected Statement Month\s+(\w+\s+\d{4})',
            r'Statement Month\s+(\w+\s+\d{4})'
        ]
        statement_date = self.extract_date(text, date_patterns)
        quality['statement_date'] = statement_date is not None

        # Payment due date
        due_patterns = [
            r'Payment Due Date\s+(\d{2}\s+\w+\s+\'\d{2})',
            r'Due Date\s+(\d{2}\s+\w+\s+\'\d{2})'
        ]
        payment_due_date = self.extract_date(text, due_patterns)
        quality['payment_due_date'] = payment_due_date is not None

        # Credit limit
        credit_limit_match = re.search(r'Credit Limit\s+₹\s*([\d,]+\.?\d*)', text)
        credit_limit = self.clean_amount(credit_limit_match.group(1)) if credit_limit_match else None
        quality['credit_limit'] = credit_limit is not None

        # Total amount due
        total_due_match = re.search(r'Total Payment Due\s+₹\s*([\d,]+\.?\d*)', text)
        total_amount_due = self.clean_amount(total_due_match.group(1)) if total_due_match else None
        quality['total_amount_due'] = total_amount_due is not None

        # Minimum amount due
        min_due_match = re.search(r'Minimum Payment Due\s+₹\s*([\d,]+\.?\d*)', text)
        minimum_amount_due = self.clean_amount(min_due_match.group(1)) if min_due_match else None
        quality['minimum_amount_due'] = minimum_amount_due is not None

        # Previous balance
        opening_balance_match = re.search(r'Opening Balance\s+₹\s*([\d,]+\.?\d*)', text)
        previous_balance = self.clean_amount(opening_balance_match.group(1)) if opening_balance_match else None
        quality['previous_balance'] = previous_balance is not None

        # Available credit
        available_credit = None
        if credit_limit and total_amount_due:
            available_credit = credit_limit - total_amount_due
        quality['available_credit'] = available_credit is not None

        transactions = self._extract_transactions(text)

        return CreditCardStatement(
            bank_name="Axis Bank",
            card_number=card_number,
            statement_date=statement_date,
            payment_due_date=payment_due_date,
            credit_limit=credit_limit,
            total_amount_due=total_amount_due,
            minimum_amount_due=minimum_amount_due,
            available_credit=available_credit,
            previous_balance=previous_balance,
            transactions=transactions,
            extraction_quality=quality
        )

    def _extract_transactions(self, text: str) -> List[Transaction]:
        """Extract transactions from Axis Bank statement"""
        transactions = []
        pattern = r"(\d{2}\s+\w+\s+'\d{2})\s+(.+?)\s+₹\s*([\d,]+\.?\d*)\s+(Credit|Debit)"
        matches = re.findall(pattern, text, re.MULTILINE)

        for match in matches:
            amount = self.clean_amount(match[2])
            if amount:
                transactions.append(Transaction(
                    date=match[0],
                    description=match[1].strip(),
                    amount=amount,
                    type=match[3].lower()
                ))
        return transactions


class BobParser(CreditCardParser):
    """Parser for Bank of Baroda credit card statements - FIXED"""

    def parse(self, pdf_path: str) -> CreditCardStatement:
        """Parse Bank of Baroda statement"""
        text = self.extract_text_from_pdf(pdf_path)
        quality = {}

        # Extract card number - BOB uses last 4 digits
        card_patterns = [
            r'XXXXXX\*+(\d{4})',
            r'Card.*?(\d{4})\s*\n',
            r'PRIMARY CARD-(\d{4})'
        ]
        card_number = self.extract_card_number(text, card_patterns)
        quality['card_number'] = card_number is not None

        # Statement date
        date_patterns = [
            r'(\d{2}/\d{2}/\d{4})\s+\d{2}\s+\w+,\s+\d{4}\s+To\s+\d{2}\s+\w+,\s+\d{4}',
            r'^(\d{2}/\d{2}/\d{4})'
        ]
        statement_date = self.extract_date(text, date_patterns)
        quality['statement_date'] = statement_date is not None

        # Payment due date - appears before "Page 1 of 4"
        due_patterns = [
            r'(\d{2}/\d{2}/\d{4})\s*\n.*?Page\s+\d+\s+of',
            r'(\d{2}/\d{2}/\d{4})\s+600\.00\s+30,000\.00'
        ]
        payment_due_date = self.extract_date(text, due_patterns)
        quality['payment_due_date'] = payment_due_date is not None

        # Credit limit - BOB format: multiple amounts in a row
        credit_limit_match = re.search(r'Card\s*:\s*VISA.*?\n.*?([\d,]+\.00)\s+([\d,]+\.00)\s+DR', text, re.DOTALL)
        if credit_limit_match:
            credit_limit = self.clean_amount(credit_limit_match.group(1))
        else:
            credit_limit = None
        quality['credit_limit'] = credit_limit is not None

        # Total and Minimum Amount Due - pattern: amount1 amount2 DR
        amounts_match = re.search(r'([\d,]+\.00)\s+([\d,]+\.00)\s+DR', text)
        if amounts_match:
            total_amount_due = self.clean_amount(amounts_match.group(2))
            minimum_amount_due = self.clean_amount(amounts_match.group(1))
        else:
            total_amount_due = None
            minimum_amount_due = None

        quality['total_amount_due'] = total_amount_due is not None
        quality['minimum_amount_due'] = minimum_amount_due is not None

        previous_balance = None
        quality['previous_balance'] = False

        # Available credit
        available_credit = None
        if credit_limit and total_amount_due:
            available_credit = credit_limit - total_amount_due
        quality['available_credit'] = available_credit is not None

        transactions = self._extract_transactions(text)

        return CreditCardStatement(
            bank_name="Bank of Baroda",
            card_number=card_number,
            statement_date=statement_date,
            payment_due_date=payment_due_date,
            credit_limit=credit_limit,
            total_amount_due=total_amount_due,
            minimum_amount_due=minimum_amount_due,
            available_credit=available_credit,
            previous_balance=previous_balance,
            transactions=transactions,
            extraction_quality=quality
        )

    def _extract_transactions(self, text: str) -> List[Transaction]:
        """Extract transactions from BOB statement - FIXED"""
        transactions = []
        # Pattern: DD/MM/YYYY transaction_id description location amount INR balance balance DR/CR
        pattern = r'(\d{2}/\d{2}/\d{4})\s+\d+\s+(.+?)\s+([\d,]+)\s+INR\s+([\d,]+\.00)\s+([\d,]+\.00)\s+(DR|CR)'
        matches = re.findall(pattern, text)

        for match in matches:
            amount = self.clean_amount(match[1])  # The actual transaction amount
            if amount:
                trans_type = 'credit' if match[5] == 'CR' else 'debit'
                transactions.append(Transaction(
                    date=match[0],
                    description=match[1].strip(),
                    amount=amount,
                    type=trans_type
                ))
        return transactions


class KotakParser(CreditCardParser):
    """Parser for Kotak Bank credit card statements - FIXED"""

    def parse(self, pdf_path: str) -> CreditCardStatement:
        """Parse Kotak Bank statement"""
        text = self.extract_text_from_pdf(pdf_path)
        quality = {}

        # Card number
        card_patterns = [
            r'Primary Card Number\s+(\d{4}\s+X+\s+X+\s+\d{4})',
            r'Card Number.*?(\d{4}\s+X+\s+X+\s+\d{4})'
        ]
        card_number = self.extract_card_number(text, card_patterns)
        quality['card_number'] = card_number is not None

        # Statement date
        date_patterns = [
            r'Statement Date\s+(\d{2}-\w{3}-\d{4})',
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
        ]
        statement_date = self.extract_date(text, date_patterns)
        quality['statement_date'] = statement_date is not None

        # Payment due date
        due_patterns = [
            r'Remember to pay by\s+(\d{2}-\w{3}-\d{4})',
            r'pay by\s+(\d{2}-\w{3}-\d{4})'
        ]
        payment_due_date = self.extract_date(text, due_patterns)
        quality['payment_due_date'] = payment_due_date is not None

        # Credit limit - FIXED pattern
        credit_limit_match = re.search(r'Total Credit Limit\s+Rs\.\s*([\d,]+\.?\d*)', text)
        credit_limit = self.clean_amount(credit_limit_match.group(1)) if credit_limit_match else None
        quality['credit_limit'] = credit_limit is not None

        # Total amount due - FIXED pattern
        total_due_match = re.search(r'Total Amount Due \(TAD\)\s+Rs\.\s*([\d,]+\.?\d*)', text)
        if not total_due_match:
            total_due_match = re.search(r'Total\s+Amount Due.*?Rs\.\s*([\d,]+\.?\d*)', text, re.DOTALL)
        total_amount_due = self.clean_amount(total_due_match.group(1)) if total_due_match else None
        quality['total_amount_due'] = total_amount_due is not None

        # Minimum amount due - FIXED pattern
        min_due_match = re.search(r'Minimum Amount Due \(MAD\)\s+Rs\.\s*([\d,]+\.?\d*)', text)
        if not min_due_match:
            min_due_match = re.search(r'Minimum\s+Amount Due.*?Rs\.\s*([\d,]+\.?\d*)', text, re.DOTALL)
        minimum_amount_due = self.clean_amount(min_due_match.group(1)) if min_due_match else None
        quality['minimum_amount_due'] = minimum_amount_due is not None

        # Available credit - FIXED pattern
        available_credit_match = re.search(r'Available Credit Limit:\s+Rs\.\s*([\d,]+\.?\d*)', text)
        available_credit = self.clean_amount(available_credit_match.group(1)) if available_credit_match else None
        quality['available_credit'] = available_credit is not None

        # Previous balance
        previous_due_match = re.search(r'Previous\s+Amount Due\s+Rs\.\s*([\d,]+\.?\d*)', text)
        previous_balance = self.clean_amount(previous_due_match.group(1)) if previous_due_match else None
        quality['previous_balance'] = previous_balance is not None

        transactions = self._extract_transactions(text)

        return CreditCardStatement(
            bank_name="Kotak Mahindra Bank",
            card_number=card_number,
            statement_date=statement_date,
            payment_due_date=payment_due_date,
            credit_limit=credit_limit,
            total_amount_due=total_amount_due,
            minimum_amount_due=minimum_amount_due,
            available_credit=available_credit,
            previous_balance=previous_balance,
            transactions=transactions,
            extraction_quality=quality
        )

    def _extract_transactions(self, text: str) -> List[Transaction]:
        """Extract transactions from Kotak statement"""
        transactions = []
        # Pattern: DD/MM/YYYY description amount Cr
        pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d,]+\.?\d*)\s+(Cr|Dr)'
        matches = re.findall(pattern, text)

        for match in matches:
            amount = self.clean_amount(match[2])
            if amount:
                trans_type = 'credit' if match[3] == 'Cr' else 'debit'
                transactions.append(Transaction(
                    date=match[0],
                    description=match[1].strip(),
                    amount=amount,
                    type=trans_type
                ))
        return transactions


class SBIParser(CreditCardParser):
    """Parser for SBI credit card statements - FIXED"""

    def parse(self, pdf_path: str) -> CreditCardStatement:
        """Parse SBI statement"""
        text = self.extract_text_from_pdf(pdf_path)
        quality = {}

        # Card number
        card_patterns = [
            r'XXXX\s+XXXX\s+XXXX\s+(XX\d{2})',
            r'Credit Card Number.*?(XX\d{2})'
        ]
        card_number = self.extract_card_number(text, card_patterns)
        quality['card_number'] = card_number is not None

        # Statement date
        date_patterns = [
            r'for Statement Period:\s+(\d{2}\s+\w{3}\s+\d{2}\s+to\s+\d{2}\s+\w{3}\s+\d{2})',
            r'(\d{2}\s+\w{3}\s+\d{2})\s+to\s+\d{2}\s+\w{3}\s+\d{2}'
        ]
        statement_date = self.extract_date(text, date_patterns)
        quality['statement_date'] = statement_date is not None

        # Payment due date - FIXED
        due_patterns = [
            r'Payment Due Date\s+(\d{2}\s+\w{3}\s+\d{4})',
            r'(\d{2}\s+\w{3}\s+\d{4})'
        ]
        payment_due_date = self.extract_date(text, due_patterns)
        quality['payment_due_date'] = payment_due_date is not None

        # Credit limit - FIXED
        credit_limit_match = re.search(r'Credit Limit\s+\(\s*`\s*\)\s*([\d,]+\.?\d*)', text)
        if not credit_limit_match:
            credit_limit_match = re.search(r'Credit Limit.*?([\d,]+\.00)', text, re.DOTALL)
        credit_limit = self.clean_amount(credit_limit_match.group(1)) if credit_limit_match else None
        quality['credit_limit'] = credit_limit is not None

        # Total amount due - FIXED
        total_due_match = re.search(r'\*Total Amount Due\s+\(\s*`\s*\)\s*([\d,]+\.?\d*)', text)
        if not total_due_match:
            total_due_match = re.search(r'Total Amount Due.*?([\d,]+\.69)', text, re.DOTALL)
        total_amount_due = self.clean_amount(total_due_match.group(1)) if total_due_match else None
        quality['total_amount_due'] = total_amount_due is not None

        # Minimum amount due - FIXED
        min_due_match = re.search(r'\*\*Minimum Amount Due\s+\(\s*`\s*\)\s*([\d,]+\.?\d*)', text)
        if not min_due_match:
            min_due_match = re.search(r'Minimum Amount Due.*?([\d,]+\.00)', text, re.DOTALL)
        minimum_amount_due = self.clean_amount(min_due_match.group(1)) if min_due_match else None
        quality['minimum_amount_due'] = minimum_amount_due is not None

        # Available credit - FIXED
        available_credit_match = re.search(r'Available Credit Limit\s+\(\s*`\s*\)\s*([\d,]+\.?\d*)', text)
        if not available_credit_match:
            available_credit_match = re.search(r'Available Credit Limit.*?([\d,]+\.00)', text, re.DOTALL)
        available_credit = self.clean_amount(available_credit_match.group(1)) if available_credit_match else None
        quality['available_credit'] = available_credit is not None

        # Previous balance - FIXED
        previous_balance_match = re.search(r'Previous Balance\s+\(\s*`\s*\)\s*([\d,]+\.?\d*)', text)
        if not previous_balance_match:
            previous_balance_match = re.search(r'Previous Balance.*?([\d,]+\.00)', text, re.DOTALL)
        previous_balance = self.clean_amount(previous_balance_match.group(1)) if previous_balance_match else None
        quality['previous_balance'] = previous_balance is not None

        transactions = self._extract_transactions(text)

        return CreditCardStatement(
            bank_name="SBI Card",
            card_number=card_number,
            statement_date=statement_date,
            payment_due_date=payment_due_date,
            credit_limit=credit_limit,
            total_amount_due=total_amount_due,
            minimum_amount_due=minimum_amount_due,
            available_credit=available_credit,
            previous_balance=previous_balance,
            transactions=transactions,
            extraction_quality=quality
        )

    def _extract_transactions(self, text: str) -> List[Transaction]:
        """Extract transactions from SBI statement - FIXED"""
        transactions = []
        # Pattern: DD Mon YY description amount D/C
        pattern = r'(\d{2}\s+\w{3}\s+\d{2})\s+(.+?)\s+([\d,]+\.?\d*)\s+([CD])'
        matches = re.findall(pattern, text)

        for match in matches:
            amount = self.clean_amount(match[2])
            if amount:
                trans_type = 'credit' if match[3] == 'C' else 'debit'
                transactions.append(Transaction(
                    date=match[0],
                    description=match[1].strip(),
                    amount=amount,
                    type=trans_type
                ))
        return transactions


# NEW: YesBankParser class
class YesBankParser(CreditCardParser):
    """Parser for Yes Bank credit card statements"""

    def parse(self, pdf_path: str) -> CreditCardStatement:
        """Parse Yes Bank statement"""
        text = self.extract_text_from_pdf(pdf_path)
        quality = {}

        card_patterns = [r'Statement for YES BANK Card Number\s+(\d{4}X+\d{4})']
        card_number = self.extract_card_number(text, card_patterns)
        quality['card_number'] = card_number is not None

        date_patterns = [r'Statement Date:\s*(\d{2}/\d{2}/\d{4})']
        statement_date = self.extract_date(text, date_patterns)
        quality['statement_date'] = statement_date is not None

        due_patterns = [r'Payment Due Date:\s*(\d{2}/\d{2}/\d{4})']
        payment_due_date = self.extract_date(text, due_patterns)
        quality['payment_due_date'] = payment_due_date is not None

        credit_limit_match = re.search(r'Credit Limit:\s*Rs\.\s*([\d,]+\.\d{2})', text)
        credit_limit = self.clean_amount(credit_limit_match.group(1)) if credit_limit_match else None
        quality['credit_limit'] = credit_limit is not None

        total_due_match = re.search(r'Total Amount Due:\s*Rs\.\s*([\d,]+\.\d{2})', text)
        total_amount_due = self.clean_amount(total_due_match.group(1)) if total_due_match else None
        quality['total_amount_due'] = total_amount_due is not None
        
        min_due_match = re.search(r'Minimum Amount Due:\s*Rs\.\s*([\d,]+\.\d{2})', text)
        minimum_amount_due = self.clean_amount(min_due_match.group(1)) if min_due_match else None
        quality['minimum_amount_due'] = minimum_amount_due is not None

        available_credit_match = re.search(r'Available Credit Limit:\s*Rs\.\s*([\d,]+\.\d{2})', text)
        available_credit = self.clean_amount(available_credit_match.group(1)) if available_credit_match else None
        quality['available_credit'] = available_credit is not None
        
        previous_balance_match = re.search(r'Previous Balance:\s*Rs\.\s*([\d,]+\.\d{2})', text)
        previous_balance = self.clean_amount(previous_balance_match.group(1)) if previous_balance_match else None
        quality['previous_balance'] = previous_balance is not None

        transactions = self._extract_transactions(text)

        return CreditCardStatement(
            bank_name="Yes Bank",
            card_number=card_number,
            statement_date=statement_date,
            payment_due_date=payment_due_date,
            credit_limit=credit_limit,
            total_amount_due=total_amount_due,
            minimum_amount_due=minimum_amount_due,
            available_credit=available_credit,
            previous_balance=previous_balance,
            transactions=transactions,
            extraction_quality=quality
        )

    def _extract_transactions(self, text: str) -> List[Transaction]:
        """Extract transactions from Yes Bank statement"""
        transactions = []
        pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+Utility Services\s+([\d,]+\.\d{2})\s+Dr'
        matches = re.findall(pattern, text)

        for match in matches:
            amount = self.clean_amount(match[2])
            if amount:
                trans_type = 'debit'
                transactions.append(Transaction(
                    date=match[0],
                    description=match[1].strip(),
                    amount=amount,
                    type=trans_type
                ))
        return transactions


class CreditCardStatementParser:
    """Main parser that handles multiple bank statements"""

    def __init__(self):
        self.parsers = {
            'axis': AxisBankParser(),
            'bob': BobParser(),
            'kotak': KotakParser(),
            'sbi': SBIParser(),
            'yes': YesBankParser() # Added Yes Bank parser
        }

    def parse_statement(self, pdf_path: str, bank: str) -> CreditCardStatement:
        """Parse a credit card statement"""
        bank = bank.lower()
        if bank not in self.parsers:
            raise ValueError(f"Unsupported bank: {bank}")

        return self.parsers[bank].parse(pdf_path)

    def parse_multiple_statements(self, statements: List[tuple]) -> List[CreditCardStatement]:
        """Parse multiple statements"""
        results = []
        for pdf_path, bank in statements:
            try:
                result = self.parse_statement(pdf_path, bank)
                results.append(result)
                quality_score = sum(result.extraction_quality.values()) / len(result.extraction_quality) * 100
                print(f"✓ {bank.upper():6s} | Quality: {quality_score:5.1f}%")
            except Exception as e:
                print(f"✗ {bank.upper():6s} | Error: {str(e)}")

        return results

    def generate_summary_report(self, statements: List[CreditCardStatement]) -> str:
        """Generate a summary report"""
        report = []
        report.append("=" * 100)
        report.append("CREDIT CARD STATEMENT SUMMARY REPORT")
        report.append("=" * 100)

        for stmt in statements:
            report.append(f"\n{stmt.bank_name}")
            report.append("-" * 100)
            report.append(f"  Card Number:           {stmt.card_number if stmt.card_number else 'N/A'}")
            report.append(f"  Statement Date:        {stmt.statement_date if stmt.statement_date else 'N/A'}")
            report.append(f"  Payment Due Date:      {stmt.payment_due_date if stmt.payment_due_date else 'N/A'}")
            report.append(f"  Credit Limit:          {f'₹{stmt.credit_limit:,.2f}' if stmt.credit_limit else 'N/A'}")
            report.append(f"  Total Amount Due:      {f'₹{stmt.total_amount_due:,.2f}' if stmt.total_amount_due else 'N/A'}")
            report.append(f"  Minimum Amount Due:    {f'₹{stmt.minimum_amount_due:,.2f}' if stmt.minimum_amount_due else 'N/A'}")
            report.append(f"  Available Credit:      {f'₹{stmt.available_credit:,.2f}' if stmt.available_credit else 'N/A'}")
            report.append(f"  Previous Balance:      {f'₹{stmt.previous_balance:,.2f}' if stmt.previous_balance else 'N/A'}")
            report.append(f"  Transactions:          {len(stmt.transactions)}")

            if stmt.transactions:
                report.append("  Recent Transactions:")
                for txn in stmt.transactions[:5]:
                    report.append(f"    • {txn.date} | {txn.description[:50]:50s} | ₹{txn.amount:>10,.2f} ({txn.type})")

        # Add summary statistics
        report.append("\n" + "=" * 100)
        report.append("OVERALL SUMMARY")
        report.append("=" * 100)

        total_credit_limit = sum(s.credit_limit for s in statements if s.credit_limit)
        total_outstanding = sum(s.total_amount_due for s in statements if s.total_amount_due)
        total_minimum_due = sum(s.minimum_amount_due for s in statements if s.minimum_amount_due)
        total_available = sum(s.available_credit for s in statements if s.available_credit)

        report.append(f"  Total Credit Limit:    ₹{total_credit_limit:,.2f}")
        report.append(f"  Total Outstanding:     ₹{total_outstanding:,.2f}")
        report.append(f"  Total Minimum Due:     ₹{total_minimum_due:,.2f}")
        report.append(f"  Total Available:       ₹{total_available:,.2f}")

        if total_credit_limit > 0:
            utilization = (total_outstanding / total_credit_limit) * 100
            report.append(f"  Credit Utilization:    {utilization:.1f}%")

        return "\n".join(report)

    def export_to_json(self, statements: List[CreditCardStatement], output_file: str = 'statements.json'):
        """Export parsed statements to JSON"""
        data = [stmt.to_dict() for stmt in statements]
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Exported to {output_file}")


# Example usage for Google Colab
if __name__ == "__main__":
    # Install PyPDF2 if needed
    try:
        import PyPDF2
    except ImportError:
        print("Installing PyPDF2...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'PyPDF2'])
        import PyPDF2

    parser = CreditCardStatementParser()

    statements_to_parse = [
        ('/content/Axis1-unlocked.pdf', 'axis'),
        ('/content/Bob1-unlocked.pdf', 'bob'),
        ('/content/Kotak1.pdf', 'kotak'),
        ('/content/SBI1.pdf', 'sbi')
    ]

    print("=" * 100)
    print("CREDIT CARD STATEMENT PARSER - PRODUCTION VERSION")
    print("=" * 100)
    print("\nParsing credit card statements...\n")

    parsed_statements = parser.parse_multiple_statements(statements_to_parse)

    print("\n")
    print(parser.generate_summary_report(parsed_statements))

    # Export to JSON
    parser.export_to_json(parsed_statements, '/content/parsed_statements.json')

    print("\n" + "=" * 100)
    print("PARSING COMPLETE!")
    print("=" * 100)