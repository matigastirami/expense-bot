import io
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable

from packages.agent.schemas import MonthlyReport, TransactionInfo, BalanceInfo


class PDFReportService:
    """Service for generating PDF financial reports."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the reports."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#2C3E50')
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#34495E')
        ))

        # Summary style
        self.styles.add(ParagraphStyle(
            name='SummaryText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            textColor=colors.HexColor('#2C3E50')
        ))

    def generate_monthly_report_pdf(self, report: MonthlyReport, user_id: int, transactions: Optional[List[TransactionInfo]] = None) -> bytes:
        """Generate a PDF monthly report."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)

        # Container for the 'Flowable' objects
        elements = []

        # Title
        title = Paragraph(f"Monthly Financial Report", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Report period
        period = Paragraph(f"<b>Period:</b> {report.month:02d}/{report.year}",
                          self.styles['SummaryText'])
        elements.append(period)
        elements.append(Spacer(1, 6))

        # Generation date
        gen_date = Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                           self.styles['SummaryText'])
        elements.append(gen_date)
        elements.append(Spacer(1, 20))

        # Financial Summary
        elements.append(Paragraph("Financial Summary", self.styles['CustomSubtitle']))

        # Summary data
        summary_data = [
            ['Metric', 'Amount', 'Currency'],
            ['Total Income', f"{report.total_income:,.2f}", 'USD'],
            ['Total Expenses', f"{report.total_expenses:,.2f}", 'USD'],
            ['Net Savings', f"{report.net_savings:,.2f}", 'USD']
        ]

        summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ]))

        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        # Largest Transaction
        if report.largest_transaction:
            elements.append(Paragraph("Largest Transaction", self.styles['CustomSubtitle']))

            largest_data = [
                ['Field', 'Value'],
                ['Type', report.largest_transaction.type.title()],
                ['Amount', f"{report.largest_transaction.amount:,.2f} {report.largest_transaction.currency}"],
                ['Date', report.largest_transaction.date.strftime('%Y-%m-%d')],
                ['Description', report.largest_transaction.description or 'N/A'],
            ]

            if report.largest_transaction.account_from:
                largest_data.append(['From Account', report.largest_transaction.account_from])
            if report.largest_transaction.account_to:
                largest_data.append(['To Account', report.largest_transaction.account_to])

            largest_table = Table(largest_data, colWidths=[2*inch, 3*inch])
            largest_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E74C3C')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
            ]))

            elements.append(largest_table)
            elements.append(Spacer(1, 20))

        # Current Balances
        if report.balances:
            elements.append(Paragraph("Current Account Balances", self.styles['CustomSubtitle']))

            balance_data = [['Account', 'Currency', 'Balance']]
            for balance in report.balances:
                balance_data.append([
                    balance.account_name,
                    balance.currency,
                    f"{balance.balance:,.2f}"
                ])

            balance_table = Table(balance_data, colWidths=[2*inch, 1*inch, 1.5*inch])
            balance_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
            ]))

            elements.append(balance_table)

        # Add transaction breakdown if transactions are provided
        if transactions:
            elements.append(Spacer(1, 20))

            # Organize transactions by type - expenses first, then income, then others
            expenses = [t for t in transactions if t.type == 'expense']
            income = [t for t in transactions if t.type == 'income']
            transfers = [t for t in transactions if t.type == 'transfer']
            conversions = [t for t in transactions if t.type == 'conversion']

            # Expenses section
            if expenses:
                elements.append(Paragraph("💰 Expenses", self.styles['CustomSubtitle']))
                expenses_data = [['Date', 'Amount', 'Currency', 'Account', 'Description']]

                for expense in sorted(expenses, key=lambda t: t.date, reverse=True):
                    expenses_data.append([
                        expense.date.strftime('%m/%d'),
                        f"{expense.amount:,.2f}",
                        expense.currency,
                        expense.account_from or 'N/A',
                        (expense.description or 'N/A')[:35] + '...' if expense.description and len(expense.description) > 35 else (expense.description or 'N/A')
                    ])

                expenses_table = Table(expenses_data, colWidths=[0.7*inch, 0.8*inch, 0.6*inch, 1*inch, 2.4*inch], repeatRows=1)
                expenses_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E74C3C')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FADBD8')]),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))

                elements.append(expenses_table)
                elements.append(Spacer(1, 15))

            # Income section
            if income:
                elements.append(Paragraph("💵 Income", self.styles['CustomSubtitle']))
                income_data = [['Date', 'Amount', 'Currency', 'Account', 'Description']]

                for inc in sorted(income, key=lambda t: t.date, reverse=True):
                    income_data.append([
                        inc.date.strftime('%m/%d'),
                        f"{inc.amount:,.2f}",
                        inc.currency,
                        inc.account_to or 'N/A',
                        (inc.description or 'N/A')[:35] + '...' if inc.description and len(inc.description) > 35 else (inc.description or 'N/A')
                    ])

                income_table = Table(income_data, colWidths=[0.7*inch, 0.8*inch, 0.6*inch, 1*inch, 2.4*inch], repeatRows=1)
                income_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#D5F4E6')]),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))

                elements.append(income_table)
                elements.append(Spacer(1, 15))

            # Transfers section
            if transfers:
                elements.append(Paragraph("🔄 Transfers", self.styles['CustomSubtitle']))
                transfers_data = [['Date', 'Amount', 'Currency', 'From', 'To', 'Description']]

                for transfer in sorted(transfers, key=lambda t: t.date, reverse=True):
                    transfers_data.append([
                        transfer.date.strftime('%m/%d'),
                        f"{transfer.amount:,.2f}",
                        transfer.currency,
                        transfer.account_from or 'N/A',
                        transfer.account_to or 'N/A',
                        (transfer.description or 'N/A')[:25] + '...' if transfer.description and len(transfer.description) > 25 else (transfer.description or 'N/A')
                    ])

                transfers_table = Table(transfers_data, colWidths=[0.7*inch, 0.7*inch, 0.5*inch, 0.9*inch, 0.9*inch, 1.8*inch], repeatRows=1)
                transfers_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#D6EAF8')]),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))

                elements.append(transfers_table)
                elements.append(Spacer(1, 15))

            # Conversions section
            if conversions:
                elements.append(Paragraph("💱 Conversions", self.styles['CustomSubtitle']))
                conversions_data = [['Date', 'From Amount', 'From Currency', 'Account', 'Description']]

                for conversion in sorted(conversions, key=lambda t: t.date, reverse=True):
                    conversions_data.append([
                        conversion.date.strftime('%m/%d'),
                        f"{conversion.amount:,.2f}",
                        conversion.currency,
                        conversion.account_from or conversion.account_to or 'N/A',
                        (conversion.description or 'N/A')[:35] + '...' if conversion.description and len(conversion.description) > 35 else (conversion.description or 'N/A')
                    ])

                conversions_table = Table(conversions_data, colWidths=[0.7*inch, 0.8*inch, 0.6*inch, 1*inch, 2.4*inch], repeatRows=1)
                conversions_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9B59B6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#E8DAEF')]),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))

                elements.append(conversions_table)

        # Build PDF
        doc.build(elements)

        # Get the value of the BytesIO buffer and return it
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data

    def generate_transactions_report_pdf(self, transactions: List[TransactionInfo],
                                       start_date: datetime, end_date: datetime,
                                       user_id: int, account_name: Optional[str] = None) -> bytes:
        """Generate a PDF report with detailed transaction list."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)

        elements = []

        # Title
        title_text = "Transaction Report"
        if account_name:
            title_text += f" - {account_name}"

        title = Paragraph(title_text, self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Report period
        period = Paragraph(f"<b>Period:</b> {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                          self.styles['SummaryText'])
        elements.append(period)
        elements.append(Spacer(1, 6))

        # Generation date
        gen_date = Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                           self.styles['SummaryText'])
        elements.append(gen_date)
        elements.append(Spacer(1, 6))

        # Transaction count
        count = Paragraph(f"<b>Total Transactions:</b> {len(transactions)}",
                         self.styles['SummaryText'])
        elements.append(count)
        elements.append(Spacer(1, 20))

        if not transactions:
            no_data = Paragraph("No transactions found for the specified period.",
                              self.styles['SummaryText'])
            elements.append(no_data)
        else:
            # Summary by type
            income_total = sum(t.amount for t in transactions if t.type == 'income')
            expense_total = sum(t.amount for t in transactions if t.type == 'expense')

            if income_total > 0 or expense_total > 0:
                elements.append(Paragraph("Summary by Type", self.styles['CustomSubtitle']))

                summary_data = [
                    ['Transaction Type', 'Count', 'Total Amount'],
                    ['Income',
                     str(len([t for t in transactions if t.type == 'income'])),
                     f"{income_total:,.2f}"],
                    ['Expenses',
                     str(len([t for t in transactions if t.type == 'expense'])),
                     f"{expense_total:,.2f}"],
                    ['Net', '', f"{income_total - expense_total:,.2f}"]
                ]

                summary_table = Table(summary_data, colWidths=[2*inch, 1*inch, 1.5*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
                ]))

                elements.append(summary_table)
                elements.append(Spacer(1, 20))

            # Detailed transactions table
            elements.append(Paragraph("Detailed Transactions", self.styles['CustomSubtitle']))

            # Create transactions table with appropriate column widths
            transaction_data = [['Date', 'Type', 'Amount', 'Currency', 'From', 'To', 'Description']]

            for transaction in sorted(transactions, key=lambda t: t.date, reverse=True):
                transaction_data.append([
                    transaction.date.strftime('%m/%d/%Y'),
                    transaction.type.title(),
                    f"{transaction.amount:,.2f}",
                    transaction.currency,
                    transaction.account_from or '-',
                    transaction.account_to or '-',
                    (transaction.description or 'N/A')[:30] + '...' if transaction.description and len(transaction.description) > 30 else (transaction.description or 'N/A')
                ])

            # Adjust column widths for better fit
            col_widths = [0.8*inch, 0.6*inch, 0.7*inch, 0.5*inch, 0.8*inch, 0.8*inch, 1.8*inch]
            transactions_table = Table(transaction_data, colWidths=col_widths, repeatRows=1)

            transactions_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8E44AD')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            elements.append(transactions_table)

        # Build PDF
        doc.build(elements)

        # Get the value of the BytesIO buffer and return it
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data

    def create_temp_pdf_file(self, pdf_data: bytes, filename_prefix: str = "report") -> str:
        """Create a temporary PDF file and return its path."""
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.pdf',
            prefix=f"{filename_prefix}_"
        )

        temp_file.write(pdf_data)
        temp_file.close()

        return temp_file.name
