import React, { useState, useCallback } from 'react';
import { GoogleMap, useJsApiLoader, Marker, Circle } from '@react-google-maps/api';
import { MapPin, Search, Target } from 'lucide-react';

// Placeholder API key - replace with actual Google Maps API key
const GOOGLE_MAPS_API_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY || 'placeholder_key';

const containerStyle = {
  width: '100%',
  height: '300px'
};

const defaultCenter = {
  lat: 28.6139, // New Delhi
  lng: 77.2090
};

export const LocationPicker = ({ onLocationSelect, initialLocation, showRadius = false, radius = 10 }) => {
  const [map, setMap] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(initialLocation || defaultCenter);
  const [address, setAddress] = useState(initialLocation?.address || '');
  const [searchQuery, setSearchQuery] = useState('');

  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: GOOGLE_MAPS_API_KEY,
    libraries: ['places']
  });

  const onLoad = useCallback(function callback(map) {
    setMap(map);
  }, []);

  const onUnmount = useCallback(function callback(map) {
    setMap(null);
  }, []);

  const handleMapClick = (event) => {
    const newLocation = {
      lat: event.latLng.lat(),
      lng: event.latLng.lng(),
      address: `${event.latLng.lat().toFixed(6)}, ${event.latLng.lng().toFixed(6)}`
    };
    
    setSelectedLocation(newLocation);
    
    // Reverse geocoding (placeholder - would use Google Maps Geocoding API)
    reverseGeocode(newLocation.lat, newLocation.lng);
  };

  const reverseGeocode = async (lat, lng) => {
    // Placeholder for reverse geocoding
    // In production, use Google Maps Geocoding API
    const mockAddress = `${lat.toFixed(4)}, ${lng.toFixed(4)} - Location in Delhi, India`;
    setAddress(mockAddress);
    
    const locationWithAddress = {
      lat,
      lng,
      address: mockAddress
    };
    
    setSelectedLocation(locationWithAddress);
    onLocationSelect?.(locationWithAddress);
  };

  const handleSearch = () => {
    if (!searchQuery.trim()) return;
    
    // Placeholder search implementation
    // In production, use Google Places API
    const mockSearchResult = {
      lat: 28.6139 + (Math.random() - 0.5) * 0.1,
      lng: 77.2090 + (Math.random() - 0.5) * 0.1,
      address: searchQuery
    };
    
    setSelectedLocation(mockSearchResult);
    setAddress(searchQuery);
    map?.panTo(mockSearchResult);
    onLocationSelect?.(mockSearchResult);
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            address: `Current Location: ${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`
          };
          
          setSelectedLocation(location);
          setAddress(location.address);
          map?.panTo(location);
          onLocationSelect?.(location);
        },
        (error) => {
          console.error('Error getting location:', error);
        }
      );
    }
  };

  if (!isLoaded) {
    return (
      <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading Map...</p>
          <p className="text-xs text-gray-500 mt-1">
            📍 Google Maps integration placeholder
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search for a location..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-orange-500 focus:border-orange-500"
          />
        </div>
        <button
          onClick={handleSearch}
          className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
        >
          Search
        </button>
        <button
          onClick={getCurrentLocation}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          title="Use current location"
        >
          <Target className="w-4 h-4" />
        </button>
      </div>

      {/* Map */}
      <div className="rounded-lg overflow-hidden border border-gray-200">
        <GoogleMap
          mapContainerStyle={containerStyle}
          center={selectedLocation}
          zoom={13}
          onLoad={onLoad}
          onUnmount={onUnmount}
          onClick={handleMapClick}
        >
          <Marker position={selectedLocation} />
          
          {showRadius && (
            <Circle
              center={selectedLocation}
              radius={radius * 1000} // Convert km to meters
              options={{
                fillColor: '#ea580c',
                fillOpacity: 0.1,
                strokeColor: '#ea580c',
                strokeOpacity: 0.3,
                strokeWeight: 2,
              }}
            />
          )}
        </GoogleMap>
      </div>

      {/* Selected Location Info */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-start">
          <MapPin className="w-5 h-5 text-orange-600 mt-0.5 mr-2" />
          <div className="flex-1">
            <h4 className="font-medium text-gray-900">Selected Location</h4>
            <p className="text-sm text-gray-600 mt-1">
              {address || 'Click on the map to select a location'}
            </p>
            {selectedLocation && (
              <p className="text-xs text-gray-500 mt-1">
                Coordinates: {selectedLocation.lat.toFixed(6)}, {selectedLocation.lng.toFixed(6)}
              </p>
            )}
            {showRadius && (
              <p className="text-xs text-blue-600 mt-1">
                Service radius: {radius} km
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export const JobLocationMap = ({ jobs, onJobSelect }) => {
  const [map, setMap] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);

  const { isLoaded } = useJsApiLoader({
    id: 'google-map-jobs',
    googleMapsApiKey: GOOGLE_MAPS_API_KEY
  });

  const onLoad = useCallback(function callback(map) {
    setMap(map);
    
    // Fit map to show all job locations
    if (jobs.length > 0) {
      const bounds = new window.google.maps.LatLngBounds();
      jobs.forEach(job => {
        if (job.location) {
          bounds.extend(new window.google.maps.LatLng(job.location.lat, job.location.lng));
        }
      });
      map.fitBounds(bounds);
    }
  }, [jobs]);

  const handleMarkerClick = (job) => {
    setSelectedJob(job);
    onJobSelect?.(job);
  };

  if (!isLoaded) {
    return (
      <div className="w-full h-96 bg-gray-100 rounded-lg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading Jobs Map...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg overflow-hidden border border-gray-200">
      <GoogleMap
        mapContainerStyle={{ width: '100%', height: '400px' }}
        center={defaultCenter}
        zoom={10}
        onLoad={onLoad}
      >
        {jobs.map((job) => (
          job.location && (
            <Marker
              key={job.id}
              position={job.location}
              onClick={() => handleMarkerClick(job)}
              icon={{
                url: job.type === 'daily' ? '/markers/daily-job.png' : '/markers/contractual-job.png',
                scaledSize: new window.google.maps.Size(32, 32)
              }}
            />
          )
        ))}
        
        {selectedJob && selectedJob.location && (
          <div className="info-window">
            {/* Custom InfoWindow content would go here */}
          </div>
        )}
      </GoogleMap>
    </div>
  );
};