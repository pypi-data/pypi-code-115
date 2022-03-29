__all__ = ('Contract', 'PaginationContract')

from rest_framework import serializers


class ContractError(serializers.ValidationError):
    pass


class Contract(serializers.Serializer):

    def is_valid(self, raise_exception=False):
        # This implementation is the same as the default,
        # except that we use lists, rather than dicts, as the empty case.
        assert hasattr(self, 'initial_data'), (
            'Cannot call `.is_valid()` as no `data=` keyword argument was '
            'passed when instantiating the serializer instance.'
        )

        if not hasattr(self, '_validated_data'):
            try:
                self._validated_data = self.run_validation(self.initial_data)
            except ContractError as exc:
                self._validated_data = []
                self._errors = exc.detail
            else:
                self._errors = []

        if self._errors and raise_exception:
            raise ContractError(self.errors)

        return not bool(self._errors)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class PaginationContract(Contract):
    previous = serializers.URLField(allow_null=True)
    next = serializers.URLField(allow_null=True)
    count = serializers.IntegerField()
