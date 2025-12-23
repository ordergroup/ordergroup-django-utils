from django.http import HttpResponse
from django.views import View

from og_django_utils.utils.decorators import class_view_decorator


def test_class_view_decorator():
    """Test class_view_decorator functionality"""

    # Create a simple decorator
    def test_decorator(view_func):
        def wrapper(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            response["X-Test-Header"] = "decorated"
            return response

        return wrapper

    # Apply decorator to a class-based view
    @class_view_decorator(test_decorator)
    class TestView(View):
        def get(self, request):
            return HttpResponse("test")

    # Verify the decorator was applied
    assert hasattr(TestView, "dispatch")
    # The dispatch method should be wrapped
    assert TestView.dispatch is not View.dispatch


def test_class_view_decorator_preserves_view():
    """Test that class_view_decorator preserves the view class"""

    def dummy_decorator(view_func):
        return view_func

    @class_view_decorator(dummy_decorator)
    class TestView(View):
        test_attribute = "test_value"

        def get(self, request):
            return HttpResponse("test")

    # Verify class attributes are preserved
    assert hasattr(TestView, "test_attribute")
    assert TestView.test_attribute == "test_value"
    assert hasattr(TestView, "get")
