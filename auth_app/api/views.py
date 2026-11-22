"""API views for registration and login."""
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegistrationSerializer


def build_auth_response(user):
    """Return the token and user data the frontend stores after login."""
    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "username": user.username,
        "email": user.email,
        "user_id": user.id,
    }


class RegistrationView(APIView):
    """POST /api/registration/ - create a new customer or business user.

    Open on purpose: a visitor has no account yet. Authentication is
    disabled so an outdated token in the header cannot block the request.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Validate the sign up data, create the user and return a token."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            build_auth_response(user), status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """POST /api/login/ - log in with username and password.

    Open on purpose: the user logs in to receive a token.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Check the credentials and return a token."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response(build_auth_response(user), status=status.HTTP_200_OK)
