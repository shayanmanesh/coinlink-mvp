/**
 * Audio Notification Service
 * Handles all notification sounds for the CoinLink application
 */

class AudioService {
  constructor() {
    this.audio = null;
    this.enabled = true;
    this.volume = 0.5;
    this.soundUrl = '/done.mp3';
    this.isInitialized = false;
    
    // Event types that trigger sounds
    this.eventTypes = {
      TASK_COMPLETE: 'task_complete',
      ERROR: 'error',
      USER_INPUT_NEEDED: 'user_input_needed',
      MESSAGE_RECEIVED: 'message_received',
      ALERT: 'alert',
      SUCCESS: 'success'
    };
    
    // Initialize audio on first user interaction
    this.initPromise = null;
    this.initializeAudio();
  }
  
  /**
   * Initialize the audio element
   */
  initializeAudio() {
    if (this.isInitialized) return Promise.resolve();
    
    if (!this.initPromise) {
      this.initPromise = new Promise((resolve) => {
        // Create audio element
        this.audio = new Audio(this.soundUrl);
        this.audio.volume = this.volume;
        this.audio.preload = 'auto';
        
        // Load the audio
        this.audio.load();
        
        this.audio.addEventListener('canplaythrough', () => {
          this.isInitialized = true;
          console.log('Audio notification system initialized');
          resolve();
        }, { once: true });
        
        this.audio.addEventListener('error', (e) => {
          console.error('Failed to load notification sound:', e);
          this.isInitialized = false;
          resolve(); // Resolve anyway to not block the app
        }, { once: true });
        
        // Fallback timeout
        setTimeout(() => {
          if (!this.isInitialized) {
            console.warn('Audio initialization timed out');
            resolve();
          }
        }, 3000);
      });
    }
    
    return this.initPromise;
  }
  
  /**
   * Play notification sound
   * @param {string} eventType - Type of event triggering the sound
   * @param {object} options - Additional options
   */
  async play(eventType = this.eventTypes.TASK_COMPLETE, options = {}) {
    if (!this.enabled) {
      console.log('Audio notifications disabled');
      return;
    }
    
    try {
      // Ensure audio is initialized
      await this.initializeAudio();
      
      if (!this.audio) {
        console.warn('Audio not available');
        return;
      }
      
      // Set volume if specified
      if (options.volume !== undefined) {
        this.audio.volume = Math.max(0, Math.min(1, options.volume));
      } else {
        this.audio.volume = this.volume;
      }
      
      // Clone and play for overlapping sounds
      const audioClone = this.audio.cloneNode();
      audioClone.volume = this.audio.volume;
      
      // Play the sound
      const playPromise = audioClone.play();
      
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            console.log(`Played notification for: ${eventType}`);
          })
          .catch(error => {
            // Auto-play was prevented
            console.warn('Notification sound blocked:', error);
            // Store that we need user interaction
            this.needsUserInteraction = true;
          });
      }
      
      // Clean up after playing
      audioClone.addEventListener('ended', () => {
        audioClone.remove();
      });
      
    } catch (error) {
      console.error('Error playing notification sound:', error);
    }
  }
  
  /**
   * Play sound for task completion
   */
  playTaskComplete() {
    return this.play(this.eventTypes.TASK_COMPLETE);
  }
  
  /**
   * Play sound for errors
   */
  playError() {
    return this.play(this.eventTypes.ERROR, { volume: 0.6 });
  }
  
  /**
   * Play sound when user input is needed
   */
  playUserInputNeeded() {
    return this.play(this.eventTypes.USER_INPUT_NEEDED, { volume: 0.4 });
  }
  
  /**
   * Play sound for incoming messages
   */
  playMessageReceived() {
    return this.play(this.eventTypes.MESSAGE_RECEIVED, { volume: 0.3 });
  }
  
  /**
   * Play sound for alerts
   */
  playAlert() {
    return this.play(this.eventTypes.ALERT, { volume: 0.7 });
  }
  
  /**
   * Play sound for success events
   */
  playSuccess() {
    return this.play(this.eventTypes.SUCCESS, { volume: 0.5 });
  }
  
  /**
   * Enable/disable audio notifications
   */
  setEnabled(enabled) {
    this.enabled = enabled;
    localStorage.setItem('audioNotificationsEnabled', enabled ? 'true' : 'false');
    console.log(`Audio notifications ${enabled ? 'enabled' : 'disabled'}`);
  }
  
  /**
   * Get enabled state
   */
  isEnabled() {
    return this.enabled;
  }
  
  /**
   * Set volume (0-1)
   */
  setVolume(volume) {
    this.volume = Math.max(0, Math.min(1, volume));
    if (this.audio) {
      this.audio.volume = this.volume;
    }
    localStorage.setItem('audioNotificationVolume', this.volume.toString());
  }
  
  /**
   * Get current volume
   */
  getVolume() {
    return this.volume;
  }
  
  /**
   * Initialize from localStorage
   */
  loadPreferences() {
    const enabled = localStorage.getItem('audioNotificationsEnabled');
    if (enabled !== null) {
      this.enabled = enabled === 'true';
    }
    
    const volume = localStorage.getItem('audioNotificationVolume');
    if (volume !== null) {
      this.volume = parseFloat(volume);
    }
  }
  
  /**
   * Test the notification sound
   */
  async test() {
    console.log('Testing notification sound...');
    await this.play('test');
  }
  
  /**
   * Handle first user interaction to enable audio
   */
  async enableOnUserInteraction() {
    if (this.needsUserInteraction) {
      await this.initializeAudio();
      this.needsUserInteraction = false;
      console.log('Audio enabled after user interaction');
    }
  }
}

// Create singleton instance
const audioService = new AudioService();

// Load preferences
audioService.loadPreferences();

// Export service
export default audioService;