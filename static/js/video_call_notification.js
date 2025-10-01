// Video Call Notification Component
class VideoCallNotification extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            showNotification: false,
            callData: null,
        };
        this.ws = null;
    }

    componentDidMount() {
        this.connectWebSocket();
    }

    componentWillUnmount() {
        if (this.ws) {
            this.ws.close();
        }
    }

    connectWebSocket = () => {
        const token = localStorage.getItem('authToken'); // Assuming token is stored
        this.ws = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}`);

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'notification' && data.notification_type === 'video_call') {
                this.setState({
                    showNotification: true,
                    callData: data,
                });
            }
        };

        this.ws.onclose = () => {
            // Reconnect logic if needed
        };
    };

    acceptCall = () => {
        // Fetch call details and redirect to call room
        fetch(`/api/video-calls/${this.state.callData.related_id}/`, {
            headers: {
                'Authorization': `Token ${localStorage.getItem('authToken')}`,
            },
        })
        .then(response => response.json())
        .then(data => {
            // Redirect to call room with roomId
            window.location.href = `/video-call/${data.room_id}/`;
        });
    };

    declineCall = () => {
        this.setState({ showNotification: false });
    };

    render() {
        if (!this.state.showNotification) {
            return null;
        }

        return (
            <div className="video-call-notification">
                <div className="notification-popup">
                    <h3>Video Call Invitation</h3>
                    <p>{this.state.callData.message}</p>
                    <button onClick={this.acceptCall}>Join Call</button>
                    <button onClick={this.declineCall}>Decline</button>
                </div>
            </div>
        );
    }
}

// Usage example:
// <VideoCallNotification />