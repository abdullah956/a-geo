/**
 * Location service for handling geolocation and location verification
 */

export const locationService = {
  /**
   * Get current user location using browser geolocation API
   * @param {Object} options - Geolocation options
   * @returns {Promise<{latitude: number, longitude: number}>}
   */
  getCurrentLocation: (options = {}) => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation is not supported by this browser'));
        return;
      }

      // Note: Some browsers require HTTPS for geolocation
      // We let the browser handle this - it will show permission prompt or error
      // On some mobile browsers, HTTP on local network might still work

      const defaultOptions = {
        enableHighAccuracy: true,
        timeout: 15000, // Increased timeout
        maximumAge: 0, // Always get fresh location
        ...options
      };

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          });
        },
        (error) => {
          let errorMessage = 'Unable to get location';
          
          switch (error.code) {
            case error.PERMISSION_DENIED:
              errorMessage = 'Location access denied by user';
              break;
            case error.POSITION_UNAVAILABLE:
              errorMessage = 'Location information unavailable';
              break;
            case error.TIMEOUT:
              errorMessage = 'Location request timed out';
              break;
            default:
              errorMessage = 'Unknown location error';
              break;
          }
          
          reject(new Error(errorMessage));
        },
        defaultOptions
      );
    });
  },

  /**
   * Request location permission from user
   * @returns {Promise<boolean>}
   */
  requestLocationPermission: async () => {
    try {
      if (!navigator.permissions) {
        // Fallback for browsers without permissions API
        await this.getCurrentLocation();
        return true;
      }

      const permission = await navigator.permissions.query({ name: 'geolocation' });
      
      if (permission.state === 'granted') {
        return true;
      } else if (permission.state === 'prompt') {
        // Try to get location to trigger permission prompt
        try {
          await this.getCurrentLocation();
          return true;
        } catch (error) {
          return false;
        }
      } else {
        return false;
      }
    } catch (error) {
      console.error('Error requesting location permission:', error);
      return false;
    }
  },

  /**
   * Check if location services are available
   * @returns {boolean}
   */
  isLocationAvailable: () => {
    return 'geolocation' in navigator;
  },

  /**
   * Calculate distance between two coordinates using Haversine formula
   * @param {number} lat1 - First latitude
   * @param {number} lon1 - First longitude
   * @param {number} lat2 - Second latitude
   * @param {number} lon2 - Second longitude
   * @returns {number} Distance in meters
   */
  calculateDistance: (lat1, lon1, lat2, lon2) => {
    console.log('=== CALCULATING DISTANCE ===');
    console.log('Input coordinates:', { lat1, lon1, lat2, lon2 });
    console.log('Coordinate types:', { 
      lat1Type: typeof lat1, 
      lon1Type: typeof lon1, 
      lat2Type: typeof lat2, 
      lon2Type: typeof lon2 
    });
    console.log('Coordinate values:', { 
      lat1Value: lat1, 
      lon1Value: lon1, 
      lat2Value: lat2, 
      lon2Value: lon2 
    });
    
    // Convert string coordinates to numbers if needed
    const numLat1 = typeof lat1 === 'string' ? parseFloat(lat1) : lat1;
    const numLon1 = typeof lon1 === 'string' ? parseFloat(lon1) : lon1;
    const numLat2 = typeof lat2 === 'string' ? parseFloat(lat2) : lat2;
    const numLon2 = typeof lon2 === 'string' ? parseFloat(lon2) : lon2;
    
    console.log('Converted coordinates:', { numLat1, numLon1, numLat2, numLon2 });
    
    // Validate inputs
    if (typeof numLat1 !== 'number' || typeof numLon1 !== 'number' || 
        typeof numLat2 !== 'number' || typeof numLon2 !== 'number' ||
        isNaN(numLat1) || isNaN(numLon1) || isNaN(numLat2) || isNaN(numLon2)) {
      console.error('Invalid coordinates provided to calculateDistance:', { numLat1, numLon1, numLat2, numLon2 });
      return Infinity; // Return infinity for invalid coordinates
    }

    const R = 6371000; // Earth's radius in meters
    const dLat = locationService.toRadians(numLat2 - numLat1);
    const dLon = locationService.toRadians(numLon2 - numLon1);
    console.log('Delta calculations:', { dLat, dLon });
    
    const a = 
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(locationService.toRadians(numLat1)) * Math.cos(locationService.toRadians(numLat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;
    
    console.log('Distance calculation result:', distance);
    return distance;
  },

  /**
   * Convert degrees to radians
   * @param {number} degrees
   * @returns {number} Radians
   */
  toRadians: (degrees) => {
    return degrees * (Math.PI / 180);
  },

  /**
   * Format distance for display
   * @param {number} distance - Distance in meters
   * @returns {string} Formatted distance string
   */
  formatDistance: (distance) => {
    if (distance < 1000) {
      return `${Math.round(distance)}m`;
    } else {
      return `${(distance / 1000).toFixed(1)}km`;
    }
  },

  /**
   * Check if location is within allowed radius
   * @param {number} userLat - User latitude
   * @param {number} userLon - User longitude
   * @param {number} targetLat - Target latitude
   * @param {number} targetLon - Target longitude
   * @param {number} radius - Allowed radius in meters
   * @returns {Object} {isWithinRadius: boolean, distance: number}
   */
  verifyLocation: (userLat, userLon, targetLat, targetLon, radius) => {
    const distance = locationService.calculateDistance(userLat, userLon, targetLat, targetLon);
    return {
      isWithinRadius: distance <= radius,
      distance: distance
    };
  }
};
