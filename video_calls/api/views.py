from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models import VideoCallSession
from ..serializers import VideoCallSessionSerializer
from ..permissions import CanCreateVideoCall
from projects.models import Project
from notifications.models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class CreateVideoCallView(generics.CreateAPIView):
    serializer_class = VideoCallSessionSerializer
    permission_classes = [IsAuthenticated, CanCreateVideoCall]

    def create(self, request, *args, **kwargs):
        contract_id = request.data.get('contract')
        contract = get_object_or_404(Project, id=contract_id)

        # Check if contract has client and expert
        if not contract.client or not contract.expert:
            return Response({'error': 'Contract must have both client and expert'}, status=status.HTTP_400_BAD_REQUEST)

        # Create session
        session = VideoCallSession.objects.create(
            contract=contract,
            initiated_by=request.user
        )
        session.participants.add(request.user, contract.client, contract.expert)
        session.save()

        print(f"Created video call session {session.id} with room_id {session.room_id}")

        # Send notifications
        channel_layer = get_channel_layer()
        for participant in [contract.client, contract.expert]:
            notification = Notification.objects.create(
                recipient=participant,
                title='Video Call Invitation',
                message=f'Admin has initiated a video call for contract: {contract.title}',
                notification_type='video_call',
                related_object_id=session.id
            )
            # Store room_id in the message for easy access
            notification.message = f'Admin has initiated a video call for contract: {contract.title}. Room: {session.room_id}'
            notification.save()
            print(f"Created notification {notification.id} for user {participant.username} with related_object_id={session.id}")
            async_to_sync(channel_layer.group_send)(
                f'notifications_{participant.id}',
                {
                    'type': 'notification_message',
                    'message': f'Admin has initiated a video call for contract: {contract.title}',
                    'notification_type': 'video_call',
                    'related_id': session.id
                }
            )

        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class VideoCallDetailView(generics.RetrieveAPIView):
    serializer_class = VideoCallSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return VideoCallSession.objects.filter(participants=self.request.user)

class EndVideoCallView(generics.GenericAPIView):
    serializer_class = VideoCallSessionSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        session = get_object_or_404(VideoCallSession, id=kwargs['pk'])
        if request.user != session.initiated_by:
            return Response({'error': 'Only the initiator can end the call'}, status=status.HTTP_403_FORBIDDEN)

        session.end_call()
        serializer = self.get_serializer(session)
        return Response(serializer.data)