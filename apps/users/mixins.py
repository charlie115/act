class UserUUIDSerializerMixin(object):

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = instance.user.uuid

        return data
