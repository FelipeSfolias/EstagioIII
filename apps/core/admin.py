from django.contrib import admin

from .models import KanbanAuditLog


@admin.register(KanbanAuditLog)
class KanbanAuditLogAdmin(admin.ModelAdmin):
    list_display  = ["card", "usuario", "coluna_de", "coluna_para", "criado_em"]
    list_filter   = ["coluna_para", "criado_em"]
    readonly_fields = ["card", "usuario", "coluna_de", "coluna_para", "criado_em"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
