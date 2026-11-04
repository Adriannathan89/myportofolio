from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsPortfolioOwnerOrReadOnly(BasePermission):
    message = 'You do not have permission to change this award.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if request.method in ('PUT', 'PATCH'):
            return request.user.has_perm('main.change_award')
        if request.method == 'POST':
            return request.user.has_perm('main.add_award')
        if request.method == 'DELETE':
            return request.user.has_perm('main.delete_award')
        return False

class IsPortfolioOwnerOrEditorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        return (
            request.method in ("PUT", "PATCH")
            and request.user.group.filter(name="Editor").exists()
        )