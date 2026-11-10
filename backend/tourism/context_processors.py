from tourism.models import WishlistItem


def global_nav_context(request):
    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(
            WishlistItem.objects.filter(user=request.user).values_list("place_id", flat=True)
        )
    return {
        "user_wishlist_ids": wishlist_ids,
        "wishlist_count": len(wishlist_ids),
    }
