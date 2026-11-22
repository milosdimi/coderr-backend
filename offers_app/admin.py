from django.contrib import admin

from .models import Offer, OfferDetail


class OfferDetailInline(admin.TabularInline):
    """Shows the three offer details directly inside the offer page."""

    model = OfferDetail
    extra = 0


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Admin list of all offers with their details inline."""

    list_display = ['title', 'user', 'created_at', 'updated_at']
    search_fields = ['title', 'description', 'user__username']
    inlines = [OfferDetailInline]


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """Admin list of all offer details, filterable by type."""

    list_display = ['offer', 'offer_type', 'price', 'delivery_time_in_days']
    list_filter = ['offer_type']
    search_fields = ['title', 'offer__title']
