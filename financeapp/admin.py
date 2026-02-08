from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Portfolio)
admin.site.register(Holding)
admin.site.register(Fund)
admin.site.register(SectorAllocation)
admin.site.register(RegionAllocation)
admin.site.register(BudgetItem)