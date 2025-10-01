from rest_framework import serializers
from .models import VideoCallSession

class VideoCallSessionSerializer(serializers.ModelSerializer):
    contract_title = serializers.CharField(source='contract.title', read_only=True)
    initiated_by_name = serializers.CharField(source='initiated_by.get_full_name', read_only=True)
    participants_names = serializers.SerializerMethodField()

    class Meta:
        model = VideoCallSession
        fields = [
            'id', 'room_id', 'contract', 'contract_title', 'initiated_by', 'initiated_by_name',
            'participants', 'participants_names', 'start_time', 'end_time', 'status'
        ]
        read_only_fields = ['id', 'room_id', 'start_time', 'end_time', 'initiated_by']

    def get_participants_names(self, obj):
        return [user.get_full_name() or user.username for user in obj.participants.all()]