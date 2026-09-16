from django.apps import apps


def get_usuario_delegacion(user):
    if not user or not user.is_authenticated:
        return None
    Funcionario = apps.get_model('funcionarios', 'Funcionario')
    try:
        funcionario = Funcionario.objects.select_related('delegacion').get(user=user)
    except Funcionario.DoesNotExist:
        return None
    return funcionario.delegacion


def es_usuario_sin_restriccion(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['Administradores', 'Verificadores']).exists()


class ScopedModelAdmin:
    scope_by = 'delegacion'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if es_usuario_sin_restriccion(request.user):
            return qs
        delegacion = get_usuario_delegacion(request.user)
        if delegacion is None:
            return qs.none()
        return qs.filter(**{self.scope_by: delegacion})

    def _objeto_en_alcance(self, request, obj):
        if obj is None:
            return True
        if es_usuario_sin_restriccion(request.user):
            return True
        delegacion = get_usuario_delegacion(request.user)
        if delegacion is None:
            return False
        valor = obj
        for paso in self.scope_by.split('__'):
            valor = getattr(valor, paso, None)
            if valor is None:
                return False
        return valor == delegacion

    def has_change_permission(self, request, obj=None):
        if not super().has_change_permission(request, obj):
            return False
        return self._objeto_en_alcance(request, obj)

    def has_delete_permission(self, request, obj=None):
        if not super().has_delete_permission(request, obj):
            return False
        return self._objeto_en_alcance(request, obj)
