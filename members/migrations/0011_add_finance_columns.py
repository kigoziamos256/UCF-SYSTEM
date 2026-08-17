from django.db import migrations, models
import django.utils.timezone
import imagekit.models.fields
from imagekit.processors import ResizeToFill

class Migration(migrations.Migration):

    dependencies = [
        ('members', '0010_add_default_currency'),  # your last migration
    ]

    operations = [

        # =========================================
        # 1. CREATE SUPPORT MODELS FIRST
        # =========================================

        migrations.CreateModel(
            name='IncomeCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('code', models.CharField(help_text='e.g., INC-001', max_length=20, unique=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Income Categories',
                'ordering': ['name'],
            },
        ),

        migrations.CreateModel(
            name='ExpenseCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('category_type', models.CharField(choices=[
                    ('direct', 'Direct Cost'),
                    ('overhead', 'Shared Overhead'),
                    ('capital', 'Capital Expenditure'),
                    ('operational', 'Operational')
                ], default='operational', max_length=20)),
                ('code', models.CharField(help_text='e.g., EXP-001', max_length=20, unique=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Expense Categories',
                'ordering': ['name'],
            },
        ),

        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('contact_person', models.CharField(blank=True, max_length=100)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('address', models.TextField(blank=True)),
                ('tax_id', models.CharField(blank=True, help_text='Tax/VAT registration number', max_length=50)),
                ('payment_terms', models.CharField(blank=True, help_text='e.g., Net 30', max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),

        # =========================================
        # 2. NOW ADD FIELDS TO FinancialTransaction
        # =========================================

        migrations.AddField(
            model_name='financialtransaction',
            name='income_sub_type',
            field=models.CharField(blank=True, choices=[
                ('tithe', 'Tithe'),
                ('offertory', 'Offertory'),
                ('donation', 'Donation'),
                ('offering', 'Offering'),
                ('special', 'Special Offering'),
                ('facility_rent', 'Facility Rent'),
                ('cafe_sales', 'Cafe Sales'),
                ('gym_membership', 'Gym Membership'),
                ('gym_day_pass', 'Gym Day Pass'),
                ('gym_training', 'Gym Training/Classes'),
                ('catering', 'Catering'),
                ('other_income', 'Other Income'),
            ], max_length=50, null=True),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='expense_sub_type',
            field=models.CharField(blank=True, choices=[
                ('rent', 'Rent'),
                ('utilities', 'Utilities'),
                ('salaries', 'Salaries/Wages'),
                ('equipment', 'Equipment'),
                ('maintenance', 'Maintenance'),
                ('travel', 'Travel'),
                ('supplies', 'Supplies'),
                ('marketing', 'Marketing'),
                ('insurance', 'Insurance'),
                ('taxes', 'Taxes'),
                ('cafe_supplies', 'Cafe Supplies'),
                ('gym_equipment', 'Gym Equipment'),
                ('other_expense', 'Other Expense'),
            ], max_length=50, null=True),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='vendor',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='transactions', to='members.vendor'),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='income_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='transactions', to='members.incomecategory'),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='expense_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='transactions', to='members.expensecategory'),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='finance_transactions', to='members.department'),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='invoice_number',
            field=models.CharField(blank=True, help_text='Vendor invoice number', max_length=100),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='purchase_order_number',
            field=models.CharField(blank=True, max_length=100),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='due_date',
            field=models.DateField(blank=True, help_text='Payment due date', null=True),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='paid_date',
            field=models.DateField(blank=True, help_text='Date payment was made', null=True),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='is_paid',
            field=models.BooleanField(default=False),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='bank_reference',
            field=models.CharField(blank=True, help_text='Bank transaction reference', max_length=100),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='approved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='approved_transactions', to='auth.user'),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='is_approved',
            field=models.BooleanField(default=False),
        ),

        migrations.AddField(
            model_name='financialtransaction',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),

        # =========================================
        # 3. ALTER EXISTING FIELDS (if needed)
        # =========================================

        migrations.AlterField(
            model_name='financialtransaction',
            name='transaction_type',
            field=models.CharField(choices=[('income', 'Income'), ('expense', 'Expense'), ('transfer', 'Transfer')], max_length=20),
        ),

        migrations.AlterField(
            model_name='financialtransaction',
            name='payment_method',
            field=models.CharField(choices=[
                ('cash', 'Cash'),
                ('mobile_money', 'Mobile Money'),
                ('bank_transfer', 'Bank Transfer'),
                ('cheque', 'Cheque'),
                ('card', 'Card'),
                ('mpesa', 'M-Pesa'),
                ('airtel_money', 'Airtel Money')
            ], default='cash', max_length=50),
        ),

        migrations.AlterField(
            model_name='financialtransaction',
            name='payer_name',
            field=models.CharField(blank=True, max_length=200),
        ),

        # =========================================
        # 4. CREATE OTHER FINANCE MODELS (if missing)
        # =========================================

        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(choices=[('church', 'Church'), ('cafe', 'Cafe'), ('gym', 'Gym'), ('shared', 'Shared Overhead')], max_length=20)),
                ('frequency', models.CharField(choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')], default='monthly', max_length=20)),
                ('period_month', models.IntegerField(blank=True, help_text='1-12 for monthly', null=True)),
                ('period_year', models.IntegerField()),
                ('budgeted_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('income_category', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='budgets', to='members.incomecategory')),
                ('expense_category', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='budgets', to='members.expensecategory')),
            ],
            options={
                'ordering': ['-period_year', 'period_month'],
                'unique_together': {('department', 'income_category', 'expense_category', 'period_month', 'period_year')},
            },
        ),

        migrations.CreateModel(
            name='ExpenseRequisition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('estimated_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('purchased', 'Purchased'), ('paid', 'Paid')], default='draft', max_length=20)),
                ('rejected_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='approved_requisitions', to='auth.user')),
                ('department', models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL, related_name='requisitions', to='members.department')),
                ('expense_category', models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL, related_name='requisitions', to='members.expensecategory')),
                ('requested_by', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='requisitions', to='auth.user')),
                ('vendor', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='requisitions', to='members.vendor')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),

        migrations.CreateModel(
            name='BankReconciliation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bank_name', models.CharField(max_length=100)),
                ('account_number', models.CharField(blank=True, max_length=50)),
                ('statement_date', models.DateField()),
                ('statement_balance', models.DecimalField(decimal_places=2, max_digits=12)),
                ('ledger_balance', models.DecimalField(decimal_places=2, max_digits=12)),
                ('difference', models.DecimalField(decimal_places=2, help_text='Statement - Ledger', max_digits=12)),
                ('notes', models.TextField(blank=True)),
                ('is_reconciled', models.BooleanField(default=False)),
                ('reconciled_at', models.DateTimeField(auto_now_add=True)),
                ('reconciled_by', models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL, related_name='reconciliations', to='auth.user')),
            ],
            options={
                'ordering': ['-statement_date'],
            },
        ),
    ]
