import React, { useState, useEffect } from 'react';
import audioService from '../services/audioService';

const AudioControls = () => {
  const [isEnabled, setIsEnabled] = useState(audioService.isEnabled());
  const [volume, setVolume] = useState(audioService.getVolume());
  const [showControls, setShowControls] = useState(false);

  useEffect(() => {
    // Enable audio on first user interaction
    const handleUserInteraction = () => {
      audioService.enableOnUserInteraction();
    };

    document.addEventListener('click', handleUserInteraction, { once: true });
    document.addEventListener('keydown', handleUserInteraction, { once: true });

    return () => {
      document.removeEventListener('click', handleUserInteraction);
      document.removeEventListener('keydown', handleUserInteraction);
    };
  }, []);

  const handleToggleEnabled = () => {
    const newEnabled = !isEnabled;
    setIsEnabled(newEnabled);
    audioService.setEnabled(newEnabled);
    
    // Play a test sound when enabling
    if (newEnabled) {
      audioService.playSuccess();
    }
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    audioService.setVolume(newVolume);
  };

  const handleTestSound = () => {
    audioService.test();
  };

  return (
    <div className="relative">
      {/* Audio Control Button */}
      <button
        onClick={() => setShowControls(!showControls)}
        className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
        title="Audio Settings"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={isEnabled ? 'text-white' : 'text-gray-500'}
        >
          {isEnabled ? (
            <>
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
            </>
          ) : (
            <>
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
              <line x1="23" y1="9" x2="17" y2="15" />
              <line x1="17" y1="9" x2="23" y2="15" />
            </>
          )}
        </svg>
      </button>

      {/* Audio Controls Dropdown */}
      {showControls && (
        <div className="absolute top-10 right-0 bg-gray-900 border border-gray-700 rounded-lg p-4 shadow-lg z-50 w-64">
          <h3 className="text-white font-semibold mb-3">Audio Settings</h3>
          
          {/* Enable/Disable Toggle */}
          <div className="flex items-center justify-between mb-3">
            <span className="text-gray-300">Notifications</span>
            <button
              onClick={handleToggleEnabled}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                isEnabled ? 'bg-green-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  isEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Volume Slider */}
          {isEnabled && (
            <>
              <div className="mb-3">
                <label className="text-gray-300 text-sm">
                  Volume: {Math.round(volume * 100)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={volume}
                  onChange={handleVolumeChange}
                  className="w-full mt-1"
                />
              </div>

              {/* Test Sound Button */}
              <button
                onClick={handleTestSound}
                className="w-full py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors text-sm"
              >
                Test Sound
              </button>
            </>
          )}

          {/* Info Text */}
          <p className="text-xs text-gray-500 mt-3">
            {isEnabled
              ? 'Sounds play for tasks, errors, and alerts'
              : 'Enable to hear notification sounds'}
          </p>
        </div>
      )}
    </div>
  );
};

export default AudioControls;