from rest_framework import permissions

class NotTransferAndUtangPiutang(permissions.BasePermission):


    def has_object_permission(self, request, view, obj):

        if (request.method in ['DELETE','PUT','PATCH']) and (obj.id_transfer or obj.id_utang_piutang):
            return False


        return True