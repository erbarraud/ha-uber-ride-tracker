# Changelog

All notable changes to the Uber Ride Tracker integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Apple Live Activity-style custom Lovelace card
- Automatic update notifications via Update entity
- Configuration migration system for seamless updates
- Comprehensive dashboard examples
- Update coordinator for version checking

## [1.0.0] - 2024-01-XX

### Added
- Initial release with OAuth2 authentication
- Real-time ride tracking with 10-second updates during active rides
- Multiple entity types: sensors, binary sensors, and device tracker
- Driver information display (name, rating, photo, phone)
- Vehicle details (make, model, color, license plate)
- Trip progress tracking with percentage completion
- Location tracking with GPS coordinates
- Service calls for refresh and ride history
- HACS compatibility
- Smart polling intervals (10s active, 60s idle, 300s error)

### Security
- Secure OAuth2 authentication flow
- Token refresh handling
- No credentials stored in plain text

## Update Guide

### From 0.x to 1.0.0
**Breaking Changes:**
- OAuth authentication is now required
- Configuration flow has changed
- Entity IDs have been standardized

**Migration Steps:**
1. Update via HACS or manually download latest release
2. Remove old integration instance
3. Re-add integration with OAuth credentials
4. Reconfigure automations with new entity IDs

### Auto-Update Features
- **HACS Users**: Automatic notifications and one-click updates
- **Manual Users**: Update entity shows available versions
- **All Users**: Configuration automatically migrated on update

## Version Policy

We follow semantic versioning:
- **Major** (X.0.0): Breaking changes requiring reconfiguration
- **Minor** (0.X.0): New features, backwards compatible
- **Patch** (0.0.X): Bug fixes only

## Rollback Instructions

If you experience issues after updating:

### Via HACS
1. Open HACS → Integrations
2. Find Uber Ride Tracker
3. Click three dots → Redownload
4. Select previous version
5. Restart Home Assistant

### Manual Installation
1. Download previous release from GitHub
2. Replace `custom_components/uber_ride_tracker` folder
3. Restart Home Assistant

## Support

- Report issues: [GitHub Issues](https://github.com/yourusername/ha-uber-ride-tracker/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/ha-uber-ride-tracker/discussions)
- Documentation: [README](README.md)