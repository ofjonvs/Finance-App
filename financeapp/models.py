from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils import timezone
import datetime

# Create your models here.

class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    name = models.CharField(max_length=100, help_text="Name of the portfolio (e.g., 'Retirement Fund')")
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

class Fund(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True, help_text="Name of the fund (e.g., 'Vanguard S&P 500 ETF')")
    ticker = models.CharField(max_length=10, unique=True, help_text="Fund ticker symbol (e.g., 'VOO')")
    isin = models.CharField(max_length=20, help_text="Fund isin", blank=True, null=True)
    nav = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, help_text="Net Asset Value per share (auto-populated)")
    def defaultDate(): return timezone.now()-datetime.timedelta(hours=11)
    last_updated = models.DateField(default=defaultDate)
    
    # Fund type allocations (as percentages, 0–100)
    domestic = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage allocated to domestic securities"
    )
    international = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage allocated to international securities"
    )
    large_cap_growth = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage allocated to large-cap growth"
    )
    large_cap_value = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage allocated to large-cap value"
    )
    large_cap_blend = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage allocated to large-cap blend"
    )
    mid_cap_growth = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage allocated to mid-cap growth"
    )
    mid_cap_value = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage allocated to mid-cap value"
    )
    mid_cap_blend = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage allocated to mid-cap blend"
    )
    small_cap_growth = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage allocated to small-cap growth"
    )
    small_cap_value = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage allocated to small-cap value"
    )
    small_cap_blend = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage allocated to small-cap blend"
    )

    def __str__(self):
        return f"{self.name} ({self.ticker})"

    def clean(self):
        """
        Validate that fund type allocations sum to approximately 100% (allowing for rounding errors).
        """
        total_allocation_cap = (
            self.large_cap_growth + self.large_cap_value + self.large_cap_blend +
            self.mid_cap_growth + self.mid_cap_value + self.mid_cap_blend +
            self.small_cap_growth + self.small_cap_value + self.small_cap_blend
        )
        domestic_total = (
            self.domestic + self.international
        )
        if not (99.5 <= total_allocation_cap <= 100.5) and (99.5 <= domestic_total <= 100.5):  # Allow small rounding errors
            raise ValueError(
                f"Fund type allocations must sum to approximately 100%"
            )
        
class SectorAllocation(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, related_name='sector_allocations')
    sector = models.CharField(
        max_length=100,
        help_text="Name of the sector (e.g., 'Technology', 'Healthcare')"
    )
    percentage = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage allocated to this sector"
    )

    class Meta:
        unique_together = ['fund', 'sector']  # Prevent duplicate sectors per fund

    def __str__(self):
        return f"{self.sector}: {self.percentage}% ({self.fund.ticker})"

class RegionAllocation(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, related_name='region_allocations')
    region = models.CharField(
        max_length=100,
        help_text="Name of the region (e.g., 'North America', 'Europe')"
    )
    percentage = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage allocated to this region"
    )

    class Meta:
        unique_together = ['fund', 'region']  # Prevent duplicate regions per fund

    def __str__(self):
        return f"{self.region}: {self.percentage}% ({self.fund.ticker})"
    
class Holding(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, help_text="The fund held in this portfolio")
    shares = models.DecimalField(max_digits=15, decimal_places=4, default=Decimal(0.0), help_text="Number of shares held (auto-calculated if not provided)")

    def __str__(self):
        return f"{self.fund.ticker} in {self.portfolio.name} for {self.portfolio.user.username}"

class BudgetItem(models.Model):
    CATEGORY_CHOICES = [
        ('Need', 'Need'),
        ('Want', 'Want'),
    ]
    MONTH_CHOICES = [
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December'),
        ('Recurring', 'Recurring'),
    ]
    date = models.DateField(auto_now_add=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budget_items')
    item = models.CharField(max_length=100, help_text="Name of the expense")
    category = models.CharField(
        max_length=4,
        choices=CATEGORY_CHOICES,
        help_text="Category of the expense"
    )
    subcategory = models.CharField(max_length=50, help_text="Subcategory (e.g., 'food')")
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text="Amount spent"
    )
    # month = models.CharField(
    #     max_length=20,
    #     choices=MONTH_CHOICES,
    #     help_text="Month of the expense"
    # )

    def __str__(self):
        return f"{self.user.username} {self.item}: {self.amount} ({self.category}, {self.date.month}/{self.date.year})"