from rest_framework import viewsets, permissions


class PublicEndpoint(permissions.BasePermission):
    def has_permission(self, request, view):
        return True
