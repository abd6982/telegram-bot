from django.conf import settings
from django.contrib.auth import authenticate
from django.shortcuts import redirect

if 'rest_framework.authtoken' in settings.INSTALLED_APPS:
    from rest_framework import parsers, renderers
    from rest_framework.authtoken.models import Token
    from rest_framework.authtoken.serializers import AuthTokenSerializer
    from rest_framework.decorators import api_view
    from rest_framework.response import Response
    from rest_framework.views import APIView


    @api_view(['POST'])
    def get_token(request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                token, created = Token.objects.get_or_create(user=user)
                request.session['auth-token'] = token.key
                return redirect('core:home', request)
        return redirect(settings.LOGIN_URL)


    class TokenView(APIView):
        throttle_classes = ()
        permission_classes = ()
        parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
        renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
        serializer_class = AuthTokenSerializer

        def post(self, request, *args, **kwargs):
            serializer = self.serializer_class(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})


    get_token = TokenView.as_view()