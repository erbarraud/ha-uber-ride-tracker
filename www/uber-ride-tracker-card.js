class UberRideTrackerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define an entity');
    }
    this.config = config;
  }

  set hass(hass) {
    this._hass = hass;
    const entity = hass.states[this.config.entity];
    
    if (!entity) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="error">Entity ${this.config.entity} not found</div>
        </ha-card>
      `;
      return;
    }

    const state = entity.state;
    const attributes = entity.attributes;
    
    // Check if ride is active
    const isActive = ['processing', 'accepted', 'arriving', 'in_progress'].includes(state);
    const noActiveRide = state === 'no_active_ride' || state === 'waiting_for_oauth' || !isActive;
    
    if (!isActive && this.config.hide_when_inactive === true) {
      this.shadowRoot.innerHTML = '';
      return;
    }

    // Calculate progress percentage
    const progress = attributes.trip_progress_percentage || 0;
    
    // Format ETA
    const formatETA = (minutes) => {
      if (!minutes) return '--';
      if (minutes < 1) return 'Now';
      if (minutes === 1) return '1 min';
      return `${minutes} mins`;
    };

    // Get status color and icon
    const getStatusStyle = (status) => {
      switch(status) {
        case 'processing':
          return { color: '#FFA500', icon: 'mdi:clock-outline', text: 'Finding driver...' };
        case 'accepted':
          return { color: '#4CAF50', icon: 'mdi:check-circle', text: 'Driver accepted' };
        case 'arriving':
          return { color: '#2196F3', icon: 'mdi:car', text: 'Driver arriving' };
        case 'in_progress':
          return { color: '#9C27B0', icon: 'mdi:map-marker-path', text: 'On the way' };
        case 'completed':
          return { color: '#4CAF50', icon: 'mdi:flag-checkered', text: 'Completed' };
        default:
          return { color: '#9E9E9E', icon: 'mdi:car', text: state };
      }
    };

    const statusInfo = getStatusStyle(state);

    // Show empty state when no active ride
    if (noActiveRide) {
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
          }
          
          .empty-state-card {
            background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            position: relative;
            overflow: hidden;
            min-height: 180px;
          }
          
          .empty-state-card::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -30%;
            width: 100%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.02) 0%, transparent 70%);
            animation: float 20s infinite ease-in-out;
          }
          
          @keyframes float {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(10deg); }
          }
          
          .uber-header {
            display: flex;
            align-items: center;
            margin-bottom: 24px;
            position: relative;
            z-index: 1;
          }
          
          .uber-logo {
            width: 48px;
            height: 48px;
            background: white;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            color: #000;
            font-size: 24px;
            margin-right: 16px;
            box-shadow: 0 4px 12px rgba(255,255,255,0.1);
          }
          
          .uber-title {
            flex: 1;
          }
          
          .uber-name {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 4px;
            letter-spacing: -0.5px;
          }
          
          .uber-tagline {
            font-size: 14px;
            opacity: 0.7;
            font-weight: 400;
          }
          
          .empty-content {
            position: relative;
            z-index: 1;
          }
          
          .empty-icon {
            width: 64px;
            height: 64px;
            margin: 0 auto 16px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
          }
          
          .empty-message {
            text-align: center;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
            letter-spacing: -0.3px;
          }
          
          .empty-submessage {
            text-align: center;
            font-size: 14px;
            opacity: 0.6;
            line-height: 1.4;
            margin-bottom: 20px;
          }
          
          .status-pills {
            display: flex;
            gap: 8px;
            justify-content: center;
            flex-wrap: wrap;
          }
          
          .status-pill {
            background: rgba(255,255,255,0.1);
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 12px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
            gap: 6px;
          }
          
          .status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #00ff88;
            animation: pulse 2s infinite;
          }
          
          .status-dot.inactive {
            background: #666;
            animation: none;
          }
          
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
          
          .hint-text {
            text-align: center;
            font-size: 11px;
            opacity: 0.4;
            margin-top: 16px;
            font-style: italic;
          }
        </style>
        
        <div class="empty-state-card">
          <div class="uber-header">
            <div class="uber-logo">U</div>
            <div class="uber-title">
              <div class="uber-name">Uber Ride Tracker</div>
              <div class="uber-tagline">Home Assistant Integration</div>
            </div>
          </div>
          
          <div class="empty-content">
            <div class="empty-icon">
              <ha-icon icon="mdi:car-outline" style="width: 32px; height: 32px; opacity: 0.8;"></ha-icon>
            </div>
            <div class="empty-message">No Active Ride</div>
            <div class="empty-submessage">
              Your ride information will appear here<br>when you request an Uber
            </div>
            
            <div class="status-pills">
              <div class="status-pill">
                <div class="status-dot ${attributes.integration_status === 'configured' ? '' : 'inactive'}"></div>
                <span>Integration ${attributes.integration_status === 'configured' ? 'Ready' : 'Setup Needed'}</span>
              </div>
              ${attributes.message && attributes.message.includes('OAuth') ? `
                <div class="status-pill">
                  <div class="status-dot inactive"></div>
                  <span>OAuth Required</span>
                </div>
              ` : ''}
            </div>
            
            <div class="hint-text">
              Request a ride in the Uber app to see live tracking here
            </div>
          </div>
        </div>
      `;
      return;
    }

    // Active ride display
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        
        .live-activity-card {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 20px;
          padding: 16px;
          box-shadow: 0 10px 40px rgba(0,0,0,0.2);
          color: white;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          position: relative;
          overflow: hidden;
        }
        
        .live-activity-card.inactive {
          background: linear-gradient(135deg, #868e96 0%, #495057 100%);
        }
        
        .live-indicator {
          position: absolute;
          top: 12px;
          right: 12px;
          display: flex;
          align-items: center;
          gap: 6px;
          background: rgba(255,255,255,0.2);
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
          backdrop-filter: blur(10px);
        }
        
        .live-dot {
          width: 8px;
          height: 8px;
          background: #00ff00;
          border-radius: 50%;
          animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
          0% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(1.2); }
          100% { opacity: 1; transform: scale(1); }
        }
        
        .header {
          display: flex;
          align-items: center;
          margin-bottom: 16px;
        }
        
        .uber-logo {
          width: 32px;
          height: 32px;
          margin-right: 12px;
          background: white;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          color: #000;
          font-size: 18px;
        }
        
        .title-section {
          flex: 1;
        }
        
        .title {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 2px;
        }
        
        .status {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 14px;
          opacity: 0.95;
        }
        
        .status-icon {
          display: inline-flex;
        }
        
        .main-content {
          display: flex;
          gap: 16px;
          margin-bottom: 16px;
        }
        
        .driver-info {
          flex: 1;
          background: rgba(255,255,255,0.15);
          border-radius: 12px;
          padding: 12px;
          backdrop-filter: blur(10px);
        }
        
        .driver-header {
          display: flex;
          align-items: center;
          margin-bottom: 8px;
        }
        
        .driver-photo {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: rgba(255,255,255,0.3);
          margin-right: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .driver-photo img {
          width: 100%;
          height: 100%;
          border-radius: 50%;
          object-fit: cover;
        }
        
        .driver-details {
          flex: 1;
        }
        
        .driver-name {
          font-size: 15px;
          font-weight: 600;
          margin-bottom: 2px;
        }
        
        .driver-rating {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 13px;
          opacity: 0.9;
        }
        
        .vehicle-info {
          font-size: 13px;
          opacity: 0.9;
          line-height: 1.4;
        }
        
        .eta-info {
          background: rgba(255,255,255,0.15);
          border-radius: 12px;
          padding: 12px;
          backdrop-filter: blur(10px);
          min-width: 100px;
          text-align: center;
        }
        
        .eta-label {
          font-size: 12px;
          opacity: 0.8;
          margin-bottom: 4px;
        }
        
        .eta-time {
          font-size: 24px;
          font-weight: 700;
        }
        
        .progress-section {
          margin-bottom: 16px;
        }
        
        .progress-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          font-size: 13px;
        }
        
        .progress-bar {
          height: 6px;
          background: rgba(255,255,255,0.2);
          border-radius: 3px;
          overflow: hidden;
        }
        
        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #00ff88, #00ffff);
          border-radius: 3px;
          transition: width 0.5s ease;
          box-shadow: 0 0 10px rgba(0,255,136,0.5);
        }
        
        .location-section {
          display: flex;
          gap: 12px;
        }
        
        .location-item {
          flex: 1;
          background: rgba(255,255,255,0.1);
          border-radius: 10px;
          padding: 10px;
          backdrop-filter: blur(10px);
        }
        
        .location-label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          opacity: 0.8;
          margin-bottom: 4px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        
        .location-address {
          font-size: 13px;
          font-weight: 500;
          line-height: 1.3;
        }
        
        .action-buttons {
          display: flex;
          gap: 10px;
          margin-top: 16px;
        }
        
        .action-button {
          flex: 1;
          background: rgba(255,255,255,0.2);
          border: none;
          border-radius: 10px;
          padding: 10px;
          color: white;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          backdrop-filter: blur(10px);
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
        }
        
        .action-button:hover {
          background: rgba(255,255,255,0.3);
          transform: translateY(-2px);
        }
        
        .error {
          padding: 16px;
          color: #f44336;
          text-align: center;
        }
        
        @media (max-width: 400px) {
          .main-content {
            flex-direction: column;
          }
          
          .eta-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
        }
      </style>
      
      <div class="live-activity-card ${!isActive ? 'inactive' : ''}">
        ${isActive ? `
          <div class="live-indicator">
            <div class="live-dot"></div>
            LIVE
          </div>
        ` : ''}
        
        <div class="header">
          <div class="uber-logo">U</div>
          <div class="title-section">
            <div class="title">${attributes.product_name || 'Uber Ride'}</div>
            <div class="status">
              <ha-icon class="status-icon" icon="${statusInfo.icon}" style="width: 16px; height: 16px;"></ha-icon>
              ${statusInfo.text}
            </div>
          </div>
        </div>
        
        ${attributes.driver_name ? `
          <div class="main-content">
            <div class="driver-info">
              <div class="driver-header">
                <div class="driver-photo">
                  ${attributes.driver_photo_url ? 
                    `<img src="${attributes.driver_photo_url}" alt="${attributes.driver_name}">` :
                    `<ha-icon icon="mdi:account" style="width: 24px; height: 24px;"></ha-icon>`
                  }
                </div>
                <div class="driver-details">
                  <div class="driver-name">${attributes.driver_name}</div>
                  ${attributes.driver_rating ? `
                    <div class="driver-rating">
                      <ha-icon icon="mdi:star" style="width: 14px; height: 14px;"></ha-icon>
                      ${attributes.driver_rating}
                    </div>
                  ` : ''}
                </div>
              </div>
              ${attributes.vehicle_make ? `
                <div class="vehicle-info">
                  ${attributes.vehicle_color || ''} ${attributes.vehicle_make} ${attributes.vehicle_model || ''}<br>
                  ${attributes.vehicle_license_plate || ''}
                </div>
              ` : ''}
            </div>
            
            <div class="eta-info">
              <div class="eta-label">${state === 'arriving' ? 'PICKUP' : 'ARRIVAL'}</div>
              <div class="eta-time">${formatETA(state === 'arriving' ? attributes.pickup_eta : attributes.destination_eta)}</div>
            </div>
          </div>
        ` : ''}
        
        ${state === 'in_progress' && progress > 0 ? `
          <div class="progress-section">
            <div class="progress-header">
              <span>Trip Progress</span>
              <span>${progress}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
          </div>
        ` : ''}
        
        <div class="location-section">
          ${attributes.pickup_address ? `
            <div class="location-item">
              <div class="location-label">
                <ha-icon icon="mdi:map-marker" style="width: 14px; height: 14px;"></ha-icon>
                PICKUP
              </div>
              <div class="location-address">${attributes.pickup_address}</div>
            </div>
          ` : ''}
          
          ${attributes.destination_address ? `
            <div class="location-item">
              <div class="location-label">
                <ha-icon icon="mdi:flag-checkered" style="width: 14px; height: 14px;"></ha-icon>
                DESTINATION
              </div>
              <div class="location-address">${attributes.destination_address}</div>
            </div>
          ` : ''}
        </div>
        
        ${isActive ? `
          <div class="action-buttons">
            ${attributes.driver_phone ? `
              <button class="action-button" onclick="window.open('tel:${attributes.driver_phone}')">
                <ha-icon icon="mdi:phone" style="width: 18px; height: 18px;"></ha-icon>
                Call Driver
              </button>
            ` : ''}
            
            ${attributes.share_url ? `
              <button class="action-button" onclick="window.open('${attributes.share_url}')">
                <ha-icon icon="mdi:share-variant" style="width: 18px; height: 18px;"></ha-icon>
                Share Trip
              </button>
            ` : ''}
            
            ${attributes.map_url ? `
              <button class="action-button" onclick="window.open('${attributes.map_url}')">
                <ha-icon icon="mdi:map" style="width: 18px; height: 18px;"></ha-icon>
                View Map
              </button>
            ` : ''}
          </div>
        ` : ''}
      </div>
    `;
  }

  getCardSize() {
    return 4;
  }

  static getConfigElement() {
    return document.createElement("uber-ride-tracker-card-editor");
  }

  static getStubConfig() {
    return {
      entity: "sensor.uber_ride_tracker_ride_status",
      hide_when_inactive: true
    };
  }
}

customElements.define('uber-ride-tracker-card', UberRideTrackerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "uber-ride-tracker-card",
  name: "Uber Ride Tracker Card",
  description: "Apple Live Activity-style card for Uber ride tracking",
  preview: true,
  documentationURL: "https://github.com/yourusername/ha-uber-ride-tracker"
});