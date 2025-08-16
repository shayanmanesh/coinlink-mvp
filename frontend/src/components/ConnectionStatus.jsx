import React, { useState, useEffect } from 'react';
import { WebSocketService } from '../services/api';
import './ConnectionStatus.css';

const ConnectionStatus = () => {
  const [connectionState, setConnectionState] = useState('disconnected');
  const [showDetails, setShowDetails] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [lastError, setLastError] = useState(null);
  
  useEffect(() => {
    // Create a WebSocket instance to monitor
    const wsService = new WebSocketService();
    
    // Listen for connection state changes
    const handleStateChange = (data) => {
      setConnectionState(data.state);
      if (data.state === 'reconnecting') {
        setReconnectAttempts(prev => prev + 1);
      } else if (data.state === 'connected') {
        setReconnectAttempts(0);
        setLastError(null);
      }
    };
    
    const handleError = (data) => {
      setLastError(data.message);
    };
    
    const handleReconnectionFailed = (data) => {
      setConnectionState('failed');
      setLastError(data.message);
    };
    
    // Subscribe to events
    wsService.on('connection_state_changed', handleStateChange);
    wsService.on('error', handleError);
    wsService.on('reconnection_failed', handleReconnectionFailed);
    
    // Connect
    wsService.connect().catch(err => {
      console.error('Initial connection failed:', err);
    });
    
    // Cleanup
    return () => {
      wsService.off('connection_state_changed', handleStateChange);
      wsService.off('error', handleError);
      wsService.off('reconnection_failed', handleReconnectionFailed);
      wsService.disconnect();
    };
  }, []);
  
  const getStatusColor = () => {
    switch (connectionState) {
      case 'connected':
        return '#4caf50'; // green
      case 'connecting':
      case 'reconnecting':
        return '#ff9800'; // orange
      case 'disconnected':
      case 'failed':
        return '#f44336'; // red
      default:
        return '#9e9e9e'; // gray
    }
  };
  
  const getStatusText = () => {
    switch (connectionState) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'reconnecting':
        return `Reconnecting... (${reconnectAttempts})`;
      case 'disconnected':
        return 'Disconnected';
      case 'failed':
        return 'Connection Failed';
      default:
        return 'Unknown';
    }
  };
  
  const getStatusIcon = () => {
    switch (connectionState) {
      case 'connected':
        return '●'; // filled circle
      case 'connecting':
      case 'reconnecting':
        return '○'; // empty circle
      case 'disconnected':
      case 'failed':
        return '✕'; // x mark
      default:
        return '?';
    }
  };
  
  return (
    <div className="connection-status">
      <div 
        className="connection-indicator"
        onClick={() => setShowDetails(!showDetails)}
        style={{ cursor: 'pointer' }}
      >
        <span 
          className="status-dot"
          style={{ color: getStatusColor() }}
        >
          {getStatusIcon()}
        </span>
        <span className="status-text">
          {getStatusText()}
        </span>
      </div>
      
      {showDetails && (
        <div className="connection-details">
          <div>Status: {connectionState}</div>
          {reconnectAttempts > 0 && (
            <div>Reconnect attempts: {reconnectAttempts}</div>
          )}
          {lastError && (
            <div className="error-message">Error: {lastError}</div>
          )}
          <div className="connection-url">
            URL: {process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws'}
          </div>
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus;