from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TravelerProfile
from .serializers import RegisterSerializer, TravelerProfileSerializer, UserSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        username = identifier
        if "@" in identifier:
            matched = User.objects.filter(email__iexact=identifier).first()
            if matched:
                username = matched.username
        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        TravelerProfile.objects.get_or_create(user=user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({"detail": "Logged out successfully."})


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        TravelerProfile.objects.get_or_create(user=request.user)
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        user = request.user
        profile, _ = TravelerProfile.objects.get_or_create(user=user)
        for field in ("first_name", "last_name", "email"):
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()

        profile_data = request.data.get("profile", request.data)
        prof_serializer = TravelerProfileSerializer(profile, data=profile_data, partial=True)
        prof_serializer.is_valid(raise_exception=True)
        prof_serializer.save()
        return Response(UserSerializer(user).data)
