// Video Call Room Component using Jitsi Meet
class VideoCallRoom extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            isAudioMuted: false,
            isVideoMuted: false,
            roomId: props.roomId,
            userName: props.userName,
            isWaitingForAdmin: !props.isAdmin,
            adminJoined: false,
        };
        this.api = null;
    }

    componentDidMount() {
        this.initializeJitsi();
    }

    componentWillUnmount() {
        if (this.api) {
            this.api.dispose();
        }
    }

    initializeJitsi = () => {
        const domain = 'meet.jit.si'; // Use your own Jitsi server if needed
        const options = {
            roomName: this.state.roomId,
            width: '100%',
            height: '100%',
            parentNode: document.querySelector('#jitsi-container'),
            userInfo: {
                displayName: this.state.userName,
            },
            configOverwrite: {
                startWithAudioMuted: false,
                startWithVideoMuted: false,
            },
            interfaceConfigOverwrite: {
                // Customize interface if needed
            },
        };

        this.api = new JitsiMeetExternalAPI(domain, options);

        // Event listeners
        this.api.addEventListener('audioMuteStatusChanged', ({ muted }) => {
            this.setState({ isAudioMuted: muted });
        });

        this.api.addEventListener('videoMuteStatusChanged', ({ muted }) => {
            this.setState({ isVideoMuted: muted });
        });

        this.api.addEventListener('readyToClose', () => {
            // Handle call end
            this.props.onLeaveCall();
        });

        this.api.addEventListener('participantJoined', (participant) => {
            // Check if Admin joined
            if (participant.displayName.includes('Admin') || participant.id === 'admin') {
                this.setState({ adminJoined: true, isWaitingForAdmin: false });
            }
        });

        // For demo, auto-show after 5 seconds if not admin
        if (!this.props.isAdmin) {
            setTimeout(() => {
                this.setState({ isWaitingForAdmin: false });
            }, 5000);
        }
    };

    toggleAudio = () => {
        if (this.api) {
            this.api.executeCommand('toggleAudio');
        }
    };

    toggleVideo = () => {
        if (this.api) {
            this.api.executeCommand('toggleVideo');
        }
    };

    leaveCall = () => {
        if (this.api) {
            this.api.executeCommand('hangup');
        }
        this.props.onLeaveCall();
    };

    render() {
        if (this.state.isWaitingForAdmin) {
            return (
                <div className="video-call-room waiting-screen">
                    <div className="waiting-content">
                        <h2>Waiting for Admin to join the call...</h2>
                        <p>Please wait while the Admin connects to the video call.</p>
                        <div className="spinner"></div>
                        <button onClick={this.leaveCall} className="leave-btn">Leave Call</button>
                    </div>
                </div>
            );
        }

        return (
            <div className="video-call-room">
                <div id="jitsi-container" style={{ width: '100%', height: '600px' }}></div>
                <div className="controls">
                    <button onClick={this.toggleAudio}>
                        {this.state.isAudioMuted ? 'Unmute Audio' : 'Mute Audio'}
                    </button>
                    <button onClick={this.toggleVideo}>
                        {this.state.isVideoMuted ? 'Unmute Video' : 'Mute Video'}
                    </button>
                    <button onClick={this.leaveCall}>Leave Call</button>
                </div>
            </div>
        );
    }
}

// Usage example:
// <VideoCallRoom roomId="room123" userName="John Doe" isAdmin={false} onLeaveCall={() => console.log('Call ended')} />