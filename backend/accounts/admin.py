from django.contrib import admin
from .models import TravelerProfile


@admin.register(TravelerProfile)
class TravelerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "nationality", "preferred_budget_tier", "is_verified_guide", "updated_at")
    search_fields = ("user__username", "user__email", "nationality")
