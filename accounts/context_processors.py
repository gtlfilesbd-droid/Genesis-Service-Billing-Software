from .models import UserProfile


def user_profile(request):
    if not request.user.is_authenticated:
        return {'profile': None}
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    return {'profile': profile}
